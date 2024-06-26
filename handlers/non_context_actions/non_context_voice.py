import openai
from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile, FSInputFile

from keyboards.non_context_action import get_non_context_voice_keyboard, get_non_context_text_keyboard
from main import server
from models.user import User
from states import Global
from utils.file_data import FileData
from utils.gemini.voice import gemini_transcribe_voice

router = Router()


@router.message(lambda x: x.content_type == ContentType.VOICE, StateFilter(None))
async def on_non_context_voice(msg: Message):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("non-context-action.non_context_voice.action-select"),
                    reply_markup=await get_non_context_voice_keyboard(FileData(msg.voice).get_data(), user))


@router.callback_query(F.data.startswith("non_context_voice.transcribe"), StateFilter(None))
async def on_non_context_voice_transcribe(cb: CallbackQuery, state: FSMContext):
    server.metrics.videos_transcribed += 1

    user = User.get_by_callback(cb)

    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(user.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        try:
            file = await server.download_file_by_id(FileData(source_message.voice).get_data(), "mp3")

            new_msg = await source_message.reply(await gemini_transcribe_voice(open(file, 'rb')))
        finally:
            await state.clear()
            await cb.answer()
            await server.delete_file(file)


@router.callback_query(F.data.startswith("non_context_voice.download"), StateFilter(None))
async def on_non_context_voice_download(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(user.get_string("non-context-action.non_context_voice.message-error"))
        return

    await state.set_state(Global.busy)
    file = await server.download_file_by_id(FileData(source_message.voice).get_data(), "mp3")
    try:
        await cb.message.answer_document(FSInputFile(file, filename=file))
    finally:
        await server.delete_file(file)
        await state.clear()
        await cb.answer()
