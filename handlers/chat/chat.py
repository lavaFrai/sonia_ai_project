import asyncio
from typing import List

import aiogram.exceptions
from aiogram import Router, F
from aiogram.enums import ChatAction, ContentType, ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.chat_dialog_keyboards import get_dialog_stop_keyboard, get_dialog_resume_keyboard
from main import server
from models.chat_dialog import ChatDialog
from models.chat_message import ChatMessage
from models.user import User
from states import Global
from utils import openai_utils
from utils.file_data import FileData
from utils.filter import CallbackFilter
from utils.gemini.chat_client import ChatClient
from utils.gemini.client import PayloadToLargeException
from utils.openai_utils import whisper_transcribe_voice, whisper_transcribe_voice_in_video

router = Router()


async def start_dialog(user_id) -> int:
    dialog = ChatDialog.create(user_id=user_id)
    return dialog.id


@router.message(Command("dialog"), StateFilter(None))
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.set_state(Global.dialog)

    dialog_id = await start_dialog(msg.from_user.id)

    await state.set_data({"id": dialog_id})
    await msg.reply(user.get_string("dialog-started"), parse_mode=None)#, reply_markup=await get_dialog_stop_keyboard(user))


@router.callback_query(CallbackFilter(data='dialog.start'), StateFilter(None))
async def on_start_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await state.set_state(Global.dialog)
    dialog_id = await start_dialog(cb.from_user.id)

    await cb.message.answer(user.get_string("dialog-started"), parse_mode=None)# , reply_markup=await get_dialog_stop_keyboard(user))

    await state.set_data({"id": dialog_id})
    await cb.answer()


@router.message(Command("stop_dialog"), Global.dialog)
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.clear()
    await msg.reply(user.get_string("dialog-stopped"))


@router.callback_query(CallbackFilter(data='dialog.stop'), Global.dialog)
async def on_stop_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    dialog_id = (await state.get_data())['id']
    dialog = ChatDialog.get(id=dialog_id)

    await server.delete_reply_markup_if_possible(cb.message.chat.id, dialog.last_bot_message)

    await state.clear()
    await cb.answer()
    await cb.message.reply(user.get_string("dialog-stopped"))# , reply_markup=await get_dialog_resume_keyboard(dialog_id, user))
    await server.reset_state_message_no_reply(cb.message.chat.id, user)


@router.callback_query(CallbackFilter(starts_with='dialog.resume'), StateFilter(None))
async def on_resume_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await server.delete_reply_markup_if_possible(cb.message.chat.id, cb.message.message_id)
    await state.set_state(Global.dialog)
    dialog_id = int(cb.data.split('.')[2])
    dialog = ChatDialog.get(id=dialog_id)
    await state.set_data({'id': str(dialog_id)})
    created_message = await cb.message.reply(user.get_string('dialog-resumed'))# , reply_markup=await get_dialog_stop_keyboard(user))
    dialog.last_bot_message = created_message.message_id
    dialog.save()
    await cb.answer()


"""async def dialog_next_message(state, msg, message_text):

    await state.set_state(Global.busy)

    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    dialog_id = (await state.get_data())['id']
    dialog: ChatDialog = ChatDialog.get(id=dialog_id)

    user = User.get_by_message(msg)

    await server.delete_reply_markup_if_possible(msg.chat.id, dialog.last_bot_message)

    ChatMessage.create(text=message_text, dialog_id=dialog_id)

    new_message = await server.await_with_typing_status(
        openai_utils.chatgpt_continue_dialog(history=await ChatDialog.get_dialog_history(dialog_id)),
        msg.chat.id
    )

    ChatMessage.create(role=new_message['role'], text=new_message['content'], dialog_id=dialog_id)
    created_msg = await msg.answer(new_message['content'], parse_mode=None,
                                   reply_markup=await get_dialog_stop_keyboard(user))
    dialog.last_bot_message = created_msg.message_id
    dialog.save()

    await state.set_state(Global.dialog)"""


async def get_system_message():
    return open("conf/system-prompt.txt", "r").read()


"""@router.message(Global.dialog, lambda x: x.content_type in [ContentType.TEXT])
async def on_new_message(msg: Message, state: FSMContext):
    server.metrics.chat_messages += 1

    await state.set_state(Global.busy)
    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)

    text = msg.text
    dialog_id = (await state.get_data())['id']
    history = await ChatDialog.get_dialog_history(dialog_id)
    dialog = ChatClient(history=history, system_instruction=await get_system_message())

    response = await dialog.send_message(text)
    await ChatDialog.save_dialog_history(dialog_id, dialog.get_history())

    try:
        await msg.answer(response, parse_mode=ParseMode.MARKDOWN)
    except aiogram.exceptions.TelegramBadRequest:
        await msg.answer(response, parse_mode=None)
    finally:
        await state.set_state(Global.dialog)


@router.message(Global.dialog, lambda x: x.content_type in [ContentType.VOICE])
async def on_new_message(msg: Message, state: FSMContext):
    server.metrics.chat_voice_messages += 1

    await state.set_state(Global.busy)
    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)

    voice_file = await server.download_file_by_id(FileData(msg.voice).get_data(), "ogg")
    dialog_id = (await state.get_data())['id']
    history = await ChatDialog.get_dialog_history(dialog_id)
    dialog = ChatClient(history=history, system_instruction=await get_system_message())

    with open(voice_file, "rb") as f:
        response = await dialog.send_media_message(f.read(), "audio/ogg")
    await ChatDialog.save_dialog_history(dialog_id, dialog.get_history())

    try:
        await msg.answer(response, parse_mode=ParseMode.MARKDOWN)
    except aiogram.exceptions.TelegramBadRequest:
        await msg.answer(response, parse_mode=None)
    finally:
        await state.set_state(Global.dialog)


@router.message(Global.dialog, lambda x: x.content_type in [ContentType.VIDEO_NOTE])
async def on_new_message(msg: Message, state: FSMContext):
    server.metrics.chat_voice_messages += 1

    await state.set_state(Global.busy)
    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)

    voice_file = await server.download_file_by_id(FileData(msg.video_note).get_data(), "mp4")
    dialog_id = (await state.get_data())['id']
    history = await ChatDialog.get_dialog_history(dialog_id)
    dialog = ChatClient(history=history, system_instruction=await get_system_message())

    with open(voice_file, "rb") as f:
        response = await dialog.send_media_message(f.read(), "video/mp4")
    await ChatDialog.save_dialog_history(dialog_id, dialog.get_history())

    try:
        await msg.answer(response, parse_mode=ParseMode.MARKDOWN)
    except aiogram.exceptions.TelegramBadRequest:
        await msg.answer(response, parse_mode=None)
    finally:
        await state.set_state(Global.dialog)"""


@router.message(Global.dialog, lambda x: x)
async def on_new_message(msg: Message, state: FSMContext, album: List[Message], user: User):
    server.metrics.chat_voice_messages += 1

    await state.set_state(Global.busy)
    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)

    messages = []

    dialog_id = (await state.get_data())['id']
    history = await ChatDialog.get_dialog_history(dialog_id)
    chat = ChatClient(history=history, system_instruction=await get_system_message())

    for message in album:
        if message.caption:
            messages.append(chat.build_text_message(message.caption, "user"))

        if message.content_type == ContentType.TEXT:
            messages.append(chat.build_text_message(message.text, "user"))

        elif message.content_type == ContentType.VOICE:
            voice_file = await server.download_file_by_id(FileData(message.voice).get_data(), "ogg")
            with open(voice_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "audio/ogg", "user"))
            await server.delete_file(voice_file)

        elif message.content_type == ContentType.AUDIO:
            voice_file = await server.download_file_by_id(FileData(message.audio).get_data(), "mp3")
            with open(voice_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "audio/mp3", "user"))
            await server.delete_file(voice_file)

        elif message.content_type == ContentType.PHOTO:
            photo_file = await server.download_file_by_id(FileData(message.photo[-1]).get_data(), "jpg")
            with open(photo_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "image/jpeg", "user"))
            await server.delete_file(photo_file)

        else:
            await message.reply(user.get_string("unsupported-media-type").replace("%type%", message.content_type))
            await state.set_state(Global.dialog)
            return

    try:
        response = await chat.send_multiple_messages(messages)
    except PayloadToLargeException:
        await msg.reply(user.get_string("dialog-too-long"))
        await state.clear()
        return
    except Exception as e:
        await msg.reply(user.get_string("dialog-error"))
        await state.clear()
        raise e

    await ChatDialog.save_dialog_history(dialog_id, chat.get_history())

    try:
        await msg.answer(response, parse_mode=ParseMode.MARKDOWN)
    except aiogram.exceptions.TelegramBadRequest:
        await msg.answer(response, parse_mode=None)
    finally:
        await state.set_state(Global.dialog)
