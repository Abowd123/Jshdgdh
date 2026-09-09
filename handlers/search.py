from typing import List, Tuple

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

from keyboards.advanced_search import AdvancedSearch
from utils.normalize import normalize_arabic
from config import DATABASE_PATH

router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()
    waiting_for_year = State()


async def search_series(query: str, filters: dict | None = None) -> List[Tuple]:
    """البحث في المسلسلات مع فلاتر متقدمة. يعيد:
    (id, title, score, total_eps, is_complete, avg_rating, rating_count)
    """
    normalized_query = normalize_arabic(query)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        sql = """
            SELECT DISTINCT s.id, s.title, s.description, s.total_eps, s.is_complete,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(DISTINCT r.user_id) as rating_count
            FROM series s
            LEFT JOIN ratings r ON s.id = r.series_id
            WHERE 1=1
        """
        params: list = []

        if query:
            sql += " AND (s.title LIKE ? OR s.description LIKE ?)"
            term = f"%{query}%"
            params.extend([term, term])

        if filters and "year" in filters:
            sql += " AND s.created_at LIKE ?"
            params.append(f"{filters['year']}%")

        if filters and "status" in filters:
            if filters["status"] == "complete":
                sql += " AND s.is_complete = 1"
            elif filters["status"] == "ongoing":
                sql += " AND s.is_complete = 0"

        if filters and "eps_range" in filters:
            if filters["eps_range"] == "short":
                sql += " AND s.total_eps < 50"
            elif filters["eps_range"] == "long":
                sql += " AND s.total_eps > 100"

        sql += " GROUP BY s.id"

        if filters and filters.get("sort") == "top_rated":
            sql += " ORDER BY avg_rating DESC"
        elif filters and filters.get("sort") == "most_viewed":
            sql += " ORDER BY s.total_eps DESC"
        else:
            sql += " ORDER BY s.created_at DESC"

        cursor = await db.execute(sql, params)
        results = await cursor.fetchall()

    scored_results = []
    for row in results:
        sid, title, desc, total_eps, is_complete, avg_rating, rating_count = row
        normalized_title = normalize_arabic(title)

        score = 0.2
        if normalized_query:
            if normalized_query == normalized_title:
                score = 1.0
            elif normalized_title.startswith(normalized_query):
                score = 0.8
            elif normalized_query in normalized_title:
                score = 0.6
            elif desc and normalized_query in normalize_arabic(desc):
                score = 0.4

        scored_results.append(
            (sid, title, score, total_eps, is_complete, avg_rating, rating_count)
        )

    scored_results.sort(key=lambda x: x[2], reverse=True)
    return scored_results


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        "🔍 <b>اكتب اسم المسلسل الذي تبحث عنه:</b>\n\nللإلغاء: /cancel",
        parse_mode="HTML",
    )


@router.message(F.text == "🔍 بحث")
async def search_button(message: Message, state: FSMContext):
    await search_command(message, state)


@router.message(SearchStates.waiting_for_query)
async def receive_search_query(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.set_state(None)

    results = await search_series(query)

    if not results:
        await message.answer(
            f"😔 <b>لا توجد نتائج لـ:</b> {query}\n\nجرّب كلمة أخرى أو استخدم /search مجدداً.",
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"🔍 <b>نتائج البحث عن:</b> {query}\n\nتم العثور على {len(results)} نتيجة",
        reply_markup=AdvancedSearch.search_results(query, results),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "search:filters")
async def show_search_filters(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>البحث المتقدم</b>\n\nاختر الفلاتر التي تريد تطبيقها:",
        reply_markup=AdvancedSearch.search_filters(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:"))
async def apply_filter(callback: CallbackQuery, state: FSMContext):
    filter_type = callback.data.split(":")[1]
    data = await state.get_data()
    filters = data.get("filters", {})

    if filter_type == "genre":
        genres = ["أكشن", "مغامرات", "كوميدي", "دراما", "خيال علمي", "رعب", "رياضي", "غموض", "رومانسي", "تاريخي"]
        await callback.message.edit_text(
            "🎭 <b>اختر النوع:</b>\n\nيمكنك اختيار أكثر من نوع",
            reply_markup=AdvancedSearch.genre_selection(genres, set(filters.get("genres", []))),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    if filter_type == "year":
        await state.set_state(SearchStates.waiting_for_year)
        await callback.message.edit_text(
            "📅 <b>أدخل السنة:</b>\n\nمثال: 2024\nللعودة: /cancel",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    labels = {
        "complete": ("status", "complete", "✅ تم تطبيق فلتر: المكتملة"),
        "ongoing": ("status", "ongoing", "🔄 تم تطبيق فلتر: المستمرة"),
        "top_rated": ("sort", "top_rated", "⭐ تم تطبيق فلتر: الأعلى تقييماً"),
        "most_viewed": ("sort", "most_viewed", "👁 تم تطبيق فلتر: الأكثر مشاهدة"),
        "short": ("eps_range", "short", "📺 تم تطبيق فلتر: أقل من 50 حلقة"),
        "long": ("eps_range", "long", "📺 تم تطبيق فلتر: أكثر من 100 حلقة"),
    }

    if filter_type in labels:
        key, value, msg = labels[filter_type]
        filters[key] = value
        await state.update_data(filters=filters)
        await callback.message.edit_text(
            f"{msg}\n\nالآن اضغط 'تطبيق الفلتر' أو اختر فلتراً آخر.",
            reply_markup=AdvancedSearch.search_filters(),
            parse_mode="HTML",
        )
    elif filter_type == "reset":
        await state.update_data(filters={})
        await callback.message.edit_text(
            "🔄 <b>تم إعادة تعيين جميع الفلاتر</b>",
            reply_markup=AdvancedSearch.search_filters(),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("genre:toggle:"))
async def toggle_genre(callback: CallbackQuery, state: FSMContext):
    genre = callback.data.split(":", 2)[2]
    data = await state.get_data()
    filters = data.get("filters", {})
    genres = set(filters.get("genres", []))

    if genre in genres:
        genres.discard(genre)
    else:
        genres.add(genre)

    filters["genres"] = list(genres)
    await state.update_data(filters=filters)

    all_genres = ["أكشن", "مغامرات", "كوميدي", "دراما", "خيال علمي", "رعب", "رياضي", "غموض", "رومانسي", "تاريخي"]
    await callback.message.edit_text(
        "🎭 <b>اختر النوع:</b>\n\nيمكنك اختيار أكثر من نوع",
        reply_markup=AdvancedSearch.genre_selection(all_genres, genres),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "genre:clear")
async def clear_genres(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filters = data.get("filters", {})
    filters["genres"] = []
    await state.update_data(filters=filters)

    all_genres = ["أكشن", "مغامرات", "كوميدي", "دراما", "خيال علمي", "رعب", "رياضي", "غموض", "رومانسي", "تاريخي"]
    await callback.message.edit_text(
        "🎭 <b>اختر النوع:</b>",
        reply_markup=AdvancedSearch.genre_selection(all_genres, set()),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SearchStates.waiting_for_year)
async def receive_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
        if year < 1900 or year > 2100:
            await message.answer("❌ السنة يجب أن تكون بين 1900 و 2100")
            return
    except ValueError:
        await message.answer("❌ الرجاء إدخال سنة صحيحة (مثال: 2024)")
        return

    data = await state.get_data()
    filters = data.get("filters", {})
    filters["year"] = year
    await state.update_data(filters=filters)
    await state.set_state(None)

    await message.answer(
        f"📅 <b>تم تطبيق فلتر السنة: {year}</b>\n\nالآن اضغط 'تطبيق الفلتر' أو اختر فلتراً آخر.",
        reply_markup=AdvancedSearch.search_filters(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "search:apply_filters")
async def apply_search_filters(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filters = data.get("filters", {})

    if not filters:
        await callback.answer("⚠️ لم يتم تطبيق أي فلاتر بعد", show_alert=True)
        return

    results = await search_series("", filters)

    if not results:
        await callback.message.edit_text(
            "😔 <b>لا توجد نتائج مطابقة للفلاتر المحددة</b>\n\nحاول تغيير الفلاتر أو إعادة تعيينها.",
            reply_markup=AdvancedSearch.search_filters(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🔍 <b>نتائج البحث</b>\n\nتم العثور على {len(results)} مسلسل",
        reply_markup=AdvancedSearch.search_results("", results),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "search:suggestions")
async def show_suggestions(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.title, SUM(e.views) as total_views
            FROM series s JOIN episodes e ON s.id = e.series_id
            GROUP BY s.id ORDER BY total_views DESC LIMIT 5
            """
        )
        popular = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT id, title FROM series ORDER BY created_at DESC LIMIT 5"
        )
        recent = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT s.id, s.title, AVG(r.rating) as avg_rating
            FROM series s JOIN ratings r ON s.id = r.series_id
            GROUP BY s.id HAVING COUNT(r.user_id) >= 1
            ORDER BY avg_rating DESC LIMIT 5
            """
        )
        top_rated = await cursor.fetchall()

    builder = InlineKeyboardBuilder()

    if popular:
        builder.row(InlineKeyboardButton(text="🔥 الأكثر مشاهدة", callback_data="ignore"))
        for sid, title, views in popular:
            builder.row(InlineKeyboardButton(text=f"📺 {title} ({views} مشاهدة)", callback_data=f"s:{sid}"))

    if recent:
        builder.row(InlineKeyboardButton(text="🆕 الأحدث", callback_data="ignore"))
        for sid, title in recent:
            builder.row(InlineKeyboardButton(text=f"✨ {title}", callback_data=f"s:{sid}"))

    if top_rated:
        builder.row(InlineKeyboardButton(text="⭐ الأعلى تقييماً", callback_data="ignore"))
        for sid, title, rating in top_rated:
            stars = "⭐" * max(1, round(rating))
            builder.row(InlineKeyboardButton(text=f"{stars} {title} ({rating:.1f})", callback_data=f"s:{sid}"))

    builder.row(InlineKeyboardButton(text="🔙 للبحث", callback_data="search:filters"))

    await callback.message.edit_text(
        "💡 <b>اقتراحات البحث</b>\n\nاختر من الاقتراحات أدناه:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()
