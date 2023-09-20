import openai
import tiktoken as tiktoken
from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.non_context_action import get_non_context_voice_keyboard, get_non_context_text_keyboard
from main import server
from states import Global
from utils.file_data import FileData

router = Router()


@router.message(lambda x: x.content_type == ContentType.TEXT, StateFilter(None))
async def on_non_context_text(msg: Message, state: FSMContext):
    await msg.reply(server.get_string("non-context-action.non_context_text.action-select"),
                    reply_markup=await get_non_context_text_keyboard(msg.text))


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string.
        For text-davinci-003 encoding is p50k_base, for newest cl100k_base"""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


@router.callback_query(F.data.startswith("non_context_text.continue"), StateFilter(None))
async def on_non_context_text_continue(cb: CallbackQuery, state: FSMContext):
    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(server.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        try:
            message_length_in_tokens = num_tokens_from_string(source_message.text, "p50k_base")
            # await source_message.reply(text=str(message_length_in_tokens))
            completion = await openai.Completion.acreate(
                model="text-davinci-003",
                prompt=source_message.text,
                max_tokens=4097 - message_length_in_tokens,
                temperature=0.3
            )
            text = source_message.text + completion["choices"][0]["text"]
            new_msg = await source_message.reply(text=text)
            # await new_msg.reply(text=server.get_string("non-context-action.non_context_text.additional-action"),
            #                     reply_markup=await get_non_context_text_keyboard(text))
        finally:
            await state.clear()
            await cb.answer()


@router.callback_query(F.data.startswith("non_context_text.reduce"), StateFilter(None))
async def on_non_context_text_reduce(cb: CallbackQuery, state: FSMContext):
    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(server.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        try:
            # message_length_in_tokens = num_tokens_from_string(source_message.text, "p50k_base")
            new_msg = await source_message.reply(text=server.get_string("generation-in-progress"))

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You should shorten the texts that are sent to you, leaving only the most important in them."},
                    {"role": "user", "content": source_message.text}
                ]
            )
            text = response["choices"][0]["message"]["content"]
            await new_msg.delete()
            await source_message.reply(text=text)
        finally:
            await state.clear()
            await cb.answer()


@router.callback_query(F.data.startswith("non_context_text.reduce"), StateFilter(None))
async def on_non_context_text_reduce(cb: CallbackQuery, state: FSMContext):
    source_message = cb.message.reply_to_message
    if source_message is None:
        await cb.answer()
        await cb.message.answer(server.get_string("non-context-action.non_context_voice.message-error"))
        return
    else:
        await state.set_state(Global.busy)
        try:
            # message_length_in_tokens = num_tokens_from_string(source_message.text, "p50k_base")
            new_msg = await source_message.reply(text=server.get_string("generation-in-progress"))

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You should shorten the texts that are sent to you, leaving only the most important in them."},
                    {"role": "user", "content": source_message.text}
                ]
            )
            text = response["choices"][0]["message"]["content"]
            await new_msg.delete()
            await source_message.reply(text=text)
        finally:
            await state.clear()
            await cb.answer()
