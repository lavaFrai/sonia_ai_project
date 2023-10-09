from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter

from keyboards.cancel_keyboard import get_cancel_keyboard
from models.user import User
from states import Global

from main import server
from utils.ai_tools.image_extender import ImageExtender
from utils.file_data import FileData
from utils.filter import CallbackFilter

router = Router()


@router.callback_query(CallbackFilter(data='non-context-action.extend-image'), StateFilter(None))
async def on_extend_started(cb: CallbackQuery, state: FSMContext):
    user = User.get_by_callback(cb)

    await cb.answer()
    await cb.message.answer(user.get_string("non-context-action.extend-image.prompt_ask"), reply_markup=get_cancel_keyboard(user))
    await state.set_state(Global.image_extending)


@router.message(Global.image_extending, F.photo)
async def on_generate(msg: Message, state: FSMContext):
    user = User.get_by_message(msg)

    await state.set_state(Global.busy)
    new_msg = await msg.answer(user.get_string("non-context-action.extend-image.in-process"))

    source_file = await server.download_file_by_id(FileData(msg.photo[-1]).get_data(), 'png')
    prepared_file = await server.create_file('PNG')
    mask_file = await server.create_file('PNG')

    image_url = ImageExtender.extend_image(source_file, prepared_file, mask_file)
    image_url = await server.await_with_typing_status(image_url, msg.chat.id, ChatAction.UPLOAD_PHOTO)

    await server.delete_file(source_file)
    await server.delete_file(prepared_file)
    await server.delete_file(mask_file)

    await msg.answer_photo(photo=image_url)
    await new_msg.delete()
    await server.reset_state_message(msg)
    await state.clear()
