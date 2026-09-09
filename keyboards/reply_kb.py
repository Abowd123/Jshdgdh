from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


class QuickMenu:
    """لوحة أزرار سفلية ثابتة (Reply Keyboard) تكمّل القوائم التفاعلية Inline.

    تتيح للمستخدم الوصول السريع لأهم الأقسام بلمسة واحدة، بينما تبقى
    التفاصيل (تصفح المواسم، الحلقات، التقييمات...) عبر الأزرار الشفافة Inline.
    """

    @staticmethod
    def user_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 المسلسلات"), KeyboardButton(text="🔍 بحث")],
                [KeyboardButton(text="🔥 الأكثر مشاهدة"), KeyboardButton(text="🆕 آخر الإضافات")],
                [KeyboardButton(text="⭐ مفضلتي"), KeyboardButton(text="ℹ️ المساعدة")],
            ],
            resize_keyboard=True,
            input_field_placeholder="اختر من القائمة أو استخدم الأزرار أعلاه...",
        )

    @staticmethod
    def admin_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📚 المسلسلات"), KeyboardButton(text="🔍 بحث")],
                [KeyboardButton(text="➕ إضافة حلقة"), KeyboardButton(text="⚡ إضافة سريعة")],
                [KeyboardButton(text="🛠️ لوحة التحكم"), KeyboardButton(text="📊 الإحصائيات")],
                [KeyboardButton(text="💾 نسخ احتياطي"), KeyboardButton(text="ℹ️ المساعدة")],
            ],
            resize_keyboard=True,
            input_field_placeholder="لوحة تحكم المطور...",
        )

    @staticmethod
    def cancel_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ إلغاء")]],
            resize_keyboard=True,
        )
