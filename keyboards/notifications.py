from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class NotificationSystem:
    """نظام الإشعارات"""

    @staticmethod
    def notification_settings(user_prefs: dict):
        builder = InlineKeyboardBuilder()

        new_eps_status = "✅ مفعل" if user_prefs.get("new_episodes") else "❌ معطل"
        builder.row(
            InlineKeyboardButton(
                text=f"🆕 الحلقات الجديدة: {new_eps_status}", callback_data="notify:toggle:new_eps"
            )
        )

        updates_status = "✅ مفعل" if user_prefs.get("series_updates") else "❌ معطل"
        builder.row(
            InlineKeyboardButton(
                text=f"📢 تحديثات المسلسلات: {updates_status}", callback_data="notify:toggle:updates"
            )
        )

        rec_status = "✅ مفعل" if user_prefs.get("recommendations") else "❌ معطل"
        builder.row(
            InlineKeyboardButton(
                text=f"💡 توصيات المشاهدة: {rec_status}", callback_data="notify:toggle:recs"
            )
        )

        quiet_status = "🌙 مفعل" if user_prefs.get("quiet_hours") else "☀️ معطل"
        builder.row(
            InlineKeyboardButton(text=f"🔇 ساعات الهدوء: {quiet_status}", callback_data="notify:quiet_hours")
        )

        if user_prefs.get("quiet_hours"):
            builder.row(
                InlineKeyboardButton(
                    text=f"⏰ من {user_prefs.get('quiet_start', '23:00')} إلى {user_prefs.get('quiet_end', '07:00')}",
                    callback_data="notify:set_quiet_time",
                )
            )

        builder.row(
            InlineKeyboardButton(text="🔙 للإعدادات", callback_data="settings:main"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()

    @staticmethod
    def episode_alert(series_title: str, season: int, ep_number: int, ep_title: str = ""):
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🎬 شاهد الآن", callback_data="watch_now:latest"))
        builder.row(
            InlineKeyboardButton(
                text=f"📺 {series_title} - م{season} ح{ep_number}", callback_data="go_series:latest"
            )
        )
        builder.row(
            InlineKeyboardButton(text="⭐ حفظ للمشاهدة لاحقاً", callback_data="watchlist:add:latest"),
            InlineKeyboardButton(text="🔕 تجاهل", callback_data="notify:dismiss"),
        )
        return builder.as_markup()
