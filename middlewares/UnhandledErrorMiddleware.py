import sys
import traceback
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
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_tb(exc_traceback)
            tb = '\n'.join(tb)

            server.metrics.add_unhandled_error()
            server.logger.error(f"Unhandled exception <{type(e).__name__}> in {handler} while handling event <{event}>. Data: <{data}>")
            if isinstance(event, aiogram.types.Message) or isinstance(event, aiogram.types.CallbackQuery):
                await server.panic(tb, e, data=data, handler=handler, event=event)

            raise e
        else:
            return result
