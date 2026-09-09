from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

# بادئات الأزرار التي يجب أن تكون مقتصرة على الأدمن فقط
ADMIN_ONLY_PREFIXES = (
    "admin:",
    "confirm_delete:",
    "broadcast:",
)


class AdminCheck(BaseMiddleware):
    """يمنع غير الأدمن من استخدام أزرار لوحة التحكم، ويترك باقي الأزرار تعمل للجميع."""

    def __init__(self, admin_ids: list[int]):
        self.admin_ids = set(admin_ids)
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        callback_data = event.data or ""

        if callback_data.startswith(ADMIN_ONLY_PREFIXES):
            if event.from_user.id not in self.admin_ids:
                await event.answer("❌ هذا الإجراء للأدمن فقط", show_alert=True)
                return

        return await handler(event, data)
