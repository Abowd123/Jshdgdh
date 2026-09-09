from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SeriesDetail:
    """صفحة تفاصيل المسلسل"""

    @staticmethod
    def series_overview(series_id: int, seasons: list, total_eps: int):
        """seasons: [(season_num, eps_count), ...]"""
        builder = InlineKeyboardBuilder()
        season_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]

        for season_num, eps_count in seasons:
            emoji = season_emojis[season_num - 1] if 1 <= season_num <= 8 else "📅"
            builder.row(
                InlineKeyboardButton(
                    text=f"{emoji} الموسم {season_num}",
                    callback_data=f"season:{series_id}:{season_num}",
                ),
                InlineKeyboardButton(
                    text=f"📺 {eps_count} حلقة",
                    callback_data=f"ep_list:{series_id}:{season_num}:0",
                ),
            )

        builder.row(
            InlineKeyboardButton(text=f"📊 الكل: {total_eps} حلقة", callback_data="ignore")
        )

        builder.row(
            InlineKeyboardButton(text="⭐ أضف للمفضلة", callback_data=f"fav:add:{series_id}"),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 للمسلسلات", callback_data="browse:series"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()

    @staticmethod
    def episodes_grid(series_id: int, season: int, episodes: list, page: int = 0):
        """episodes: [(ep_num, title, watched), ...]"""
        builder = InlineKeyboardBuilder()

        for ep_num, title, watched in episodes:
            status = "✅ " if watched else "📺 "
            builder.button(
                text=f"{status}{ep_num}",
                callback_data=f"ep:{series_id}:{season}:{ep_num}",
            )

        builder.adjust(5)

        nav_row = []
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀", callback_data=f"ep_page:{series_id}:{season}:{page-1}"
                )
            )
        nav_row.append(InlineKeyboardButton(text=f"📄 {page+1}", callback_data="ignore"))
        nav_row.append(
            InlineKeyboardButton(
                text="▶", callback_data=f"ep_page:{series_id}:{season}:{page+1}"
            )
        )
        builder.row(*nav_row)

        builder.row(
            InlineKeyboardButton(text="🔙 للمواسم", callback_data=f"s:{series_id}"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()
