from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.non_context_action import get_non_context_action
from main import server

router = Router()


@router.message(Command("start"))
async def on_start(msg: Message, state: FSMContext):
    await msg.reply(server.get_string("start"), reply_markup=await get_non_context_action())
    await state.clear()
