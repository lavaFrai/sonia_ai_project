from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from main import server

router = Router()


@router.message(Command("<command>"))
async def on_command(msg: Message, state: FSMContext):
    await msg.reply(server.get_string("<command>"))
