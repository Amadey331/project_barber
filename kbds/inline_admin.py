from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters.callback_data import CallbackData

from datetime import datetime, timedelta, date, time

from typing import List, Dict, Tuple

from utils.format import format_date_rus











class AdminServicesListCallBack(CallbackData, prefix = "admin_services_list"):
    level: int
    service_category: str | None = None
    page: int = 1
    service_id : int | None = None
    name_btn: str | None = None



class AdminBarbersListCallback(CallbackData, prefix = "admin_barbers_list"):
    page: int = 1
    barber_id: int|None = None
    name_btn: str | None = None



# Для добовления админом записей
class AdminAddRecordCallBack(CallbackData, prefix = "add_record_admin"):
    level : int
    service_category: str |None = None
    service_id: int | None = None
    barber_id: int|None = None
    name_btn: str | None = None 
    page: int = 1
    date: str | None = None  
    time: str | None = None

class AdminViewSlotsCallBack(CallbackData, prefix = "view_slots_admin"):
    level : int
    barber_id: int | None = None
    barber_name: str | None = None
    page: int = 1
    date: str | None = None
    


def get_main_inlineBtns_admin():

    kbds = InlineKeyboardBuilder()
    kbds.add(InlineKeyboardButton(text="➕ Записать" , callback_data="add_recod_admin"))    
    kbds.add(InlineKeyboardButton(text="📝 Записи" , callback_data="view_slots_admin"))    
    kbds.add(InlineKeyboardButton(text="✏️ Редактировать" , callback_data="edit"))
    kbds.add(InlineKeyboardButton(text="📜 Журнал", callback_data="list_admin"))
    kbds.add(InlineKeyboardButton(text="🔧 Админы" , callback_data="edit_admin_list"))
    kbds.add(InlineKeyboardButton(text="🏠 Выйти" , callback_data="exit_admin"))
    kbds.add(InlineKeyboardButton(text="📕 Руководство" , callback_data="anagement"))    
    
    return kbds.adjust(2).as_markup()





def get_weekday_selection_kb_admin():
    days = {
        "Пн": 0,
        "Вт": 1,
        "Ср": 2,
        "Чт": 3,
        "Пт": 4,
        "Сб": 5,
        "Вс": 6
    }

    kb = InlineKeyboardBuilder()

    for name, value in days.items():
        kb.add(InlineKeyboardButton(text=name, callback_data=f"day_{value}"))

    
    kb.add(InlineKeyboardButton(text="✅ Готово", callback_data="weekday_selection_done"))

    
    kb.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    
    return kb.adjust(3).as_markup()








# Для получения кнопок для списка барберов
def get_barbers_list_btns_admin(
        *,
        page: int,
        pagination_btns: dict,
        barber_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Удалить',
        callback_data=AdminBarbersListCallback( barber_id = barber_id, name_btn = "delete").pack()))

    keyboard.add(InlineKeyboardButton(text='Редактировать',
        callback_data=AdminBarbersListCallback(barber_id = barber_id, name_btn = "edit").pack()))
    
    keyboard.adjust(*sizes)
    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminBarbersListCallback(
                    
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminBarbersListCallback(
 
                    page=page - 1
                ).pack()))
            
    
    keyboard.add(InlineKeyboardButton(text='Удалить услугу',
        callback_data=AdminBarbersListCallback(barber_id = barber_id, name_btn = "unlink_service").pack()))

    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    keyboard.adjust(2)
    return keyboard.row(*row).as_markup()





def get_barbers_list_btns_for_record_admin(
        *,
        page: int,
        pagination_btns: dict,
        barber_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Записать',
        callback_data=AdminAddRecordCallBack( barber_id = barber_id, name_btn = "record").pack()))

    keyboard.add(InlineKeyboardButton(text='Слоты',
        callback_data=AdminAddRecordCallBack(barber_id = barber_id, name_btn = "slots").pack()))
    
    keyboard.adjust(*sizes)
    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminAddRecordCallBack(
                    
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminAddRecordCallBack(
 
                    page=page - 1
                ).pack()))
            
            
    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    return keyboard.row(*row).as_markup()





def generate_time_slot_btns_admin(
    selected_date: date,
    schedule: Dict[int, Tuple[time, time]],
    appointments: List[Tuple[time, time]],
    service_duration_minutes: int
) -> InlineKeyboardMarkup:
    weekday = selected_date.weekday()

    if weekday not in schedule:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="⛔ Нет работы в этот день", callback_data="back_to_dates"))
        return kb.as_markup()

    start_time, end_time = schedule[weekday]
    slots = []

    current = datetime.combine(selected_date, start_time)
    end = datetime.combine(selected_date, end_time)

    step = timedelta(minutes=30)
    service_delta = timedelta(minutes=service_duration_minutes)

    while current + service_delta <= end:
        slot_start = current.time()
        slot_end = (current + service_delta).time()

        overlap = False
        for busy_start, busy_end in appointments:
            if busy_start < slot_end and busy_end > slot_start:
                overlap = True
                break

        if not overlap:
            slots.append(slot_start.strftime("%H:%M"))

        current += step

    kb = InlineKeyboardBuilder()
    for t in slots:
        kb.add(InlineKeyboardButton(text=t, callback_data=f"select_time:{t}"))

    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_dates"))
    return kb.adjust(4).as_markup()







def generate_date_buttons(available_dates: List[date]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for d in available_dates:
        kb.add(InlineKeyboardButton(
            text=d.strftime("%d.%m"),
            callback_data=f"select_date:{d.isoformat()}"
        ))
    kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_barbers"))
    return kb.adjust(4).as_markup()






def get_admin_services_list_btns(
        *,  
        level: int,
        category: str,  # Должен быть str, а не int
        page: int,
        pagination_btns: dict,
        service_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Удалить',
        callback_data=AdminServicesListCallBack(level=level, service_category=category, service_id=service_id, name_btn = "delete").pack()))

    keyboard.add(InlineKeyboardButton(text='Редактировать',
        callback_data=AdminServicesListCallBack(level=level, service_category=category, service_id=service_id, name_btn = "edit").pack()))



    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminServicesListCallBack(
                    level=level,
                    service_category=category,  
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminServicesListCallBack(
                    level=level,
                    service_category=category,  
                    page=page - 1
                ).pack()))
            
    keyboard.add(InlineKeyboardButton(
    text='➕ Связать барбера',
    callback_data=AdminServicesListCallBack(
        level=level,
        service_category=category,
        service_id=service_id,
        name_btn="link_barber"
    ).pack()
))
    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    keyboard.adjust(2)
    return keyboard.row(*row).as_markup()








def get_admin_services_category_btns(*, level:int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
            "✂️ Стрижки": "haircut",
            "🧔 Борода и бритьё": "beard",
            "💆‍♂️ Уход за волосами и кожей": "care",
            "🎭 Стайлинг": "styling",
            "🎟 Комплексные услуги": "combo",
            "🔙 Отмена": "cancel_admin"
    }

    for text, data in btns.items():
        if text != "🔙 Отмена":
            keyboard.add(InlineKeyboardButton(text=text,
                    callback_data=AdminServicesListCallBack(level=level+1, service_category=data).pack()))      
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                    callback_data="cancel_admin"))
    return keyboard.adjust(*sizes).as_markup()







# Инлайн кнопки при выборе что хочет сделать админ при редактировании барберов
def get_barbers_list_what_do_inline():
    barbers_list_what_do = InlineKeyboardBuilder()
    
    barbers_list_what_do.add(InlineKeyboardButton(text="➕ Добавить",callback_data = "add_barber" ))
    barbers_list_what_do.add(InlineKeyboardButton(text="📜 Список",callback_data = AdminBarbersListCallback().pack() ))
    barbers_list_what_do.add(InlineKeyboardButton(text="🔙 Назад",callback_data = "cancel_admin" ))
    
    return barbers_list_what_do.adjust(2).as_markup()
# ...................................................................................................................................................................
# ...................................................................................................................................................................
# ...................................................................................................................................................................










# функции для добовления админом записей

# ...................................................................................................................................................................
# ...................................................................................................................................................................
# ...................................................................................................................................................................
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
            callback_data=AdminAddRecordCallBack(level=level+1, service_category=data_btn).pack()
        )
    kbds.add(InlineKeyboardButton(text="Отмена",
    callback_data="cancel_admin"))
    kbds.adjust(2)
    return kbds.as_markup()




# Получение кнопок для выбора конкретной услуги
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
                callback_data=AdminAddRecordCallBack(
                    level=level,
                    service_category=service_category,  
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminAddRecordCallBack(
                    level=level,
                    service_category=service_category,  
                    page=page - 1
                ).pack()))
            
    keyboard.add(InlineKeyboardButton(text="Выбрать",
        callback_data=AdminAddRecordCallBack(
            level = level+1,
            service_category= service_category,
            page = 1,
            service_id= service_id,
            name_btn= "select_service"
        ).pack()))

    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    
    return keyboard.row(*row).as_markup()






# Получения кнопок для меню барберов при добавления клиента админом
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
                callback_data=AdminAddRecordCallBack(
                    level= level, 
                    service_id= service_id,
                    barber_id=barber_id,
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminAddRecordCallBack(
                    level= level,
                    barber_id=barber_id,
                    service_id=service_id,
                    page=page - 1
                ).pack()))

    
    keyboard.add(InlineKeyboardButton(text='Выбрать',
        callback_data=AdminAddRecordCallBack(
            level = level+1 ,
            service_category=service_category,
            service_id= service_id,
            barber_id= barber_id,
            name_btn="select_barber").pack()))

    keyboard.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    keyboard.adjust(2)
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
            callback_data=AdminAddRecordCallBack(
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
        callback_data=AdminAddRecordCallBack(
            level=level - 1,
            service_category=service_category,
            service_id=service_id,
            page=1
        ).pack()
    ))
    kbds.adjust(2)
    return kbds.as_markup()









# Получение кнопок свободных слотов на конкретный день
def get_select_time_kb_for_record(slots, level, service_category, service_id, barber_id, date):
    keyboard = InlineKeyboardBuilder()

    for slot_time in slots:
        text = slot_time.strftime("%H:%M")
        
        time_str = slot_time.strftime("%H_%M")

        keyboard.add(
            InlineKeyboardButton(
                text=text,
                callback_data=AdminAddRecordCallBack(
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
            callback_data=AdminAddRecordCallBack(
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











# ...................................................................................................................................................................
# ...................................................................................................................................................................
# ...................................................................................................................................................................



# Просмотр записей пользователей

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
                callback_data=AdminViewSlotsCallBack(
                    level= level, 
                    barber_id=barber_id,
                    page=page + 1
                ).pack()))
        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                callback_data=AdminViewSlotsCallBack(
                    level= level,
                    barber_id=barber_id,
                    page=page - 1
                ).pack()))

    
    kbds.add(InlineKeyboardButton(text='Выбрать',
        callback_data=AdminViewSlotsCallBack(
            level = level+1 ,
            barber_id= barber_id,
            barber_name= barber_name,
            name_btn="select_barber").pack()))

    kbds.add(InlineKeyboardButton(text="Отмена",
        callback_data="cancel_admin"))
    kbds.adjust(2)
    return kbds.row(*row).as_markup()







def get_select_date_kb_for_view(dates: list[date], level: int, barber_id: int, barber_name: str):
    kbds = InlineKeyboardBuilder()

    for d in dates:
        display_text = format_date_rus(d)  # В кнопке
        date_str = d.strftime("%d.%m.%Y")  # В callback
        kbds.add(InlineKeyboardButton(
            text=display_text,
            callback_data=AdminViewSlotsCallBack(
            level=level + 1, \
            barber_id=barber_id,
            barber_name=barber_name,
            date=date_str).pack()))
        
    
    kbds.add(InlineKeyboardButton(text="🔙 Назад", callback_data=AdminViewSlotsCallBack(level=level - 1).pack()))
    kbds.add(InlineKeyboardButton(text="Отмена",
    callback_data="cancel_admin"))
    kbds.adjust(2)
    return kbds.as_markup()








def get_what_do_for_view(level: int, barber_id: int, barber_name: str, date: str):
    kbds = InlineKeyboardBuilder()
    
    # Кнопка удалить запись
    kbds.row(
        InlineKeyboardButton(
            text="🗑 Удалить запись",
            callback_data=AdminViewSlotsCallBack(
                level=level + 1,
                barber_id=barber_id,
                barber_name=barber_name,
                date=date,
                page=1  # если требуется, можно менять
            ).pack()
        )
    )

    # Кнопка назад
    kbds.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=AdminViewSlotsCallBack(
                level=level - 1,
                barber_id=barber_id,
                barber_name=barber_name,
                page=1,
                date=date
            ).pack()
        )
    )

    # Кнопка отмены
    kbds.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_admin"
        )
    )
    kbds.adjust(2)
    return kbds.as_markup()
















# text то что написанно на кнопке callback_data то что кнопка отправляет это не видит пользователь
def get_callback_btns(
        *,
        btns: dict[str,str],
        sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text = text, callback_data = data))

    return keyboard.adjust(*sizes).as_markup()







def get_confirm_delete_barber_kb(barber_id: int):
    return get_callback_btns(btns={
        "✅ Подтвердить удаление": f"confirm_delete_barber_{barber_id}",
        "❌ Отмена": "cancel_admin"
    })