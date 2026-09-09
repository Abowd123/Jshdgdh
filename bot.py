import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS, AUTO_BACKUP_HOURS
from database.models import init_db
from handlers import (
    start,
    admin_add,
    admin_manage,
    admin_stats,
    admin_backup,
    user_browse,
    search,
    inline,
    ratings,
    menu_nav,
    fallback,
)
from middlewares import AdminCheck, SubscriptionCheck, Throttling

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود. أضفه في ملف .env")

    # تهيئة قاعدة البيانات
    await init_db()
    logger.info("✅ تم تهيئة قاعدة البيانات")

    # إنشاء البوت والموزع
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # إضافة الوسائط (Middlewares)
    dp.message.middleware(Throttling())
    dp.message.middleware(SubscriptionCheck())
    dp.callback_query.middleware(AdminCheck(ADMIN_IDS))

    # تسجيل الموجهات (Routers)
    dp.include_router(start.router)
    dp.include_router(admin_add.router)
    dp.include_router(admin_manage.router)
    dp.include_router(admin_stats.router)
    dp.include_router(admin_backup.router)
    dp.include_router(user_browse.router)
    dp.include_router(search.router)
    dp.include_router(ratings.router)
    dp.include_router(inline.router)
    dp.include_router(menu_nav.router)  # أزرار لوحة المفاتيح السفلية الثابتة
    dp.include_router(fallback.router)  # يجب أن يبقى الأخير دائماً

    logger.info("✅ تم تحميل جميع الموجهات")

    # مهمة النسخ الاحتياطي التلقائي
    if AUTO_BACKUP_HOURS > 0:
        asyncio.create_task(admin_backup.scheduled_backup_task(bot, AUTO_BACKUP_HOURS))
        logger.info(f"✅ تم جدولة النسخ الاحتياطي التلقائي كل {AUTO_BACKUP_HOURS} ساعة")

    # بدء البوت
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
