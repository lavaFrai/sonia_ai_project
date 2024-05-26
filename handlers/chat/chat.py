from typing import List

import PyPDF2
import docx2txt
from aiogram import Router
from aiogram.enums import ChatAction, ContentType, ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.chat_dialog_keyboards import get_dialog_stop_keyboard
from main import server
from models.chat_dialog import ChatDialog
from models.user import User
from states import Global
from utils.answer_safe import answer_safe
from utils.file_data import FileData
from utils.filter import CallbackFilter
from utils.gemini.chat_client import ChatClient
from utils.gemini.client import PayloadToLargeException

router = Router()


async def start_dialog(user_id) -> int:
    dialog = ChatDialog.create(user_id=user_id)
    return dialog.id


@router.message(Command("dialog"), StateFilter(None))
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.set_state(Global.dialog)

    dialog_id = await start_dialog(msg.from_user.id)

    await state.set_data({"id": dialog_id})
    await msg.reply(user.get_string("dialog-started"),
                    parse_mode=None)  #, reply_markup=await get_dialog_stop_keyboard(user))


@router.callback_query(CallbackFilter(data='dialog.start'), StateFilter(None))
async def on_start_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await state.set_state(Global.dialog)
    dialog_id = await start_dialog(cb.from_user.id)

    await cb.message.answer(user.get_string("dialog-started"),
                            parse_mode=None)  # , reply_markup=await get_dialog_stop_keyboard(user))

    await state.set_data({"id": dialog_id})
    await cb.answer()


@router.message(Command("stop_dialog"), Global.dialog)
async def on_command(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.clear()
    await msg.reply(user.get_string("dialog-stopped"))


@router.callback_query(CallbackFilter(data='dialog.stop'), Global.dialog)
async def on_stop_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    dialog_id = (await state.get_data())['id']
    dialog = ChatDialog.get(id=dialog_id)

    await server.delete_reply_markup_if_possible(cb.message.chat.id, dialog.last_bot_message)

    await state.clear()
    await cb.answer()
    await cb.message.reply(
        user.get_string("dialog-stopped"))  # , reply_markup=await get_dialog_resume_keyboard(dialog_id, user))
    await server.reset_state_message_no_reply(cb.message.chat.id, user)


@router.callback_query(CallbackFilter(starts_with='dialog.resume'), StateFilter(None))
async def on_resume_dialog(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await server.delete_reply_markup_if_possible(cb.message.chat.id, cb.message.message_id)
    await state.set_state(Global.dialog)
    dialog_id = int(cb.data.split('.')[2])
    dialog = ChatDialog.get(id=dialog_id)
    await state.set_data({'id': str(dialog_id)})
    created_message = await cb.message.reply(
        user.get_string('dialog-resumed'))  # , reply_markup=await get_dialog_stop_keyboard(user))
    dialog.last_bot_message = created_message.message_id
    dialog.save()
    await cb.answer()


async def get_system_message():
    return open("conf/system-prompt.txt", "r", encoding='utf8').read()


allowed_mime = [
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/heic",
    "image/heif",
    "audio/wav",
    "audio/mp3",
    "audio/aiff",
    "audio/aac",
    "audio/ogg",
    "audio/flac",
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
    "application/x-javascript",
    "text/x-typescript",
    "text/csv",
    "text/markdown",
    "application/json",
    "text/xml",
    "application/rtf",
    "text/rtf",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


@router.message(Global.dialog, lambda x: x)
async def on_new_message(msg: Message, state: FSMContext, album: List[Message], user: User):
    server.metrics.chat_voice_messages += 1

    await state.set_state(Global.busy)
    await server.bot.send_chat_action(msg.chat.id, ChatAction.TYPING)
    dialog_id = (await state.get_data())['id']

    last_message = ChatDialog.select(ChatDialog.last_bot_message).where(ChatDialog.id == dialog_id)[0].last_bot_message
    if last_message is not None:
        try:
            await server.bot.edit_message_reply_markup(chat_id=msg.chat.id, message_id=last_message, reply_markup=None)
        except Exception:
            pass

    messages = []

    chat = ChatClient(
        system_instruction=await get_system_message(),
        tools=[]
    )

    for message in album:
        if message.caption:
            messages.append(chat.build_text_message(message.caption, "user"))

        if message.content_type == ContentType.TEXT:
            messages.append(chat.build_text_message(message.text, "user"))

        elif message.content_type == ContentType.VOICE:
            voice_file = await server.download_file_by_id(FileData(message.voice).get_data(), "ogg")
            with open(voice_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "audio/ogg", "user"))
            await server.delete_file(voice_file)

        elif message.content_type == ContentType.AUDIO:
            voice_file = await server.download_file_by_id(FileData(message.audio).get_data(), "mp3")
            with open(voice_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "audio/mp3", "user"))
            await server.delete_file(voice_file)

        elif message.content_type == ContentType.PHOTO:
            photo_file = await server.download_file_by_id(FileData(message.photo[-1]).get_data(), "jpg")
            with open(photo_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), "image/jpeg", "user"))
            await server.delete_file(photo_file)

        elif message.content_type == ContentType.DOCUMENT:
            mime_type = message.document.mime_type
            if mime_type is None:
                await message.reply(
                    user.get_string("unsupported-media-type").replace("%type%", message.document.mime_type))
                await state.set_state(Global.dialog)
                return
            if mime_type not in allowed_mime:
                await message.reply(
                    user.get_string("unsupported-media-type").replace("%type%", message.document.mime_type))
                await state.set_state(Global.dialog)
                return

            document_file = await server.download_file_by_id(FileData(message.document).get_data(),
                                                             message.document.file_name)

            if mime_type == "application/pdf":
                pdf_file = open(document_file, "rb")
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                messages.append(chat.build_text_message(text, "user"))
                pdf_file.close()

                new_file = await server.create_file("txt")
                with open(new_file, "w", encoding='utf8') as f:
                    f.write(text)
                await server.delete_file(document_file)
                document_file = new_file
                mime_type = "text/plain"

            if mime_type == "application/msword" or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                document_file = await server.download_file_by_id(FileData(message.document).get_data(), "docx")
                new_file = await server.create_file("txt")
                with open(document_file, "rb") as input_f:
                    with open(new_file, "w", encoding='utf8') as output_f:
                        doc = docx2txt.process(input_f)
                        output_f.write(doc)

                await server.delete_file(document_file)
                document_file = new_file
                mime_type = "text/plain"

            with open(document_file, "rb") as f:
                messages.append(chat.build_file_message(f.read(), mime_type, "user"))
            # await server.delete_file(document_file)

        else:
            await message.reply(user.get_string("unsupported-media-type").replace("%type%", message.content_type))
            await state.set_state(Global.dialog)
            return

    await ChatDialog.add_messages(dialog_id, messages)
    history = await ChatDialog.get_dialog_history(dialog_id)
    chat.set_history(history)

    try:
        response = await chat.request_response()
        await ChatDialog.add_messages(dialog_id, chat.get_new_messages())
    except PayloadToLargeException:
        await msg.reply(user.get_string("dialog-too-long"))
        await state.clear()
        return
    except Exception as e:
        await msg.reply(user.get_string("dialog-error"))
        await state.clear()
        raise e

    await ChatDialog.save_dialog_history(dialog_id, chat.get_history())

    msg = await answer_safe(msg, response.replace("* **", "**").replace("**", "*"),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=await get_dialog_stop_keyboard(user)
                            )

    ChatDialog.update(last_bot_message=msg.message_id).where(ChatDialog.id == dialog_id).execute()

    await state.set_state(Global.dialog)
