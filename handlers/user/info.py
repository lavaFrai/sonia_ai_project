import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from main import server
from models.user import User

router = Router()


@router.message(Command("info"))
async def on_command(msg: Message, state: FSMContext):
    user: User = await server.get_user_by_message(msg)
    await msg.reply(
        server.get_string("user-info")
        .replace("%id%", str(msg.from_user.id))
        .replace("%subscription_expires%", ("expiring at " + str(user.subscription_expires)
                                            if user.subscription_expires > datetime.datetime.now()
                                            else "`not subscribed`"))
    )
