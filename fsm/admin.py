from aiogram.fsm.state import State, StatesGroup




# Для добавления записи
class AdminAddRecordFSM(StatesGroup):
    waiting_for_client_name = State()
    waiting_for_client_phone = State()


# для удаления записи

class AdminDeleteRecordFSM(StatesGroup):
    appointment_id = State()