from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.non_context_action import get_non_context_action
from main import server
from models.user import User
from states import Global
from utils.filter import CallbackFilter

router = Router()


@router.callback_query(CallbackFilter(data='cancel-all-actions'))
async def on_cancel(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    if await state.get_state() == Global.busy:
        await cb.message.reply(user.get_string("busy"))
        return
    await cb.message.reply(user.get_string("all-canceled"), reply_markup=await get_non_context_action(user))
    await cb.answer()
    await state.clear()
