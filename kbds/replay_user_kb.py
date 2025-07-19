from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,ReplyKeyboardRemove,KeyboardButtonPollType

from aiogram.utils.keyboard import ReplyKeyboardBuilder



def get_send_number_kb_user() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )