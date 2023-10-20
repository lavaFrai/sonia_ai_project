from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.non_context_action import get_non_context_action
from keyboards.start_keyboard import get_language_list_keyboard
from main import server
from models.user import User
from utils.filter import CallbackFilter

router = Router()


@router.message(Command("start"))
async def on_start(msg: Message, state: FSMContext):
    user = await server.get_user_by_message(msg)
    if user.state == User.State.language_select:
        await msg.answer(server.get_string("welcome_and_choose_language"), reply_markup=get_language_list_keyboard())
        return

    await msg.answer(user.get_string("start"), reply_markup=await get_non_context_action(user))
    await state.clear()


@router.callback_query(CallbackFilter(starts_with='start.language_set'))
async def on_language_set(cb: CallbackQuery, state: FSMContext, user: User):
    await cb.message.delete()

    language = cb.data.split('.')[2]
    user.language = language
    user.state = User.State.ready
    user.save()

    await cb.answer()
    await cb.message.answer(user.get_string('language_has_been_set'))

    await cb.message.answer(user.get_string("start"), reply_markup=await get_non_context_action(user))
    await state.clear()


@router.message(Command("language"))
async def on_start(msg: Message, state: FSMContext):
    b = 2 / 0
    await msg.answer(server.get_string("welcome_and_choose_language"), reply_markup=get_language_list_keyboard())
