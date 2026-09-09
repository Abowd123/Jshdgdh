import asyncio
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.backup import create_backup, cleanup_old_backups
from config import ADMIN_IDS

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(F.text == "/backup")
async def manual_backup(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ غير مصرح لك")
        return

    await message.answer("🔄 جاري إنشاء النسخة الاحتياطية...")

    try:
        backup_path = await create_backup()
        await message.answer_document(
            document=FSInputFile(backup_path),
            caption=f"💾 نسخة احتياطية - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )
        cleanup_old_backups(keep=7)
        await message.answer("✅ تم إنشاء النسخة الاحتياطية بنجاح")
    except Exception as e:
        await message.answer(f"❌ خطأ في النسخ الاحتياطي: {e}")


@router.callback_query(F.data == "admin:backup")
async def backup_menu(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💾 إنشاء نسخة الآن", callback_data="backup:create"))
    builder.row(InlineKeyboardButton(text="🔙 للوحة التحكم", callback_data="admin:panel"))

    await callback.message.edit_text(
        "💾 <b>نظام النسخ الاحتياطي</b>\n\n"
        "احرص على عمل نسخ احتياطية دورية لقاعدة البيانات.\n"
        f"النسخ التلقائي مفعّل حسب إعداد AUTO_BACKUP_HOURS في .env",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "backup:create")
async def create_backup_now(callback: CallbackQuery):
    await callback.answer("🔄 جاري الإنشاء...")

    backup_path = await create_backup()
    cleanup_old_backups(keep=7)

    await callback.message.answer_document(
        document=FSInputFile(backup_path),
        caption=f"💾 نسخة احتياطية - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )
    await callback.message.edit_text("✅ <b>تم إنشاء النسخة الاحتياطية بنجاح</b>", parse_mode="HTML")


async def scheduled_backup_task(bot, interval_hours: int = 24):
    """مهمة مجدولة للنسخ الاحتياطي التلقائي، تُشغّل في الخلفية طوال عمر البوت."""
    while True:
        await asyncio.sleep(interval_hours * 3600)
        try:
            backup_path = await create_backup()
            cleanup_old_backups(keep=7)

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_document(
                        chat_id=admin_id,
                        document=FSInputFile(backup_path),
                        caption=f"💾 نسخة احتياطية تلقائية - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send backup to admin {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
