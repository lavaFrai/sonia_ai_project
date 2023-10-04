from aiogram import Router
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendChatAction
from aiogram.types import Message, CallbackQuery

from keyboards.chat_dialog_keyboards import get_dialog_stop_keyboard
from main import server
from models.chat_dialog import ChatDialog
from models.chat_message import ChatMessage
from states import Global
from utils import openai_utils
from utils.filter import CallbackFilter

router = Router()


@router.message(Command("dialog"), StateFilter(None))
async def on_command(msg: Message, state: FSMContext):
    await state.set_state(Global.dialog)
    dialog = ChatDialog.create(user_id=msg.from_user.id)
    with open("conf/system-prompt.txt") as f:
        system_prompt = f.read()
    ChatMessage.create(role="system", text=system_prompt, dialog_id=dialog.id)
    await state.set_data({"id": dialog.id})
    await msg.reply(server.get_string("dialog-started"))


@router.callback_query(CallbackFilter(data='dialog.start'), StateFilter(None))
async def on_start_dialog(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Global.dialog)
    dialog = ChatDialog.create(user_id=cb.from_user.id)
    with open("conf/system-prompt.txt") as f:
        system_prompt = f.read()
    ChatMessage.create(role="system", text=system_prompt, dialog_id=dialog.id)
    await state.set_data({"id": dialog.id})
    await cb.answer()
    await cb.message.answer(server.get_string("dialog-started"), reply_markup=await get_dialog_stop_keyboard())


@router.message(Command("stop_dialog"), Global.dialog)
async def on_command(msg: Message, state: FSMContext):
    await state.clear()
    await msg.reply(server.get_string("dialog-stopped"))


@router.callback_query(CallbackFilter(data='dialog.stop'), Global.dialog)
async def on_command(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    await cb.message.reply(server.get_string("dialog-stopped"))
    await server.reset_state_message(cb.message)


@router.message(Global.dialog)
async def on_new_message(msg: Message, state: FSMContext):
    text = msg.text
    await state.set_state(Global.busy)

    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    dialog_id = (await state.get_data())['id']
    ChatMessage.create(text=text, dialog_id=dialog_id)
    new_message = await openai_utils.chatgpt_continue_dialog(history=await ChatDialog.get_dialog_history(dialog_id))
    ChatMessage.create(role=new_message['role'], text=new_message['content'], dialog_id=dialog_id)
    await msg.reply(new_message['content'], parse_mode=None, reply_markup=await get_dialog_stop_keyboard())

    await state.set_state(Global.dialog)
