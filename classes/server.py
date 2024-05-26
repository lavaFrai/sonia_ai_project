import asyncio
import logging
import os.path
import uuid
from pathlib import Path
from urllib.parse import urlparse

import PIL.Image
import aiogram
import openai as openai
from aiogram import Dispatcher, Router
from aiogram.enums import ParseMode, ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, File, FSInputFile
from peewee import SqliteDatabase, PostgresqlDatabase, Database
from playhouse.cockroachdb import CockroachDatabase

from api.MetricsServer import MetricsServer
from classes.commands import CommandsRegistrator
from classes.config import Config
from handlers import handlers_names
from middlewares.database_check_middleware import DatabaseCheckMiddleware
from utils.i18n import I18n
from middlewares.album_middleware import MediaGroupMiddleware
from utils.singleton import Singleton
import utils.gemini.client as gemini


class Server(metaclass=Singleton):
    def __init__(self):
        self.db: Database = None
        self.logger = logging.getLogger(__name__)
        self.logger.info("initializing server")
        self.logger.debug(self)
        self.i18n = I18n()

        self.config = Config()

        self.bot = aiogram.Bot(self.config.telegram_token, parse_mode=ParseMode.MARKDOWN)
        self.metrics = MetricsServer()

        self.dispatcher = None

    async def run(self):
        await self.reconnect_db()
        from utils.aiogram_storage import SQLiteStorage
        self.dispatcher = Dispatcher(storage=SQLiteStorage())

        openai.api_key = self.config.openai_token
        gemini.api_key = self.config.gemini_token
        gemini.base_url = self.config.gemini_base_url
        gemini.proxy = self.config.gemini_proxy

        from middlewares.UnhandledErrorMiddleware import UnhandledErrorMiddleware
        from middlewares.MessagesCounterMiddleware import MessagesCounterMiddleware
        from middlewares.CallbacksCounterMiddleware import CallbacksCounterMiddleware
        from middlewares.UserLoaderMiddleware import UserLoaderMiddleware

        for handler in handlers_names:
            self.logger.debug("Including router " + handler)
            router: Router = __import__('handlers.' + handler, fromlist=['router']).router

            if not self.config.debug:
                router.message.middleware(UnhandledErrorMiddleware())
                router.callback_query.middleware(UnhandledErrorMiddleware())

            router.message.middleware(MessagesCounterMiddleware())
            router.message.middleware(MediaGroupMiddleware())
            router.message.middleware(DatabaseCheckMiddleware())
            router.callback_query.outer_middleware(DatabaseCheckMiddleware())
            router.callback_query.outer_middleware(CallbacksCounterMiddleware())

            router.message.middleware(UserLoaderMiddleware())
            router.callback_query.middleware(UserLoaderMiddleware())

            self.dispatcher.include_router(router)

        self.logger.debug("Registering commands")
        await CommandsRegistrator().update(self.bot)

        dispatcher_task = asyncio.create_task(self.dispatcher.start_polling(self.bot))
        metrics_task = asyncio.create_task(self.metrics.run())

        await asyncio.wait(
            [dispatcher_task, metrics_task],
            return_when=asyncio.FIRST_EXCEPTION
        )

    async def reconnect_db(self):
        if self.db != None:
            self.db.close()
            self.db.connect()
            return

        if self.config.postgresql.use:
            url = urlparse(self.config.postgresql.url)
            self.db = PostgresqlDatabase(
                self.config.postgresql.url
            )
            self.logger.debug("Using postgresql db")
        else:
            self.logger.warning("Using deprecated sqlite db")
            self.db = SqliteDatabase('db.sqlite')

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
            return f"<String undefined:{name}@{locale}>"
        except FileNotFoundError:
            self.logger.error(f"Failed i18n file loading name: {name} locale: {locale}")
            return f"<Locale undefined:{name}@{locale}>"

    @staticmethod
    async def reset_state_message(msg: Message):
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

    @staticmethod
    async def on_error(error):
        print("ada", error)

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

    async def send_string_as_file(self, string: str, chat_id: int, filename=None):
        file = await self.create_file()
        with open(file, 'wb') as f:
            f.write(str(string).encode('utf8'))
        await self.bot.send_document(chat_id, FSInputFile(file, filename))

    async def panic(self, traceback, exception: Exception, data: dict = None, handler=None, event=None):
        case = uuid.uuid1().hex[:10]

        error = f"Unhandled exception case `{case}`\n" \
                f"---\n" \
                f"Exception: `{type(exception).__name__} {exception.args}`\n" \
                f"State: `{data['raw_state']}`\n"\
                f"User: [{data['event_from_user'].id}](tg://user?id={data['event_from_user'].id})\n"\
                f"Event: `{type(event).__name__}`\n"

        await self.bot.send_message(self.config.logs_channel, error)
        await self.send_string_as_file(str(traceback), self.config.logs_channel, f'traceback_{case}.txt')

        await data['state'].clear()

        from models.user import User
        user, _ = User.get_or_create(id=data['event_from_user'].id)
        from keyboards.non_context_action import get_non_context_action
        await self.bot.send_message(data['event_chat'].id, user.get_string('panic').replace('%case_id%', str(case))
                                    .replace('%error_code%', type(exception).__name__),
                                    reply_markup=await get_non_context_action(user))
