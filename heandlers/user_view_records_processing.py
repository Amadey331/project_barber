from sqlalchemy.ext.asyncio import AsyncSession


from utils.paginator import Paginator


from database.orm_query import (
    orm_get_actual_appointments_by_user_id,
    orm_get_service_by_id,
    orm_get_barber_by_id,
    orm_delete_appointment_if_possible
    
)
from kbds.inline_user import get_main_inlineBtns_user,get_user_records_btns

def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns

async def user_records(session: AsyncSession, user_id: int, appointment_id: int, page: int = 1):
    appointments = await orm_get_actual_appointments_by_user_id(session, user_id)

    if not appointments:
        return "📭 У вас нет записей.", get_main_inlineBtns_user()

    paginator = Paginator(appointments, page=page)
    appointment = paginator.get_page()[0]

    # Теперь используем встроенные поля, а не делаем лишние запросы
    service_name = appointment.service_name or "неизвестная услуга"
    service_price = f"{round(appointment.service_price, 2)} ₽" if appointment.service_price else "неизвестно"
    barber_name = appointment.barber_name or "неизвестный барбер"

    text = (
        f"📌 <b>Услуга:</b> {service_name}\n"
        f"💰 <b>Цена:</b> {service_price}\n"
        f"💈 <b>Барбер:</b> {barber_name}\n"
        f"📅 <b>Дата:</b> {appointment.date_appointment.strftime('%d.%m.%Y')}\n"
        f"⏰ <b>Время:</b> {appointment.time_appointment.strftime('%H:%M')}\n"
        f"\n📄 <i>Запись {paginator.page} из {paginator.pages}</i>"
    )

    pagination_btns = pages(paginator)

    kbds = get_user_records_btns(
        level=0,
        page=page,
        pagination_btns=pagination_btns,
        appointment_id=appointment.id
    )

    return text, kbds


async def user_delete_record(session: AsyncSession, user_id: int, page: int, appointment_id: int):
    success = await orm_delete_appointment_if_possible(session, appointment_id)

    if success:
        return "✅ Ваша запись успешно удалена.", get_main_inlineBtns_user()
    else:
        return "❌ Нельзя отменить запись менее чем за 3 часа до её начала.", get_main_inlineBtns_user()



async def get_user_records_list(
        session: AsyncSession,
        level: int,
        user_id: int,
        page: int = 1,
        appointment_id: int | None = None
):
    if level == 0:
        return await user_records(session=session, user_id=user_id, page=page, appointment_id=appointment_id)
    if level == 1:
        return await user_delete_record(session=session, user_id=user_id, page=page, appointment_id=appointment_id)