import re

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import aiosqlite

from config import DATABASE_PATH

router = Router()


@router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    bot_username = (await inline_query.bot.get_me()).username

    if not query:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                "SELECT id, title, total_eps FROM series ORDER BY total_eps DESC LIMIT 10"
            )
            series_list = await cursor.fetchall()

        results = [
            InlineQueryResultArticle(
                id=f"series_{sid}",
                title=f"📺 {title}",
                description=f"{total_eps} حلقة",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎬 {title}\nاختر الموسم والحلقة من البوت: @{bot_username}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text="🎬 فتح في البوت",
                            url=f"https://t.me/{bot_username}?start=series_{sid}",
                        )
                    ]]
                ),
            )
            for sid, title, total_eps in series_list
        ]
        await inline_query.answer(results, cache_time=300)
        return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, total_eps FROM series WHERE title LIKE ? LIMIT 5",
            (f"%{query}%",),
        )
        series_results = await cursor.fetchall()

        episode_results = []
        numbers = re.findall(r"\d+", query)
        if numbers:
            ep_number = int(numbers[0])
            cursor = await db.execute(
                """
                SELECT e.series_id, s.title, e.season, e.ep_number
                FROM episodes e JOIN series s ON e.series_id = s.id
                WHERE s.title LIKE ? AND e.ep_number = ?
                LIMIT 5
                """,
                (f"%{query}%", ep_number),
            )
            episode_results = await cursor.fetchall()

    results = []

    for sid, title, total_eps in series_results:
        results.append(
            InlineQueryResultArticle(
                id=f"series_{sid}",
                title=f"📚 {title}",
                description=f"المسلسل كاملاً - {total_eps} حلقة",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎬 {title}\nاختر الموسم والحلقة من البوت: @{bot_username}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text="🎬 فتح في البوت",
                            url=f"https://t.me/{bot_username}?start=series_{sid}",
                        )
                    ]]
                ),
            )
        )

    for sid, title, season, ep_num in episode_results:
        results.append(
            InlineQueryResultArticle(
                id=f"ep_{sid}_{season}_{ep_num}",
                title=f"🎬 {title} - حلقة {ep_num}",
                description=f"الموسم {season}",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎬 {title}\nالموسم {season} • الحلقة {ep_num}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text="▶ شاهد الآن",
                            url=f"https://t.me/{bot_username}?start=ep_{sid}_{season}_{ep_num}",
                        )
                    ]]
                ),
            )
        )

    await inline_query.answer(results, cache_time=60)
