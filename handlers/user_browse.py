from math import ceil

from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from keyboards.series_browse import SeriesBrowse
from keyboards.series_detail import SeriesDetail
from keyboards.episode_player import EpisodePlayer
from keyboards.watchlist import Watchlist
from config import DATABASE_PATH, ITEMS_PER_PAGE

router = Router()


@router.callback_query(F.data == "browse:series")
async def browse_series(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, total_eps FROM series ORDER BY title"
        )
        all_series = await cursor.fetchall()

    total_pages = max(1, ceil(len(all_series) / ITEMS_PER_PAGE))
    page_series = all_series[:ITEMS_PER_PAGE]

    await callback.message.edit_text(
        "📚 <b>جميع المسلسلات</b>\n\nاختر المسلسل الذي تريد مشاهدته:",
        reply_markup=SeriesBrowse.series_list(page_series, 0, total_pages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def paginate_series(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, total_eps FROM series ORDER BY title"
        )
        all_series = await cursor.fetchall()

    total_pages = max(1, ceil(len(all_series) / ITEMS_PER_PAGE))
    start = page * ITEMS_PER_PAGE
    page_series = all_series[start : start + ITEMS_PER_PAGE]

    await callback.message.edit_text(
        "📚 <b>جميع المسلسلات</b>\n\nاختر المسلسل الذي تريد مشاهدته:",
        reply_markup=SeriesBrowse.series_list(page_series, page, total_pages),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("s:"))
async def show_series(callback: CallbackQuery):
    series_id = int(callback.data.split(":")[1])

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT title, description, poster_id, total_eps, is_complete "
            "FROM series WHERE id = ?",
            (series_id,),
        )
        series = await cursor.fetchone()

        cursor = await db.execute(
            """
            SELECT season, COUNT(*) as eps_count
            FROM episodes
            WHERE series_id = ?
            GROUP BY season
            ORDER BY season
            """,
            (series_id,),
        )
        seasons = await cursor.fetchall()

    if not series:
        await callback.answer("❌ المسلسل غير موجود")
        return

    title, desc, poster, total_eps, is_complete = series
    status = "✅ مكتمل" if is_complete else "🔄 مستمر"

    text = f"<b>{title}</b>\n\n"
    if desc:
        text += f"{desc}\n\n"
    text += f"📺 عدد الحلقات: {total_eps}\n"
    text += f"📊 الحالة: {status}"

    await callback.message.edit_text(
        text,
        reply_markup=SeriesDetail.series_overview(series_id, seasons, total_eps),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("season:"))
async def show_season(callback: CallbackQuery):
    # season:{series_id}:{season} -> نعرض قائمة الحلقات مباشرة من الصفحة الأولى
    _, series_id, season = callback.data.split(":")
    callback.data = f"ep_list:{series_id}:{season}:0"
    await show_episodes(callback)


@router.callback_query(F.data.startswith("ep_list:"))
async def show_episodes(callback: CallbackQuery):
    _, series_id, season, page = callback.data.split(":")
    series_id = int(series_id)
    season = int(season)
    page = int(page)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        offset = page * ITEMS_PER_PAGE
        cursor = await db.execute(
            """
            SELECT ep_number, title,
                   (SELECT COUNT(*) FROM watch_history WHERE episode_id = episodes.id) as watched
            FROM episodes
            WHERE series_id = ? AND season = ?
            ORDER BY ep_number
            LIMIT ? OFFSET ?
            """,
            (series_id, season, ITEMS_PER_PAGE, offset),
        )
        episodes = await cursor.fetchall()

        cursor = await db.execute("SELECT title FROM series WHERE id = ?", (series_id,))
        row = await cursor.fetchone()

    if not row:
        await callback.answer("❌ المسلسل غير موجود")
        return

    series_title = row[0]

    if not episodes:
        await callback.answer("لا توجد حلقات في هذا الموسم بعد", show_alert=True)
        return

    await callback.message.edit_text(
        f"📺 <b>{series_title}</b> - الموسم {season}\n\nاختر الحلقة:",
        reply_markup=SeriesDetail.episodes_grid(series_id, season, episodes, page),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ep_page:"))
async def paginate_episodes(callback: CallbackQuery):
    _, series_id, season, page = callback.data.split(":")
    callback.data = f"ep_list:{series_id}:{season}:{page}"
    await show_episodes(callback)


@router.callback_query(F.data.startswith("ep:"))
async def send_episode(callback: CallbackQuery):
    _, series_id, season, ep_number = callback.data.split(":")
    series_id = int(series_id)
    season = int(season)
    ep_number = int(ep_number)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT e.id, e.file_id, e.title, e.views, s.title as series_title
            FROM episodes e
            JOIN series s ON e.series_id = s.id
            WHERE e.series_id = ? AND e.season = ? AND e.ep_number = ?
            """,
            (series_id, season, ep_number),
        )
        episode = await cursor.fetchone()

        if not episode:
            await callback.answer("❌ الحلقة غير موجودة")
            return

        ep_id, file_id, ep_title, views, series_title = episode

        cursor = await db.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM episodes WHERE series_id = ? AND season = ? AND ep_number < ?) > 0,
                (SELECT COUNT(*) FROM episodes WHERE series_id = ? AND season = ? AND ep_number > ?) > 0
            """,
            (series_id, season, ep_number, series_id, season, ep_number),
        )
        has_prev, has_next = await cursor.fetchone()

        await db.execute("UPDATE episodes SET views = views + 1 WHERE id = ?", (ep_id,))
        await db.execute(
            "INSERT INTO watch_history (user_id, episode_id, progress) VALUES (?, ?, 100)",
            (callback.from_user.id, ep_id),
        )
        await db.commit()

    caption = (
        f"🎬 <b>{series_title}</b>\n"
        f"الموسم {season} • الحلقة {ep_number}\n"
        f"{ep_title or ''}\n\n"
        f"👁 {views + 1} مشاهدة"
    )

    await callback.message.answer_video(
        video=file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=EpisodePlayer.player_controls(
            series_id, season, ep_number, bool(has_prev), bool(has_next)
        ),
    )
    await callback.answer("✅ تم إرسال الحلقة")


# ---------- المفضلة ----------

@router.callback_query(F.data == "fav:list")
async def show_favorites(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.title, 0, 0
            FROM favorites f
            JOIN series s ON f.series_id = s.id
            WHERE f.user_id = ?
            """,
            (callback.from_user.id,),
        )
        favorites = await cursor.fetchall()

    if not favorites:
        await callback.answer("⭐ قائمة المفضلة فارغة حالياً", show_alert=True)
        return

    await callback.message.edit_text(
        "⭐ <b>مفضلتك</b>",
        reply_markup=Watchlist.favorites_list(favorites),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fav:add:"))
async def add_favorite(callback: CallbackQuery):
    series_id = int(callback.data.split(":")[2])
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, series_id) VALUES (?, ?)",
            (callback.from_user.id, series_id),
        )
        await db.commit()
    await callback.answer("⭐ تمت الإضافة للمفضلة")


# ---------- الأكثر مشاهدة / الأحدث ----------

@router.callback_query(F.data == "top:viewed")
async def top_viewed(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.title, SUM(e.views) as total_views
            FROM series s JOIN episodes e ON s.id = e.series_id
            GROUP BY s.id
            ORDER BY total_views DESC
            LIMIT 10
            """
        )
        rows = await cursor.fetchall()

    if not rows:
        await callback.answer("لا توجد بيانات مشاهدة بعد", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for sid, title, views in rows:
        builder.button(text=f"🔥 {title} ({views} مشاهدة)", callback_data=f"s:{sid}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"))

    await callback.message.edit_text(
        "🔥 <b>الأكثر مشاهدة</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "latest:eps")
async def latest_episodes(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT s.id, s.title, e.season, e.ep_number
            FROM episodes e JOIN series s ON e.series_id = s.id
            ORDER BY e.added_at DESC
            LIMIT 10
            """
        )
        rows = await cursor.fetchall()

    if not rows:
        await callback.answer("لا توجد إضافات بعد", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for sid, title, season, ep_num in rows:
        builder.button(
            text=f"🆕 {title} - م{season} ح{ep_num}",
            callback_data=f"ep:{sid}:{season}:{ep_num}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"))

    await callback.message.edit_text(
        "🆕 <b>آخر الإضافات</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_button(callback: CallbackQuery):
    await callback.answer()
