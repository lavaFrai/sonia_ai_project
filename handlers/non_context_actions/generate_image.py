import openai
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

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


@router.message(Global.image_generation, F.text)
async def on_generate(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    if msg.text is None:
        await msg.answer(user.get_string("non-context-action.generate-image.invalid-prompt-type"), reply_markup=get_cancel_keyboard(user))
        return

    await state.set_state(Global.busy)
    new_msg = await msg.answer(user.get_string("non-context-action.generate-image.in-process"))

    try:
        response = await openai.Image.acreate(
            prompt=msg.text,
            n=1,
            size='512x512'
        )
        image_url = response['data'][0]['url']
    except openai.error.InvalidRequestError:
        await msg.reply(user.get_string("non-context-action.generate-image.invalid-prompt"), reply_markup=get_cancel_keyboard(user))
        await new_msg.delete()
        await state.set_state(Global.image_generation)
        return

    await msg.reply_photo(photo=image_url)
    await new_msg.delete()
    await server.reset_state_message(msg)
    await state.clear()
