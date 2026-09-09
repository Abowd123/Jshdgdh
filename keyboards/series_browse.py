from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SeriesBrowse:
    """قوائم تصفح المسلسلات"""

    @staticmethod
    def series_list(series_data: list, page: int = 0, total_pages: int = 1):
        """series_data: [(id, title, total_eps), ...]"""
        builder = InlineKeyboardBuilder()
        emojis = ["🎭", "🎪", "🎯", "🌟", "💫", "✨", "🎨", "🎬"]

        for i, (sid, title, eps) in enumerate(series_data):
            emoji = emojis[i % len(emojis)]
            builder.row(
                InlineKeyboardButton(text=f"{emoji} {title}", callback_data=f"s:{sid}"),
                InlineKeyboardButton(text=f"📺 {eps}", callback_data=f"s:{sid}"),
            )

        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="◀ السابق", callback_data=f"page:{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="ignore")
        )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="التالي ▶", callback_data=f"page:{page+1}")
            )
        builder.row(*nav_buttons)

        builder.row(
            InlineKeyboardButton(text="🔍 بحث سريع", switch_inline_query_current_chat=""),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()
