from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from main import server
from states import Global

router = Router()


@router.message(Global.busy)
async def on_cancel(msg: Message, state: FSMContext):
    await msg.reply(server.get_string("busy"))
