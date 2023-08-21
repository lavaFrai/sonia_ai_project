from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from main import server

router = Router()


@router.message(Command("help"))
async def on_help(msg: Message):
    await msg.reply(server.get_string("help"))
