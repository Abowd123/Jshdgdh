"""
يربط أزرار لوحة المفاتيح السفلية الثابتة (Reply Keyboard) بنفس المنطق
المستخدم أصلاً في القوائم الشفافة (Inline)، بدل تكرار كل شيء من الصفر.
يجب تسجيل هذا الموجّه بعد admin_add و admin_manage و admin_backup حتى
تتوفر الدوال التي يستوردها، وقبل fallback الذي يجب أن يبقى الأخير دائماً.
"""
from math import ceil

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiosqlite

from config import DATABASE_PATH, ITEMS_PER_PAGE, ADMIN_IDS
from keyboards.series_browse import SeriesBrowse
from keyboards.watchlist import Watchlist
from handlers.admin_add import start_add_episode
from handlers.admin_manage import open_panel
from handlers.admin_backup import manual_backup

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(F.text == "📚 المسلسلات")
async def quick_browse_series(message: Message):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT id, title, total_eps FROM series ORDER BY title")
        all_series = await cursor.fetchall()

    total_pages = max(1, ceil(len(all_series) / ITEMS_PER_PAGE))
    page_series = all_series[:ITEMS_PER_PAGE]

    await message.answer(
        "📚 <b>جميع المسلسلات</b>\n\nاختر المسلسل الذي تريد مشاهدته:",
        reply_markup=SeriesBrowse.series_list(page_series, 0, total_pages),
        parse_mode="HTML",
    )


@router.message(Command("top"))
@router.message(F.text == "🔥 الأكثر مشاهدة")
async def quick_top_viewed(message: Message):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.title, SUM(e.views) as total_views
            FROM series s JOIN episodes e ON s.id = e.series_id
            GROUP BY s.id ORDER BY total_views DESC LIMIT 10
            """
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("لا توجد بيانات مشاهدة كافية بعد.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for sid, title, views in rows:
        builder.row(InlineKeyboardButton(text=f"🔥 {title} ({views or 0} مشاهدة)", callback_data=f"s:{sid}"))

    await message.answer(
        "🔥 <b>الأكثر مشاهدة</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(Command("latest"))
@router.message(F.text == "🆕 آخر الإضافات")
async def quick_latest(message: Message):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT e.series_id, s.title, e.season, e.ep_number
            FROM episodes e JOIN series s ON e.series_id = s.id
            ORDER BY e.added_at DESC LIMIT 10
            """
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("لا توجد حلقات مضافة بعد.")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for sid, title, season, ep_num in rows:
        builder.row(
            InlineKeyboardButton(
                text=f"🆕 {title} - م{season} ح{ep_num}",
                callback_data=f"ep:{sid}:{season}:{ep_num}",
            )
        )

    await message.answer(
        "🆕 <b>آخر الحلقات المضافة</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(F.text == "⭐ مفضلتي")
async def quick_favorites(message: Message):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT f.series_id, s.title, 0, 0
            FROM favorites f
            JOIN series s ON s.id = f.series_id
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
            """,
            (message.from_user.id,),
        )
        favorites = await cursor.fetchall()

    if not favorites:
        await message.answer("⭐ قائمة المفضلة فارغة حالياً.")
        return

    await message.answer(
        "⭐ <b>مفضلتك</b>",
        reply_markup=Watchlist.favorites_list(favorites),
        parse_mode="HTML",
    )


@router.message(F.text == "ℹ️ المساعدة")
async def quick_help(message: Message):
    await message.answer(
        "ℹ️ <b>الأوامر المتاحة</b>\n\n"
        "/start - القائمة الرئيسية\n"
        "/search - بحث عن مسلسل\n"
        "/latest - آخر الإضافات\n"
        "/top - الأكثر مشاهدة\n"
        "/cancel - إلغاء العملية الحالية",
        parse_mode="HTML",
    )


# ---------- أزرار الأدمن ----------

@router.message(F.text == "➕ إضافة حلقة")
async def quick_add_episode(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await start_add_episode(message, state)


@router.message(F.text == "⚡ إضافة سريعة")
async def quick_batch_hint(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "⚡ <b>وضع الإضافة السريعة</b>\n\n"
        "أرسل: <code>/batch اسم_المسلسل رقم_الموسم</code>\n"
        "مثال: <code>/batch ناروتو 1</code>\n\n"
        "بعدها أرسل الفيديوهات بالترتيب، وأنهِ بـ /done",
        parse_mode="HTML",
    )


@router.message(F.text == "🛠️ لوحة التحكم")
async def quick_panel(message: Message):
    await open_panel(message)


@router.message(F.text == "📊 الإحصائيات")
async def quick_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📊 من فضلك افتح 🛠️ <b>لوحة التحكم</b> ثم اختر «الإحصائيات الكاملة» لعرض تقرير مفصّل.",
        parse_mode="HTML",
    )


@router.message(F.text == "💾 نسخ احتياطي")
async def quick_backup(message: Message):
    await manual_backup(message)
