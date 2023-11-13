import sys

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from models.user import User
import platform
import psutil
from uptime import uptime

router = Router()


@router.message(Command("diagnostics"))
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await msg.reply(f"ℹ️ Bot diagnostics data:\n\n\n"
                    f"System: {platform.machine()}\n\n"
                    f"Python: {sys.version}\n\n"
                    f"Processor: {platform.processor()}\n\n"
                    f"CPU count: {psutil.cpu_count()}\n\n"
                    f"Platform: {platform.platform()}\n\n"
                    f"Platform version: {platform.version()}\n\n"
                    f"Uptime: {int(uptime() // (60 * 60 * 24))}d {int((uptime() // (60 * 60)) % 24)}h {int((uptime() // 60) % 60)}m {int(uptime() % 60)}s\n\n"
                    f"RAM: {psutil.virtual_memory().used // (1024*1024)}M/{psutil.virtual_memory().total // (1024*1024)}M used\n\n")
