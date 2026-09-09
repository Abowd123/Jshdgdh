from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query()
async def fallback_callback(callback: CallbackQuery):
    """يلتقط أي زر لم يُعالج بعد في أي راوتر آخر، لتفادي بقاء الزر معلقاً بلا استجابة."""
    await callback.answer("⏳ هذه الميزة قيد التطوير", show_alert=False)
