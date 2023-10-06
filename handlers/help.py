from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from models.user import User

router = Router()


@router.message(Command("help"))
async def on_help(msg: Message):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("help"))
