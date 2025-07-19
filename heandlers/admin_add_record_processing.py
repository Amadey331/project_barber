from sqlalchemy.ext.asyncio import AsyncSession

from kbds.inline_admin import (
    get_service_categoty_for_record,
    get_services_list_btns_for_record,
    get_main_inlineBtns_admin,
    get_barbers_list_btns_for_record,
    get_select_date_kb_for_record,
    get_select_time_kb_for_record,
    AdminAddRecordCallBack
)


from database.orm_query import (
    orm_get_services,
    orm_get_barbers_by_service_id,
    orm_get_available_dates,
    orm_get_free_time_slots
    
)


from utils.paginator import Paginator
from utils.format import format_rating

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton,CallbackQuery
from aiogram.fsm.state import StatesGroup, State

from datetime import datetime

from fsm.admin import AdminAddRecordFSM

from utils.plular_years import plural_years

BARBER_SPECIALIZATIONS = {
    "classic_barber": "💈 Классический барбер",
    "beard_specialist": "🧔‍♂️ Бородист",
    "stylist_barber": "🎨 Стайлист",
    "universal_barber": "🎯 Барбер-универсал"
}


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns




async def record_service_category(session,level):
    text = "📌 Укажите категорию услуги:"
    kbds = get_service_categoty_for_record(session, level)
    return {"text": text, "photo": None, "kb": kbds}




async def record_select_barber(session, level, service_category, service_id, page):
    barbers = await orm_get_barbers_by_service_id(session, service_id)
    paginator = Paginator(barbers, page=page)

    if not paginator.get_page():
        text = "Барберы для этой услуги не найдены"
        kbds = get_main_inlineBtns_admin()
        return {"text": text, "photo": None, "kb": kbds}

    barber = paginator.get_page()[0]
    rating_text = format_rating(barber.rating_sum, barber.rating_count)

    text = f"""
<b>👤 Имя барбера:</b> {barber.name}
📞 <b>Телефон:</b> <code>{barber.phone}</code>
💼 <b>Стаж:</b> {plural_years(barber.experience)}
🎯 <b>Специализация:</b> {BARBER_SPECIALIZATIONS[barber.specialization]}
⭐️ <b>{rating_text}</b>
"""
    kbds = get_barbers_list_btns_for_record(
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber.id,
        page=page,
        pagination_btns=pages(paginator),
    )

    return {"text": text, "photo": barber.photo_path, "kb": kbds}




async def record_service(session, level, service_category, name_btn, page):
    services = await orm_get_services(session, service_category)
    if not services:
        text = "⚠️ В этой категории пока нет добавленных услуг."
        kbds = InlineKeyboardBuilder()
        kbds.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=AdminAddRecordCallBack(level=0).pack()
        ))
        return {"text": text, "photo": None, "kb": kbds.as_markup()}

    paginator = Paginator(services, page=page)
    service = paginator.get_page()[0]

    text = f"""
<b>📌 Услуга:</b> {service.service_name}
💰 <b>Цена:</b> {round(service.service_price, 2)} руб.
⏳ <b>Длительность:</b> {service.service_duration} мин.

<strong>Услуга {paginator.page} из {paginator.pages}</strong>
"""

    pagination_btns = pages(paginator)

    kbds = get_services_list_btns_for_record(
        level=level,
        page=page,
        pagination_btns=pagination_btns,
        service_category=service_category,
        service_id=service.id
    )

    return {"text": text, "photo": None, "kb": kbds}







async def record_select_date(session, level, service_category, service_id, barber_id):
    dates = await orm_get_available_dates(session, barber_id, service_id)

    if not dates:
        text = "⚠️ Нет доступных дат для записи"
        kbds = get_main_inlineBtns_admin()
        return {"text": text, "photo": None, "kb": kbds}

    text = "📅 Выберите дату для записи:"
    kbds = get_select_date_kb_for_record(
        dates=dates,
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber_id
    )

    return {"text": text, "photo": None, "kb": kbds}




async def record_select_time(session, level, service_category, service_id, barber_id, date):
    date_obj = datetime.strptime(date, "%d.%m.%Y").date()
    slots = await orm_get_free_time_slots(session, barber_id, service_id, date_obj)

    if not slots:
        text = "⚠️ Нет доступного времени на выбранную дату"
        kbds = get_main_inlineBtns_admin()
        return {"text": text, "photo": None, "kb": kbds}

    kbds = get_select_time_kb_for_record(
        slots=slots,
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber_id,
        date=date
    )
    text = "⏰ Выберите время для записи:"
    return {"text": text, "photo": None, "kb": kbds}




async def get_add_record_menu_admin(
        session:AsyncSession,
        level : int,
        service_category: str |None = None,
        service_id: int | None = None,
        barber_id: int|None = None,
        name_btn: str | None = None ,
        page: int = 1,
        date: str | None = None,
        time: str | None = None,
        state: StatesGroup | None = None,
        
               
                                    ):
    
    if level == 0 :
        return await record_service_category(session,level)
    if level == 1:
        return await record_service(session,level, service_category, name_btn, page)      
    if level == 2:
        return await record_select_barber(session, level, service_category, service_id, page)
    if level == 3:
        return await record_select_date(session,level, service_category, service_id, barber_id)
    if level == 4:
        return await record_select_time(session,level, service_category, service_id, barber_id, date)
    if level == 5:
        await state.set_state(AdminAddRecordFSM.waiting_for_client_name)
        await state.update_data(
            service_category=service_category,
            service_id=service_id,
            barber_id=barber_id,
            date=date,
            time=time,
        )
        text = "👤 Введите имя клиента:"
        kbds = InlineKeyboardBuilder()
        kbds.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=AdminAddRecordCallBack(level=0).pack()
        ))
        return {"text": text, "photo": None, "kb": kbds.as_markup()}