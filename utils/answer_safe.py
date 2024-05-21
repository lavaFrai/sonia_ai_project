import re

import aiogram.exceptions
from aiogram.enums import ParseMode
from aiogram.types import Message


def split_string(text, chunk_size=4096):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


async def answer_safe(message: Message, text: str, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2):
    parts = split_string(text)

    for part in parts:
        try:
            await message.answer(part,
                                 parse_mode=parse_mode,
                                 reply_markup=reply_markup if part == parts[-1] else None)
        except aiogram.exceptions.TelegramBadRequest as e:
            print(text)
            print(e, e.message)
            await message.answer(part,
                                 parse_mode=None,
                                 reply_markup=reply_markup if part == parts[-1] else None)
