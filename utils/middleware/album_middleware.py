import asyncio
from typing import Union, Callable, Dict, Any, Awaitable, List

from aiogram import BaseMiddleware, types
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message

from states import Global

DEFAULT_DELAY = 1


class MediaGroupMiddleware(BaseMiddleware):
    ALBUM_DATA: Dict[int, List[Message]] = {}

    def __init__(self, delay: Union[int, float] = DEFAULT_DELAY):
        self.delay = delay

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data.get("state")
        if await state.get_state() != Global.dialog:
            return await handler(event, data)

        try:
            self.ALBUM_DATA[event.chat.id].append(event)
            return  # Don't propagate the event
        except KeyError:
            self.ALBUM_DATA[event.chat.id] = [event]
            await asyncio.sleep(self.delay)
            data["album"] = self.ALBUM_DATA.pop(event.chat.id)

        return await handler(event, data)
