from aiogram.fsm.state import State, StatesGroup

class UserRecordStates(StatesGroup):
    waiting_for_phone = State()