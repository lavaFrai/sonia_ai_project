import asyncio
import random

import openai
from aiogram import Router, F
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto

from keyboards.cancel_keyboard import get_cancel_keyboard
from main import server
from models.user import User
from states import Global
from utils.filter import CallbackFilter

router = Router()


@router.callback_query(CallbackFilter(data='non-context-action.generate-image'), StateFilter(None))
async def on_generate_started(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await cb.answer()
    await cb.message.answer(user.get_string("non-context-action.generate-image.prompt_ask"), reply_markup=get_cancel_keyboard(user))
    await state.set_state(Global.image_generation)


async def generate_image_repeating(prompt, use_dall_e_3, msg):
    try:
        if use_dall_e_3:
            response = openai.Image.acreate(
                prompt=prompt,
                n=1,
                size='1024x1024',
                model="dall-e-3"
            )
            response = await server.await_with_typing_status(response, msg.chat.id, ChatAction.UPLOAD_PHOTO)
            media = [InputMediaPhoto(media=response['data'][i]['url']) for i in range(1)]
            return media
        else:
            response = openai.Image.acreate(
                prompt=prompt,
                n=4,
                size='1024x1024',
                model="dall-e-2"
            )
            response = await server.await_with_typing_status(response, msg.chat.id, ChatAction.UPLOAD_PHOTO)
            media = [InputMediaPhoto(media=response['data'][i]['url']) for i in range(4)]
            return media
    except openai.error.RateLimitError:
        await server.await_with_typing_status(asyncio.sleep(random.randint(10, 20)), msg.chat.id, ChatAction.UPLOAD_PHOTO)
        return await generate_image_repeating(prompt, use_dall_e_3, msg)


@router.message(Global.image_generation, F.text)
async def on_generate(msg: Message, state: FSMContext, user: User):
    server.metrics.images_generated += 1

    use_dall_e_3 = user.get_cache_field("image_model", "dall-e-3") == "dall-e-3"

    user = User.get_by_message(msg)

    if msg.text is None:
        await msg.answer(user.get_string("non-context-action.generate-image.invalid-prompt-type"), reply_markup=get_cancel_keyboard(user))
        return

    await state.set_state(Global.busy)
    new_msg = await msg.answer(user.get_string("non-context-action.generate-image.in-process"))

    try:
        if use_dall_e_3:
            response = openai.Image.acreate(
                prompt=msg.text,
                n=1,
                size='1024x1024',
                model="dall-e-3"
            )
            response = await server.await_with_typing_status(response, msg.chat.id, ChatAction.UPLOAD_PHOTO)
            media = [InputMediaPhoto(media=response['data'][i]['url']) for i in range(1)]
        else:
            response = openai.Image.acreate(
                prompt=msg.text,
                n=4,
                size='1024x1024',
                model="dall-e-2"
            )
            response = await server.await_with_typing_status(response, msg.chat.id, ChatAction.UPLOAD_PHOTO)
            media = [InputMediaPhoto(media=response['data'][i]['url']) for i in range(4)]
        # image_url = response['data'][0]['url']
    except openai.error.InvalidRequestError:
        await msg.reply(user.get_string("non-context-action.generate-image.invalid-prompt"), reply_markup=get_cancel_keyboard(user))
        await new_msg.delete()
        await state.set_state(Global.image_generation)
        return
    except openai.error.RateLimitError:
        await msg.answer(user.get_string('non-context-action.generate-image.rate-limit'))
        try:
            media = await generate_image_repeating(msg.text, use_dall_e_3, msg)
        except openai.error.InvalidRequestError:
            await msg.reply(user.get_string("non-context-action.generate-image.invalid-prompt"), reply_markup=get_cancel_keyboard(user))
            await new_msg.delete()
            await state.set_state(Global.image_generation)
            return

    await msg.reply_media_group(media=media)
    await new_msg.delete()
    await server.reset_state_message(msg)
    await state.clear()


@router.message(Command("image_model"), StateFilter(None))
async def on_generate(msg: Message, state: FSMContext, user: User):
    model = user.get_cache_field("image_model", "dall-e-3")
    if model == "dall-e-3":
        user.set_cache_field("image_model", "dall-e-2")
        await msg.reply(user.get_string('image-model.dall-e-2'), parse_mode=None)
    if model == "dall-e-2":
        user.set_cache_field("image_model", "dall-e-3")
        await msg.reply(user.get_string('image-model.dall-e-3'), parse_mode=None)
