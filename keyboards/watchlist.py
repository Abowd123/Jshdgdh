from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Watchlist:
    """قائمة المتابعة والمفضلة"""

    @staticmethod
    def favorites_list(favorites: list):
        """favorites: [(series_id, title, last_watched_ep, progress), ...]"""
        builder = InlineKeyboardBuilder()

        for sid, title, last_ep, progress in favorites:
            builder.row(InlineKeyboardButton(text=f"📺 {title}", callback_data=f"s:{sid}"))

        builder.row(InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"))

        return builder.as_markup()
