from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MainMenu:
    """القائمة الرئيسية للمستخدم"""

    @staticmethod
    def start_menu():
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📚 تصفح المسلسلات", callback_data="browse:series")
        )
        builder.row(
            InlineKeyboardButton(
                text="🔍 بحث عن مسلسل", switch_inline_query_current_chat=""
            ),
            InlineKeyboardButton(text="🔥 الأكثر مشاهدة", callback_data="top:viewed"),
        )
        builder.row(
            InlineKeyboardButton(text="🆕 آخر الإضافات", callback_data="latest:eps"),
            InlineKeyboardButton(text="⭐ المفضلة", callback_data="fav:list"),
        )
        builder.row(
            InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="settings:main"),
            InlineKeyboardButton(text="ℹ️ عن البوت", callback_data="about"),
        )
        return builder.as_markup()

    @staticmethod
    def settings_menu():
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🌐 تغيير اللغة", callback_data="settings:lang"))
        builder.row(InlineKeyboardButton(text="🔔 الإشعارات", callback_data="settings:notify"))
        builder.row(InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats:user"))
        builder.row(InlineKeyboardButton(text="🔙 رجوع", callback_data="main_menu"))
        return builder.as_markup()
