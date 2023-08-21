import openai
from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.non_context_action import get_non_context_voice_keyboard
from main import server
from states import Global
from utils.file_data import FileData

router = Router()


@router.message(lambda x: x.content_type == ContentType.VOICE, StateFilter(None))
async def on_non_context_voice(msg: Message, state: FSMContext):
    await msg.reply(server.get_string("non-context-action.non_context_voice.action-select"),
                    reply_markup=await get_non_context_voice_keyboard(FileData(msg.voice).get_data()))


@router.callback_query(F.data.startswith("non_context_voice.transcribe"), StateFilter(None))
async def on_non_context_voice_transcribe(cb: CallbackQuery, state: FSMContext):
    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(server.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        try:
            file = await server.download_file_by_id(FileData(source_message.voice).get_data(), "mp3")
            response = await openai.Audio.atranscribe(
                model='whisper-1',
                file=open(file, 'rb')
            )
            await source_message.reply(response['text'])
        finally:
            await state.clear()
            await cb.answer()
            await server.delete_file(file)
