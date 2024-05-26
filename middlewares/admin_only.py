from aiogram.types import Message
from main import server


def admin_only_middleware(func):
    async def wrapper(msg: Message):
        if msg.from_user.id in server.config.admin:
            await func(msg)
        else:
            server.logger.info("Access to admin function denied for id: " + str(msg.from_user.id))
    return wrapper
