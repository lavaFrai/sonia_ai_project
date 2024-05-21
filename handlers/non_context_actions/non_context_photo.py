from contextlib import suppress

import openai
from aiogram import Router, F
from aiogram.enums import ContentType, ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from keyboards.non_context_action import get_non_context_text_keyboard, get_non_context_photo_keyboard
from main import server
from models.user import User
from states import Global
from utils.answer_safe import answer_safe
from utils.file_data import FileData
from utils.gemini.chat_client import gemini_generate_one_message, ChatClient

router = Router()


@router.message(lambda x: x.content_type == ContentType.PHOTO)
async def on_non_context_photo(msg: Message):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("non-context-action.non_context_photo.action-select"),
                    reply_markup=await get_non_context_photo_keyboard(msg.text, user))


@router.callback_query(F.data.startswith("non_context_photo.describe"), StateFilter(None))
async def on_non_context_text_reduce(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(user.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        photo = await server.download_file_by_id(FileData(source_message.photo[-1]).get_data(), "jpg")
        try:

            chat = ChatClient(system_instruction=f"Transcribe everything you see in details. Use language {user.language}.")
            with open(photo, "rb") as f:
                text = await chat.send_media_message(f.read(), "image/jpeg")

            # await new_msg.delete()
            await answer_safe(source_message, text)
            # await source_message.answer_safe(text=text, reply_markup=await get_non_context_text_keyboard(text, user))
        finally:
            with suppress(Exception):
                await server.delete_file(photo)
            await state.clear()
            await cb.answer()
