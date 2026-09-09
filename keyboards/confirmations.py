from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Confirmations:
    """قوائم التأكيد"""

    @staticmethod
    def delete_confirmation(item_type: str, item_name: str, item_id: int):
        """item_type: 'series' | 'episode' | 'user'"""
        type_emoji = {"series": "📚", "episode": "🎬", "user": "👤"}

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"⚠️ تأكيد حذف {type_emoji.get(item_type, '📌')} {item_type}",
                callback_data="ignore",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=f"✅ نعم، احذف",
                callback_data=f"confirm_delete:{item_type}:{item_id}",
            )
        )
        builder.row(InlineKeyboardButton(text="❌ إلغاء", callback_data="admin:panel"))

        return builder.as_markup()

    @staticmethod
    def broadcast_preview(message_preview: str, target_count: int):
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=f"📢 سيتم الإرسال إلى {target_count} مستخدم", callback_data="ignore"
            )
        )
        builder.row(InlineKeyboardButton(text="🚀 إرسال الآن", callback_data="broadcast:send"))
        builder.row(
            InlineKeyboardButton(text="✏️ تعديل الرسالة", callback_data="broadcast:edit"),
            InlineKeyboardButton(text="❌ إلغاء", callback_data="admin:panel"),
        )

        return builder.as_markup()
