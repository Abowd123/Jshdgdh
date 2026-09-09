import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class Throttling(BaseMiddleware):
    """يمنع إرسال الرسائل بمعدل أسرع من الحد المسموح لكل مستخدم."""

    def __init__(self, rate_limit: float = 0.7):
        self.rate_limit = rate_limit
        self._last_call: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is not None:
            now = time.monotonic()
            last = self._last_call.get(user_id, 0)
            if now - last < self.rate_limit:
                return  # تجاهل الرسالة بصمت لتفادي الإزعاج
            self._last_call[user_id] = now

        return await handler(event, data)
