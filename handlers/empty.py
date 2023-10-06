from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from models.user import User

router = Router()


@router.message(Command("<command>"))
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await msg.reply(user.get_string("<command>"))
