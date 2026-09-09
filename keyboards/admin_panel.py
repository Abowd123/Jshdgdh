from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminPanel:
    """لوحة تحكم المطور"""

    @staticmethod
    def main_panel():
        builder = InlineKeyboardBuilder()

        builder.row(InlineKeyboardButton(text="📝 إدارة المسلسلات", callback_data="admin:series_manage"))
        builder.row(
            InlineKeyboardButton(text="➕ إضافة حلقة جديدة", callback_data="admin:add_ep"),
            InlineKeyboardButton(text="⚡ إضافة سريعة", callback_data="admin:batch_add"),
        )

        builder.row(InlineKeyboardButton(text="📊 إحصائيات شاملة", callback_data="admin:full_stats"))

        builder.row(
            InlineKeyboardButton(text="📢 إرسال إعلان", callback_data="broadcast:hint"),
            InlineKeyboardButton(text="💾 نسخ احتياطي", callback_data="admin:backup"),
        )

        builder.row(InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="main_menu"))

        return builder.as_markup()

    @staticmethod
    def series_management():
        builder = InlineKeyboardBuilder()

        builder.row(InlineKeyboardButton(text="🆕 إنشاء مسلسل جديد (/newseries)", callback_data="admin:new_series_hint"))
        builder.row(InlineKeyboardButton(text="🗑 حذف مسلسل (/delseries اسم)", callback_data="admin:del_series_hint"))
        builder.row(InlineKeyboardButton(text="🗑 حذف حلقة (/del رقم)", callback_data="admin:del_ep_hint"))
        builder.row(InlineKeyboardButton(text="🔙 للوحة التحكم", callback_data="admin:panel"))

        return builder.as_markup()

    @staticmethod
    def stats_dashboard(stats: dict):
        """
        stats: {
            'total_users': int, 'active_today': int, 'total_series': int,
            'total_episodes': int, 'total_views': int, 'storage_used': str
        }
        """
        builder = InlineKeyboardBuilder()

        builder.row(InlineKeyboardButton(text=f"👥 المستخدمين: {stats['total_users']}", callback_data="admin:user_details"))
        builder.row(InlineKeyboardButton(text=f"🟢 نشط اليوم (24h): {stats['active_today']}", callback_data="ignore"))
        builder.row(
            InlineKeyboardButton(text=f"📚 المسلسلات: {stats['total_series']}", callback_data="browse:series"),
            InlineKeyboardButton(text=f"🎬 الحلقات: {stats['total_episodes']}", callback_data="ignore"),
        )
        builder.row(InlineKeyboardButton(text=f"👁 المشاهدات: {stats['total_views']}", callback_data="ignore"))
        builder.row(InlineKeyboardButton(text=f"💾 المساحة: {stats['storage_used']}", callback_data="ignore"))

        builder.row(
            InlineKeyboardButton(text="🔄 تحديث", callback_data="admin:refresh_stats"),
            InlineKeyboardButton(text="📥 تصدير CSV", callback_data="admin:export_stats"),
        )
        builder.row(InlineKeyboardButton(text="🔙 للوحة التحكم", callback_data="admin:panel"))

        return builder.as_markup()
