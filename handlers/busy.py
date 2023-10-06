from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from main import server
from models.user import User
from states import Global

router = Router()


@router.message(Global.busy)
async def on_cancel(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("busy"))
