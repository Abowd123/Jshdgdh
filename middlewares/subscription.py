from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from config import REQUIRE_SUBSCRIPTION, MAIN_CHANNEL_ID, ADMIN_IDS

# الأوامر المسموح بها دائماً حتى قبل التحقق من الاشتراك
ALLOWED_COMMANDS = {"/start", "/help", "/cancel"}


class SubscriptionCheck(BaseMiddleware):
    """يتحقق من اشتراك المستخدم في القناة الرئيسية قبل السماح له باستخدام البوت،
    إذا كان REQUIRE_SUBSCRIPTION مفعلاً في الإعدادات."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not REQUIRE_SUBSCRIPTION or not MAIN_CHANNEL_ID:
            return await handler(event, data)

        if event.from_user.id in ADMIN_IDS:
            return await handler(event, data)

        if event.text and event.text.split()[0] in ALLOWED_COMMANDS:
            return await handler(event, data)

        try:
            member = await event.bot.get_chat_member(MAIN_CHANNEL_ID, event.from_user.id)
            if member.status in ("left", "kicked"):
                await self._ask_to_subscribe(event)
                return
        except TelegramBadRequest:
            # تعذر التحقق (مثلاً البوت ليس أدمن في القناة) - نسمح بالمرور بدل حجب المستخدم
            return await handler(event, data)

        return await handler(event, data)

    @staticmethod
    async def _ask_to_subscribe(event: Message):
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📢 اشترك في القناة", url=f"https://t.me/c/{str(MAIN_CHANNEL_ID)[4:]}"))
        await event.answer(
            "⚠️ يجب الاشتراك في قناتنا أولاً لاستخدام البوت.",
            reply_markup=builder.as_markup(),
        )
