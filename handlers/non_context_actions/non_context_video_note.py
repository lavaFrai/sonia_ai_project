from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from keyboards.non_context_action import get_non_context_video_note_keyboard, get_non_context_text_keyboard
from main import server
from models.user import User
from states import Global
from utils.file_data import FileData
from moviepy.editor import VideoFileClip

from utils.gemini.voice import gemini_transcribe_voice
from utils.openai_utils import whisper_transcribe_voice, whisper_transcribe_voice_in_video

router = Router()


@router.message(lambda x: x.content_type == ContentType.VIDEO_NOTE, StateFilter(None))
async def on_non_context_voice(msg: Message):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("non-context-action.non_context_video_note.action-select"),
                    reply_markup=await get_non_context_video_note_keyboard(FileData(msg.video_note).get_data(), user))


@router.callback_query(F.data.startswith("non_context_video_note.transcribe-audio"), StateFilter(None))
async def on_non_context_voice_transcribe(cb: CallbackQuery, state: FSMContext):
    server.metrics.voices_transcribed += 1

    user = User.get_by_callback(cb)

    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(user.get_string("non-context-action.non_context_voice.message-error"))
        return
    await state.set_state(Global.busy)
    try:
        video_file = await server.download_file_by_id(FileData(source_message.video_note).get_data(), "mp4")
        video = VideoFileClip(video_file)
        audio_file = await server.create_file(ex='mp3')
        audio = video.audio
        audio.write_audiofile(audio_file)

        audio.close()
        video.close()

        text = await server.await_with_typing_status(
            gemini_transcribe_voice(open(audio_file, 'rb')),
            source_message.chat.id
        )

        await server.delete_file(audio_file)
        new_msg = await source_message.reply(text)

        await new_msg.reply(user.get_string("non-context-action.non_context_text.action-select"),
                            reply_markup=await get_non_context_text_keyboard(new_msg.text, user))
    finally:
        await state.clear()
        await cb.answer()
        # await server.delete_file(file)


@router.callback_query(F.data.startswith("non_context_video_note.download"), StateFilter(None))
async def on_non_context_video_note_download(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(user.get_string("non-context-action.non_context_voice.message-error"))
        return

    await state.set_state(Global.busy)
    file = await server.download_file_by_id(FileData(source_message.video_note).get_data(), "mp4")
    try:
        await cb.message.answer_document(FSInputFile(file, filename=file))
    finally:
        await server.delete_file(file)
        await state.clear()
        await cb.answer()

