from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.context import FSMContext

from scheduler import schedule_reminder


from kbds.inline_user import (
    get_service_categoty_for_record,
    get_main_inlineBtns_user,
    get_barbers_list_btns_for_record,
    get_services_list_btns_for_record,
    get_select_date_kb_for_record,
    get_select_time_kb_for_record,
    get_callback_btns,
    UserAddRecordCallBack,
    get_confirm_record_kb

)

from kbds.replay_user_kb import(
    get_send_number_kb_user
)



from aiogram.types import CallbackQuery

from database.orm_query import (
    orm_get_services,
    orm_get_barbers_by_service_id,
    orm_get_available_dates,
    orm_get_free_time_slots,
    orm_check_daily_limit,
    orm_add_appointment_user,
    orm_get_service_by_id,
    orm_get_barber_by_id,
    orm_get_user_by_id,
    orm_slot_exists_in_history,
    orm_save_to_history,
    orm_check_barber_slot_taken,
    orm_check_user_double_booking
    
    
)


from utils.paginator import Paginator


from aiogram.utils.keyboard import InlineKeyboardBuilder


from aiogram.types import InlineKeyboardButton,CallbackQuery


from datetime import datetime

from fsm.user import UserRecordStates

from aiogram.fsm.state import StatesGroup, State

from fsm.admin import AdminAddRecordFSM

from utils.plular_years import plural_years
from utils.format import format_rating

from datetime import datetime, timedelta


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
    return text,kbds




async def record_select_barber(session, level, service_category, service_id, page):
    barbers = await orm_get_barbers_by_service_id(session, service_id)
    paginator = Paginator(barbers, page=page)

    if not paginator.get_page():
        text = "Барберы для этой услуги не найдены"
        kbds = get_main_inlineBtns_user()
        return text, None, kbds

    barber = paginator.get_page()[0]

    rating_text = format_rating(barber.rating_sum, barber.rating_count)

    text = f"""
<b>👤 Имя барбера:</b> {barber.name}
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

    return text, barber.photo_path, kbds




async def record_service(session, level, service_category,  name_btn, page):

    
    services = await orm_get_services(session, service_category)
    if not services:
        text = "⚠️ В этой категории пока нет добавленных услуг."
        kbds = InlineKeyboardBuilder()
        kbds.add(InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data=UserAddRecordCallBack(level=0).pack()
        ))
        return text, kbds.as_markup()

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
        page= page,
        pagination_btns= pagination_btns,
        service_category = service_category,
        service_id= service.id
    )
    
    return text,kbds







async def record_select_date(
        session,
        level,
        service_category,
        service_id, 
        barber_id, 

):
    dates = await orm_get_available_dates(session, barber_id, service_id)

    if not dates:
        text = "⚠️ Нет доступных дат для записи", get_main_inlineBtns_user()
        return text

    text =  "📅 Выберите дату для записи:"

    kbds = get_select_date_kb_for_record(
        dates=dates,
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber_id
    )



    return text, kbds




async def record_select_time(session, level, service_category, service_id, barber_id, date):
    date_obj = datetime.strptime(date, "%d.%m.%Y").date()
    slots = await orm_get_free_time_slots(session, barber_id, service_id, date_obj)

    if not slots:
        
        text = "⚠️ Нет доступного времени на выбранную дату"
        kbds = get_main_inlineBtns_user()
        return text,kbds
    kbds = get_select_time_kb_for_record(
        slots=slots,
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber_id,
        date=date
    )
    text = "⏰ Выберите время для записи:"
    return text, kbds





async def record_confirm_appointment(
    session: AsyncSession,
    level: int,
    service_category: str,
    service_id: int,
    barber_id: int,
    date: str,
    time: str,
    callback_query: CallbackQuery
):
    user = await orm_get_user_by_id(session, callback_query.from_user.id)
    if not user:
        return (
            "❌ Не удалось получить ваш номер. Попробуйте перезапустить бота через /start",
            get_main_inlineBtns_user()
        )

    # --- Преобразуем дату и время ---
    try:
        date_obj = datetime.strptime(date, "%d.%m.%Y").date()
        time_obj = datetime.strptime(time.replace("_", ":"), "%H:%M").time()
    except Exception:
        return "❌ Ошибка формата даты или времени. Попробуйте ещё раз.", get_main_inlineBtns_user()

    # --- Проверка на прошедшее время ---
    now = datetime.now()
    appointment_datetime = datetime.combine(date_obj, time_obj)
    if appointment_datetime <= now:
        return "❌ Этот слот уже недоступен — выберите время позже текущего.", get_main_inlineBtns_user()

    # --- Проверка двойного бронирования в это же время ---
    double_booking = await orm_check_user_double_booking(
        session=session,
        phone=user.phone,
        date_=date_obj,
        time_=time_obj
    )
    if double_booking:
        return (
            "❌ Вы уже записаны на услугу в это время. Выберите другой слот.",
            get_main_inlineBtns_user()
        )

    # --- Проверка истории (тот же слот уже был) ---
    already_booked = await orm_slot_exists_in_history(
        session=session,
        phone=user.phone,
        date_=date_obj,
        time_=time_obj
    )
    if already_booked:
        return (
            "❌ Вы уже ранее были записаны на это время. Попробуйте выбрать другой слот.",
            get_main_inlineBtns_user()
        )

    # --- Проверка лимита на день ---
    limit_exceeded = await orm_check_daily_limit(session, phone=user.phone, date=date_obj)
    if limit_exceeded:
        return (
            "❌ Вы уже записаны на 2 услуги в этот день. Нельзя записаться больше.",
            get_main_inlineBtns_user()
        )

    # --- Проверка занят ли слот у барбера ---
    slot_taken = await orm_check_barber_slot_taken(
        session=session,
        barber_id=barber_id,
        date_=date_obj,
        time_=time_obj
    )
    if slot_taken:
        return (
            "❌ Этот слот уже занят выбранным барбером. Попробуйте выбрать другое время.",
            get_main_inlineBtns_user()
        )

    # --- Загрузка данных для красивого подтверждения ---
    service = await orm_get_service_by_id(session, service_id)
    barber = await orm_get_barber_by_id(session, barber_id)
    if not service or not barber:
        return (
            "❌ Ошибка загрузки данных. Попробуйте выбрать заново.",
            get_main_inlineBtns_user()
        )

    service_price = float(service.service_price) if service.service_price else 0.0

    text = (
        f"✅ <b>Проверьте данные перед подтверждением записи:</b>\n\n"
        f"📅 <b>Дата:</b> {date}\n"
        f"⏰ <b>Время:</b> {time.replace('_', ':')}\n"
        f"💈 <b>Барбер:</b> {barber.name}\n"
        f"🛠 <b>Услуга:</b> {service.service_name}\n"
        f"💰 <b>Стоимость:</b> {round(service_price, 2)} ₽\n\n"
        f"Нажмите «Подтвердить», чтобы завершить запись."
    )

    kbds = get_confirm_record_kb(
        level=level,
        service_category=service_category,
        service_id=service_id,
        barber_id=barber_id,
        date=date,
        time=time
    )

    return text, kbds























async def record_save_appointment(
    session: AsyncSession,
    level: int,
    service_category: str,
    service_id: int,
    barber_id: int,
    date: str,
    time: str,
    callback_query: CallbackQuery
):
    user = await orm_get_user_by_id(session, callback_query.from_user.id)
    if not user:
        return (
            "❌ Не удалось получить ваш номер. Попробуйте перезапустить бота через /start",
            get_main_inlineBtns_user()
        )

    # --- Преобразуем дату и время ---
    date_obj = datetime.strptime(date, "%d.%m.%Y").date()
    time_obj = datetime.strptime(time.replace("_", ":"), "%H:%M").time()
    appointment_datetime = datetime.combine(date_obj, time_obj)

    # --- Финальное добавление записи в основную таблицу ---
    success, response_message, appointment_id = await orm_add_appointment_user(
        session=session,
        client_name=callback_query.from_user.full_name,
        phone=user.phone,
        date_str=date,
        time_str=time,
        service_id=service_id,
        barber_id=barber_id
    )

    if not success:
        return f"❌ Ошибка при создании записи.\n\n{response_message}", get_main_inlineBtns_user()

    # --- Добавляем в историю ---
    await orm_save_to_history(
        session=session,
        client_name=callback_query.from_user.full_name,
        phone=user.phone,
        date_=date_obj,
        time_=time_obj,
        service_id=service_id,
        barber_id=barber_id
    )

    # --- Для напоминания загружаем сервис и барбера ---
    service = await orm_get_service_by_id(session, service_id)
    barber = await orm_get_barber_by_id(session, barber_id)

    service_name = service.service_name if service else "неизвестная услуга"
    barber_name = barber.name if barber else "неизвестный барбер"

    # --- Планируем напоминание ---
    remind_time = appointment_datetime - timedelta(hours=1)
    reminder_text = (
        f"🔔 Напоминание о записи!\n\n"
        f"⏰ <b>Время:</b> {appointment_datetime.strftime('%H:%M %d.%m.%Y')}\n"
        f"💈 <b>Барбер:</b> {barber_name}\n"
        f"🛠 <b>Услуга:</b> {service_name}"
    )

    schedule_reminder(
        bot=callback_query.bot,
        chat_id=callback_query.message.chat.id,
        remind_time=remind_time,
        text=reminder_text,
        appointment_id=appointment_id
    )

    return response_message, get_main_inlineBtns_user()





async def get_add_record_menu_user(
        session: AsyncSession,
        level: int,
        service_category: str | None = None,
        service_id: int | None = None,
        barber_id: int | None = None,
        name_btn: str | None = None,
        page: int = 1,
        date: str | None = None,
        time: str | None = None,
        state: StatesGroup | None = None,
        callback_query: CallbackQuery | None = None,
):
    if level == 0:
        text, kbds = await record_service_category(session, level)
        return text, None, kbds
    if level == 1:
        text, kbds = await record_service(session, level, service_category, name_btn, page)
        return text, None, kbds
    if level == 2:
        return await record_select_barber(session, level, service_category, service_id, page)
    if level == 3:
        text, kbds = await record_select_date(session, level, service_category, service_id, barber_id)
        return text, None, kbds
    if level == 4:
        text, kbds = await record_select_time(session, level, service_category, service_id, barber_id, date)
        return text, None, kbds
    

    if level == 5:
        text, kbds = await record_confirm_appointment(
            session=session,
            level=level,
            service_category=service_category,
            service_id=service_id,
            barber_id=barber_id,
            date=date,
            time=time,
            callback_query=callback_query
        )
        return text, None, kbds


    if level == 6:
        text, kbds = await record_save_appointment(
            session=session,
            level=level,
            service_category=service_category,
            service_id=service_id,
            barber_id=barber_id,
            date=date,
            time=time,
            callback_query=callback_query
        )
        return text, None, kbds


    # if level == 5:
    #     user = await orm_get_user_by_id(session, callback_query.from_user.id)
    #     if not user:
    #         return "❌ Не удалось получить ваш номер. Попробуйте перезапустить бота через /start", None, get_main_inlineBtns_user()

    #     await state.update_data(
    #         service_category=service_category,
    #         service_id=service_id,
    #         barber_id=barber_id,
    #         date=date,
    #         time=time,
    #         client_name=callback_query.from_user.full_name,
    #         phone=user.phone
    #     )

    #     text, kbds = await confirm_and_save_user_appointment(callback_query, state, session)
    #     return text, None, kbds





# функция для удаления послежнего сообщения
async def delete_last_message(env, data):
    """Удаляет последнее сообщение с кнопками, если оно есть."""
    if "last_msg_id" in data:
        
        chat_id = env.message.chat.id if isinstance(env, CallbackQuery) else env.chat.id
        bot = env.bot if isinstance(env, CallbackQuery) else env._bot
        
        try:

            await bot.delete_message(chat_id, data["last_msg_id"])
        except Exception:

            pass  # Игнорируем ошибку, если сообщение уже удалено
