from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.non_context_action import get_non_context_action
from keyboards.start_keyboard import get_language_list_keyboard
from main import server
from models.user import User

router = Router()


@router.message(Command("menu"), StateFilter(None))
async def on_menu(msg: Message, state: FSMContext, user: User):
    await msg.answer(user.get_string("menu"), reply_markup=await get_non_context_action(user))
    await state.clear()
