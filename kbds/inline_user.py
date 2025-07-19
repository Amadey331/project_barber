from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters.callback_data import CallbackData

from datetime import datetime, timedelta, date, time

from typing import List, Dict, Tuple

from utils.format import format_date_rus











class UserServiceslistCallBack(CallbackData, prefix = "user_services_list"):
    level: int
    service_category: str | None = None
    page: int = 1



class UserAddRecordCallBack(CallbackData, prefix = "add_record_user"):
    level : int
    service_category: str |None = None
    service_id: int | None = None
    barber_id: int|None = None
    name_btn: str | None = None 
    page: int = 1
    date: str | None = None  
    time: str | None = None



class UserViewSlotsCallBack(CallbackData, prefix = "view_slots_user"):
    level : int
    barber_id: int | None = None
    barber_name: str | None = None
    page: int = 1
    date: str | None = None

class UserRememberOkCallback(CallbackData, prefix="remember_ok_user"):
    message_id: int
    chat_id: int
    appointment_id: int
    status: str  # "confirm" или "cancel"

class UserViewRecordsCallback(CallbackData, prefix="user_records"):
    level: int
    page: int = 1
    appointment_id: int | None = None

class UserRateBarberCallback(CallbackData, prefix="rate"):
    barber_id: int
    appointment_id: int
    score: int

class UserRateDeclineCallback(CallbackData, prefix="decline_rating"):
    appointment_id: int

def get_main_inlineBtns_user(

) -> InlineKeyboardMarkup:
    kbds = InlineKeyboardBuilder()

    
    kbds.add(
        InlineKeyboardButton(text="➕ Записаться", callback_data="record_user"),
        InlineKeyboardButton(text="🏠 Список услуг", callback_data="view_service_user")
    )

    
    kbds.add(
        InlineKeyboardButton(text="📋 Мои записи", callback_data="my_records"),
        InlineKeyboardButton(text="📞 Тех. поддержка", url="https://t.me/Kkjhjyfyu")
    )

    
    kbds.add(
        InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")
    )

    return kbds.adjust(2).as_markup()









def get_user_services_category_btns(*, level:int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
            "✂️ Стрижки": "haircut",
            "🧔 Борода и бритьё": "beard",
            "💆‍♂️ Уход за волосами и кожей": "care",
            "🎭 Стайлинг": "styling",
            "🎟 Комплексные услуги": "combo",
            "🔙 Отмена": "cancel_user"
    }

    for text, data in btns.items():
        if text != "🔙 Отмена":
            keyboard.add(InlineKeyboardButton(text=text,
                    callback_data=UserServiceslistCallBack(level=level+1, service_category=data).pack()))      
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                    callback_data="cancel_user"))
    return keyboard.adjust(*sizes).as_markup()




def get_user_services_list_btns(
        *,  
        level: int,
        category: str,  # Должен быть str, а не int
        page: int,
        pagination_btns: dict,
        
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()





    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserServiceslistCallBack(
                    level=level,
                    service_category=category,  # Исправлено
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserServiceslistCallBack(
                    level=level,
                    service_category=category,  # Исправлено
                    page=page - 1
                ).pack()))
            
            
    keyboard.add(InlineKeyboardButton(
        text="🔙 Назад", 
        callback_data=UserServiceslistCallBack(level=0).pack()
    ))
    return keyboard.row(*row).as_markup()












# text то что написанно на кнопке callback_data то что кнопка отправляет это не видит пользователь
def get_callback_btns(
        *,
        btns: dict[str,str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text = text, callback_data = data))

    return keyboard.adjust(*sizes).as_markup()










def get_barbers_list_btns_for_view_slots(
        *,
        level: int,
        barber_id: int,
        barber_name: str,
        page: int,
        pagination_btns: dict,
        sizes: tuple[int] = (2, 1)
):
    kbds = InlineKeyboardBuilder()


    

    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserViewSlotsCallBack(
                    level= level, 
                    barber_id=barber_id,
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserViewSlotsCallBack(
                    level= level,
                    barber_id=barber_id,
                    page=page - 1
                ).pack()))

    
    kbds.add(InlineKeyboardButton(text='Выбрать',
        callback_data=UserViewSlotsCallBack(
            level = level+1 ,
            barber_id= barber_id,
            barber_name= barber_name,
            name_btn="select_barber").pack()))

    kbds.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_user"))
    kbds.adjust(2)
    return kbds.row(*row).as_markup()







def get_service_categoty_for_record(session, level):
    kbds = InlineKeyboardBuilder()
    btns={
            "✂️ Стрижки": "haircut",
            "🧔 Борода и бритьё": "beard",
            "💆‍♂️ Уход за волосами и кожей": "care",
            "🎭 Стайлинг": "styling",
            "🎟 Комплексные услуги": "combo"
            
    }
    row = []
    for name_btn, data_btn in btns.items():
        kbds.button(
            text=name_btn,
            callback_data=UserAddRecordCallBack(level=level+1, service_category=data_btn).pack()
        )
    kbds.add(InlineKeyboardButton(text="Отмена",
    callback_data="cancel_user"))
    kbds.adjust(2)
    return kbds.as_markup()






def get_barbers_list_btns_for_record(
        *,
        level: int,
        service_category:str,
        service_id: int,
        barber_id: int,
        page: int,
        pagination_btns: dict,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()


    

    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserAddRecordCallBack(
                    level= level, 
                    service_id= service_id,
                    barber_id=barber_id,
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserAddRecordCallBack(
                    level= level,
                    barber_id=barber_id,
                    service_id=service_id,
                    page=page - 1
                ).pack()))

    
    keyboard.add(InlineKeyboardButton(text='Выбрать',
        callback_data=UserAddRecordCallBack(
            level = level+1 ,
            service_category=service_category,
            service_id= service_id,
            barber_id= barber_id,
            name_btn="select_barber").pack()))

    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_user"))
    keyboard.adjust(2)
    return keyboard.row(*row).as_markup()






def get_services_list_btns_for_record(
        *,  
        level: int,
        page: int,
        pagination_btns: dict,
        service_category:str,
        service_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()





    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserAddRecordCallBack(
                    level=level,
                    service_category=service_category,  
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=UserAddRecordCallBack(
                    level=level,
                    service_category=service_category,  
                    page=page - 1
                ).pack()))
            
    keyboard.add(InlineKeyboardButton(text="Выбрать",
        callback_data=UserAddRecordCallBack(
            level = level+1,
            service_category= service_category,
            page = 1,
            service_id= service_id,
            name_btn= "select_service"
        ).pack()))

    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_user"))
    
    return keyboard.row(*row).as_markup()






# Генерация клавиатуры на 14 дней.
# Формат данных:  выводится не больше 14 кнопок с датой (пн: 14:02)
def get_select_date_kb_for_record(dates, level, service_category, service_id, barber_id):
    kbds = InlineKeyboardBuilder()

   
    for date_obj in dates:
        display_text = format_date_rus(date_obj)  # В кнопке
        date_str = date_obj.strftime("%d.%m.%Y")  # В callback

        kbds.add(InlineKeyboardButton(
            text=display_text,
            callback_data=UserAddRecordCallBack(
                level=level + 1,
                service_category=service_category,
                service_id=service_id,
                barber_id=barber_id,
                name_btn="select_date",
                page=0,
                date=date_str  # 👈 хранится как 12.05.2025
            ).pack()
        ))
    
    kbds.add(InlineKeyboardButton(  # Назад
        text="🔙 Назад",
        callback_data=UserAddRecordCallBack(
            level=level - 1,
            service_category=service_category,
            service_id=service_id,
            page=1
        ).pack()
    ))
    kbds.adjust(2)
    return kbds.as_markup()







def get_select_time_kb_for_record(slots, level, service_category, service_id, barber_id, date):
    keyboard = InlineKeyboardBuilder()

    for slot_time in slots:
        text = slot_time.strftime("%H:%M")
        
        time_str = slot_time.strftime("%H_%M")

        keyboard.add(
            InlineKeyboardButton(
                text=text,
                callback_data=UserAddRecordCallBack(
                    level=level + 1,
                    service_category=service_category,
                    service_id=service_id,
                    barber_id=barber_id,
                    date=date,
                    name_btn="select_time",
                    page=0,
                    time=time_str
                ).pack()
            )
        )

    keyboard.adjust(3)
    keyboard.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=UserAddRecordCallBack(
                level=level - 1,
                service_category=service_category,
                service_id=service_id,
                barber_id=barber_id,
                page=1,
                date=date
            ).pack()
        )
    )

    return keyboard.as_markup()









def get_remember_ok_kb(message_id, chat_id, appointment_id):
    kbds = InlineKeyboardBuilder()
    kbds.add(InlineKeyboardButton(
        text="Я приду 🟢",
        callback_data=UserRememberOkCallback(
            message_id=message_id,
            chat_id=chat_id,
            appointment_id=appointment_id,
            status="confirm"
        ).pack()
    ))
    kbds.add(InlineKeyboardButton(
        text="Я не приду 🔴",
        callback_data=UserRememberOkCallback(
            message_id=message_id,
            chat_id=chat_id,
            appointment_id=appointment_id,
            status="cancel"
        ).pack()
    ))
    kbds.adjust(2)
    return kbds.as_markup()









def get_user_records_btns(level, page, pagination_btns: dict, appointment_id: int):
    kb = InlineKeyboardBuilder()

    # 🔝 Первая строка — пагинация
    row_top = []
    for text, direction in pagination_btns.items():
        next_page = page + 1 if direction == "next" else page - 1
        row_top.append(InlineKeyboardButton(
            text=text,
            callback_data=UserViewRecordsCallback(
                level=level,
                page=next_page,
                appointment_id=appointment_id
            ).pack()
        ))
    kb.row(*row_top)

    # 🔚 Одна строка — отмена и меню
    kb.row(
        InlineKeyboardButton(
            text="❌ Отменить запись",
            callback_data=UserViewRecordsCallback(
                level=level + 1,
                page=1,
                appointment_id=appointment_id
            ).pack()
        ),
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="cancel_user"
        )
    )

    return kb.as_markup()



def get_rating_inline_kb(barber_id: int, appointment_id: int):
    buttons = [
        [InlineKeyboardButton(text=f"⭐️ {i}", callback_data=UserRateBarberCallback(barber_id=barber_id, appointment_id=appointment_id, score=i).pack())]
        for i in range(1, 6)
    ]
    # Добавляем кнопку "Отказаться"
    buttons.append([
        InlineKeyboardButton(text="❌ Отказаться", callback_data=UserRateDeclineCallback(appointment_id=appointment_id).pack())
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)




def get_confirm_record_kb(
    level: int,
    service_category: str,
    service_id: int,
    barber_id: int,
    date: str,
    time: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # ➕ Верхний ряд: Подтвердить и Назад
    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=UserAddRecordCallBack(
                level=level + 1,
                service_category=service_category,
                service_id=service_id,
                barber_id=barber_id,
                date=date,
                time=time,
                name_btn="confirm"
            ).pack()
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=UserAddRecordCallBack(
                level=level - 1,
                service_category=service_category,
                service_id=service_id,
                barber_id=barber_id,
                date=date,
                time=time
            ).pack()
        )
    )

    # ➕ Отдельным рядом: Отмена
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_user"
        )
    )

    return builder.as_markup()