import asyncio
import logging
import os.path
import uuid
from pathlib import Path

import openai as openai
import PIL.Image
from aiogram import Dispatcher
from aiogram.enums import ParseMode, ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, Downloadable, File
from peewee import SqliteDatabase

from classes.config import Config
import aiogram
from handlers import handlers_names
from utils.i18n import I18n
from utils.singleton import Singleton


class Server(metaclass=Singleton):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("initializing server")
        self.logger.debug(self)
        self.i18n = I18n()
        self.db = SqliteDatabase('db.sqlite')

        self.config = Config()
        self.bot = aiogram.Bot(self.config.telegram_token, parse_mode=ParseMode.MARKDOWN)

        self.dispatcher = None

    async def run(self):
        from utils.aiogram_storage import SQLiteStorage
        self.dispatcher = Dispatcher(storage=SQLiteStorage())

        openai.api_key = self.config.openai_token

        for handler in handlers_names:
            self.logger.debug("Including router " + handler)
            self.dispatcher.include_router(__import__('handlers.' + handler, fromlist=['router']).router)

        await self.dispatcher.start_polling(self.bot)

    def get_logger(self):
        return self.logger

    def get_string(self, name, locale='default-DEFAULT'):
        try:
            if locale == 'default-DEFAULT':
                return self.i18n.get_string(name)
            else:
                return I18n(locale).get_string(name)
        except KeyError:
            self.logger.error(f"Failed i18n string loading name: {name} locale: {locale}")
            return "<String undefined>"
        except FileNotFoundError:
            self.logger.error(f"Failed i18n file loading name: {name} locale: {locale}")
            return "<Locale undefined>"

    async def reset_state_message(self, msg: Message):
        from models.user import User
        user = User.get_by_message(msg)
        from keyboards.non_context_action import get_non_context_action
        await msg.answer(user.get_string("state-reset"), reply_markup=await get_non_context_action(user))

    async def reset_state_message_no_reply(self, chat, user):
        from keyboards.non_context_action import get_non_context_action
        await self.bot.send_message(chat, user.get_string("state-reset"), reply_markup=await get_non_context_action(user))

    @staticmethod
    async def create_file(ex=''):
        uid = uuid.uuid4().hex
        path = f"downloads/{uid}.{ex}"
        return path

    async def download_file_by_id(self, file_data, ex='') -> str:
        file = File(file_id=file_data.split(":")[0], file_unique_id=file_data.split(":")[1])
        Path("downloads").mkdir(parents=True, exist_ok=True)

        uid = uuid.uuid4().hex
        path = f"downloads/{uid}.{ex}"
        await self.bot.download(file, path)

        if ex.lower() == 'png':
            im = PIL.Image.open(path)

            im.save(path, "PNG")
            # await self.delete_file(path)
        return path

    @staticmethod
    async def delete_file(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    async def get_user_by_message(self, msg: Message):
        from models.user import User
        user, created = User.get_or_create(id=msg.from_user.id)
        if created:
            user = User.get(id=msg.from_user.id)
        return user

    async def delete_reply_markup_if_possible(self, chat_id, message_id):
        try:
            if message_id != 0:
                await self.bot.edit_message_reply_markup(chat_id=chat_id,
                                                         message_id=message_id, reply_markup=None)
        except TelegramBadRequest:
            pass

    async def await_with_typing_status(self, coroutine, chat_id, status=ChatAction.TYPING):
        async def send_typing():
            while True:
                await self.bot.send_chat_action(chat_id, status)
                await asyncio.sleep(1)

        tasks = [send_typing(), coroutine]

        new_message, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        pending.pop().cancel()
        return new_message.pop().result()
