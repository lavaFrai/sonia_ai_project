from aiogram import Router
from aiogram.enums import ChatAction, ContentType
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
from utils.openai_utils import whisper_transcribe_voice

router = Router()


@router.message(Command("dialog"), StateFilter(None))
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.set_state(Global.dialog)
    dialog = ChatDialog.create(user_id=msg.from_user.id)
    with open("conf/system-prompt.txt") as f:
        system_prompt = f.read()
    ChatMessage.create(role="system", text=system_prompt, dialog_id=dialog.id)
    await state.set_data({"id": dialog.id})
    await msg.reply(user.get_string("dialog-started"))


@router.callback_query(CallbackFilter(data='dialog.start'), StateFilter(None))
async def on_start_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await state.set_state(Global.dialog)
    created_message = await cb.message.answer(user.get_string("dialog-started"), reply_markup=await get_dialog_stop_keyboard(user))
    dialog = ChatDialog.create(user_id=cb.from_user.id, last_bot_message=created_message.message_id)
    with open("conf/system-prompt.txt") as f:
        system_prompt = f.read()
    ChatMessage.create(role="system", text=system_prompt, dialog_id=dialog.id)
    await state.set_data({"id": dialog.id})
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
    await cb.message.reply(user.get_string("dialog-stopped"), reply_markup=await get_dialog_resume_keyboard(dialog_id, user))
    await server.reset_state_message_no_reply(cb.message.chat.id, user)


@router.callback_query(CallbackFilter(starts_with='dialog.resume'), StateFilter(None))
async def on_resume_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await server.delete_reply_markup_if_possible(cb.message.chat.id, cb.message.message_id)
    await state.set_state(Global.dialog)
    dialog_id = int(cb.data.split('.')[2])
    dialog = ChatDialog.get(id=dialog_id)
    await state.set_data({'id': str(dialog_id)})
    created_message = await cb.message.reply(user.get_string('dialog-resumed'), reply_markup=await get_dialog_stop_keyboard(user))
    dialog.last_bot_message = created_message.message_id
    dialog.save()
    await cb.answer()


async def dialog_next_message(state, msg, message_text):
    await state.set_state(Global.busy)

    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    dialog_id = (await state.get_data())['id']
    dialog: ChatDialog = ChatDialog.get(id=dialog_id)

    user = User.get_by_message(msg)

    await server.delete_reply_markup_if_possible(msg.chat.id, dialog.last_bot_message)

    ChatMessage.create(text=message_text, dialog_id=dialog_id)
    new_message = await openai_utils.chatgpt_continue_dialog(history=await ChatDialog.get_dialog_history(dialog_id))
    ChatMessage.create(role=new_message['role'], text=new_message['content'], dialog_id=dialog_id)
    created_msg = await msg.answer(new_message['content'], parse_mode=None,
                                   reply_markup=await get_dialog_stop_keyboard(user))
    dialog.last_bot_message = created_msg.message_id
    dialog.save()

    await state.set_state(Global.dialog)


@router.message(Global.dialog, lambda x: x.content_type in [ContentType.TEXT])
async def on_new_message(msg: Message, state: FSMContext):
    text = msg.text
    await dialog_next_message(state, msg, text)


@router.message(Global.dialog, lambda x: x.content_type in [ContentType.VOICE])
async def on_new_message(msg: Message, state: FSMContext):
    file = await server.download_file_by_id(FileData(msg.voice).get_data(), "mp3")
    text = await whisper_transcribe_voice(open(file, 'rb'))
    await server.delete_file(file)

    await dialog_next_message(state, msg, text)
