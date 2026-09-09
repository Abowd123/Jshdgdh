from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from keyboards.rating_system import RatingSystem
from config import DATABASE_PATH

router = Router()


@router.callback_query(F.data.startswith("rate:"))
async def open_rating(callback: CallbackQuery):
    _, series_id, season, ep_number = callback.data.split(":")
    series_id, season, ep_number = int(series_id), int(season), int(ep_number)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT rating FROM ratings
            WHERE user_id = ? AND series_id = ? AND season = ? AND ep_number = ?
            """,
            (callback.from_user.id, series_id, season, ep_number),
        )
        row = await cursor.fetchone()

    current_rating = row[0] if row else 0

    await callback.message.answer(
        "⭐ <b>قيّم هذه الحلقة:</b>",
        reply_markup=RatingSystem.rate_episode(series_id, season, ep_number, current_rating),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate_set:"))
async def set_rating(callback: CallbackQuery):
    _, series_id, season, ep_number, stars = callback.data.split(":")
    series_id, season, ep_number, stars = int(series_id), int(season), int(ep_number), int(stars)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO ratings (user_id, series_id, season, ep_number, rating)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, series_id, season, ep_number)
            DO UPDATE SET rating = excluded.rating
            """,
            (callback.from_user.id, series_id, season, ep_number, stars),
        )
        await db.commit()

    await callback.message.edit_text(
        f"⭐ <b>قيّم هذه الحلقة:</b>\n\nتم حفظ تقييمك: {'⭐' * stars}",
        reply_markup=RatingSystem.rate_episode(series_id, season, ep_number, stars),
        parse_mode="HTML",
    )
    await callback.answer("✅ تم حفظ التقييم")
