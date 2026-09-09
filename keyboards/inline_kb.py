from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_button(callback_data: str, text: str = "🔙 رجوع"):
    """زر رجوع بسيط، مفيد لإلحاقه بأي لوحة مفاتيح."""
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def home_button():
    return InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu")


def confirm_cancel_kb(confirm_data: str, cancel_data: str = "main_menu"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ تأكيد", callback_data=confirm_data),
        InlineKeyboardButton(text="❌ إلغاء", callback_data=cancel_data),
    )
    return builder.as_markup()
