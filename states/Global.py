from aiogram.fsm.state import StatesGroup, State


class Global(StatesGroup):
    busy = State()
    image_generation = State()
    image_editing = State()
    image_extending = State()
