from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from keyboards import MainMenu, QuickMenu
from database.queries import upsert_user
from config import ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def start_command(message: Message):
    await upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # لوحة الأزرار السفلية الثابتة (وصول سريع) — تختلف بين الأدمن والمستخدم العادي
    quick_menu = QuickMenu.admin_menu() if message.from_user.id in ADMIN_IDS else QuickMenu.user_menu()
    await message.answer("🏠 أهلاً بك!", reply_markup=quick_menu)

    await message.answer(
        "🏠 <b>مرحباً بك في بوت المسلسلات الكرتونية!</b>\n\n"
        "اختر من القائمة أدناه للبدء:",
        reply_markup=MainMenu.start_menu(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "ℹ️ <b>الأوامر المتاحة</b>\n\n"
        "/start - القائمة الرئيسية\n"
        "/search - بحث عن مسلسل\n"
        "/latest - آخر الإضافات\n"
        "/top - الأكثر مشاهدة\n"
        "/cancel - إلغاء العملية الحالية",
        parse_mode="HTML",
    )


@router.message(Command("cancel"))
async def cancel_command(message: Message, state):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("لا توجد عملية جارية لإلغائها.")
        return
    await state.clear()
    await message.answer("✅ تم الإلغاء.", reply_markup=MainMenu.start_menu())


@router.callback_query(F.data == "about")
async def about(callback):
    await callback.message.edit_text(
        "ℹ️ <b>عن البوت</b>\n\n"
        "بوت لتصفح ومشاهدة حلقات المسلسلات الكرتونية مباشرة داخل تيليجرام.\n"
        "الفيديوهات تُرسل من خوادم تيليجرام مباشرة دون أي تخزين على سيرفر خارجي.",
        reply_markup=MainMenu.start_menu(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback):
    await callback.message.edit_text(
        "🏠 <b>القائمة الرئيسية</b>\n\nاختر من القائمة أدناه:",
        reply_markup=MainMenu.start_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings:main")
async def settings_main(callback):
    await callback.message.edit_text(
        "⚙️ <b>الإعدادات</b>",
        reply_markup=MainMenu.settings_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings:notify")
async def settings_notify(callback):
    from keyboards.notifications import NotificationSystem

    prefs = {"new_episodes": True, "series_updates": True, "recommendations": False, "quiet_hours": False}
    await callback.message.edit_text(
        "🔔 <b>إعدادات الإشعارات</b>",
        reply_markup=NotificationSystem.notification_settings(prefs),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings:lang")
async def settings_lang(callback):
    await callback.answer("اللغة العربية هي اللغة الوحيدة المدعومة حالياً 🇸🇦", show_alert=True)


@router.callback_query(F.data == "stats:user")
async def user_stats(callback):
    import aiosqlite
    from config import DATABASE_PATH

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM watch_history WHERE user_id = ?",
            (callback.from_user.id,),
        )
        watched = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?",
            (callback.from_user.id,),
        )
        favs = (await cursor.fetchone())[0]

    await callback.answer(
        f"📊 شاهدت {watched} حلقة\n⭐ لديك {favs} مسلسل في المفضلة",
        show_alert=True,
    )
