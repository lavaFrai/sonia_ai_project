from typing import Callable, Dict, Any, Awaitable

import aiogram.types
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from main import server


class UnhandledErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            result = await handler(event, data)
        except BaseException as e:
            server.metrics.add_unhandled_error()
            server.logger.error(f"Unhandled exception <{str(e)}> in {handler} while handling event <{event}>. Data: <{data}>")
            if isinstance(event, aiogram.types.Message) or isinstance(event, aiogram.types.CallbackQuery):
                await server.panic(event.from_user.id, event.chat.id, e, data=data, handler=handler, event=event)
        else:
            return result
