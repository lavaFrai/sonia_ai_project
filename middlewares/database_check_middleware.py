import asyncio
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject



class DatabaseCheckMiddleware(BaseMiddleware):
    def __init__(self):
        ...

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ):
        from main import server
        try:
            a = server.db.execute_sql("SELECT 1;").fetchall()[0][0]
            if a != 1:
                raise AssertionError("Failed to check database health")
        except Exception as e:
            server.logger.warning("Reconnecting db, reason = " + str(e))
            await server.reconnect_db()
            await asyncio.sleep(0.1)
            return await self.__call__(handler, event, data)
        return await handler(event, data)
