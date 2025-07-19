from sqlalchemy.ext.asyncio import AsyncSession

from utils.paginator import Paginator
from utils.format import format_rating
from database.orm_query import (
    orm_get_all_barbers,
    orm_get_barber_schedule_by_id,
    orm_get_available_dates_for_view_slots,
    orm_get_appointments_for_view_slots
    )

from database.models import AppointmentStatus
from kbds.inline_admin import (
    get_barbers_list_btns_for_view_slots,
    get_main_inlineBtns_admin,
    get_select_date_kb_for_view,
    get_what_do_for_view,
    AdminViewSlotsCallBack
    )

from datetime import datetime


from aiogram.fsm.state import StatesGroup, State

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fsm.admin import AdminDeleteRecordFSM



from utils.plular_years import plural_years


STATUS_LABELS = {
    AppointmentStatus.PENDING: "⏳ Ожидает подтверждения",
    AppointmentStatus.CONFIRMED: "✅ Подтверждена",
    AppointmentStatus.CANCELLED: "❌ Отменена",
    AppointmentStatus.ADDED_BY_ADMIN: "📌 Добавлена админом"
}


BARBER_SPECIALIZATIONS = {
    "classic_barber": "💈 Классический барбер",
    "beard_specialist": "🧔‍♂️ Бородист",
    "stylist_barber": "🎨 Стайлист",
    "universal_barber": "🎯 Барбер-универсал"
}


WEEKDAY_LABELS = {
    0: "Пн",
    1: "Вт",
    2: "Ср",
    3: "Чт",
    4: "Пт",
    5: "Сб",
    6: "Вс"
}


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns

async def view_slots_select_barber(session, level, page):
    barbers = await orm_get_all_barbers(session)
    paginator = Paginator(barbers, page=page)

    if not paginator.get_page():
        return {
            "text": "Барберы не найдены",
            "photo": None,
            "kb": get_main_inlineBtns_admin()
        }

    barber = paginator.get_page()[0]

    rating_text = format_rating(barber.rating_sum, barber.rating_count)

    text = f"""
<b>👤 Имя барбера:</b> {barber.name}
📞 <b>Телефон:</b> <code>{barber.phone}</code>
💼 <b>Стаж:</b> {plural_years(barber.experience)}
🎯 <b>Специализация:</b> {BARBER_SPECIALIZATIONS[barber.specialization]}
⭐️ <b>{rating_text}</b>
🎯 <b>Специализация:</b> {BARBER_SPECIALIZATIONS[barber.specialization]}
    """

    schedule = await orm_get_barber_schedule_by_id(session, barber.id)
    if schedule:
        text += "\n<b>📅 График работы:</b>\n"
        for weekday in sorted(schedule):
            start, end = schedule[weekday]
            text += f"• {WEEKDAY_LABELS[weekday]} — {start.strftime('%H:%M')}–{end.strftime('%H:%M')}\n"
    else:
        text += "\n📅 <i>График не задан</i>\n"

    kbds = get_barbers_list_btns_for_view_slots(
        level=level,
        barber_id=barber.id,
        barber_name=barber.name,
        page=page,
        pagination_btns=pages(paginator)
    )

    return {
        "text": text,
        "photo": barber.photo_path,
        "kb": kbds
    }




async def view_slots_select_date(
        session,
        level, 
        barber_id, 
        barber_name

):
    dates_with_slots = await orm_get_available_dates_for_view_slots(session, barber_id)

    if not dates_with_slots:
        text = "⚠️ У выбранного барбера нет доступных дат на ближайшие 14 дней."
        return text, get_main_inlineBtns_admin()

    text = "📅 Выберите дату для просмотра свободных слотов:"

    kbds = get_select_date_kb_for_view(
        dates=dates_with_slots,
        level=level,
        barber_id=barber_id,
        barber_name = barber_name
        
    )

    return text, kbds


async def view_slots(session: AsyncSession, level: int, barber_id: int, barber_name:str, page: int, date: str):
    """Формирует сообщение со списком записей барбера на указанную дату."""
    date_obj = datetime.strptime(date, "%d.%m.%Y").date()

    appointments = await orm_get_appointments_for_view_slots(session, barber_id, date_obj)

    if not appointments:
        dates_with_slots = await orm_get_available_dates_for_view_slots(session, barber_id)
        kbds = get_select_date_kb_for_view(
        dates=dates_with_slots,
        level=level-1,
        barber_id=barber_id,
        barber_name=barber_name
        
    )
        return "ℹ️ На выбранную дату нет записей.", kbds

    text_lines = [f"📅 Записи на <b>{date}</b> для барбера <b>{barber_name}</b>:\n"]

    for i, (app_id, time, name, phone, service_name, duration, status) in enumerate(appointments, start=1):
        time_str = time.strftime("%H:%M")
        status_text = STATUS_LABELS.get(status, "🟡 Неизвестно")
        
        text_lines.append(
            f"<b>{i}.</b> 🔖 <b>ID:</b> <code>{app_id}</code>\n"
            f"   🕒 <b>Время:</b> <i>{time_str}</i> — <i>{service_name}</i> ({duration} мин)\n"
            f"   👤 <b>Имя:</b> {name}\n"
            f"   📞 <b>Телефон:</b> {phone}\n"
            f"   📌 <b>Статус:</b> {status_text}\n"
        )
    
    text = "\n".join(text_lines)

    
    kbds = get_what_do_for_view(level = level, barber_id=barber_id, barber_name = barber_name, date = date)
    return text, kbds



async def get_view_slots_menu_admin(
        session: AsyncSession,
        level: int,
        barber_id: int | None = None,
        barber_name: str | None = None,
        page: int = 1,
        date: str | None = None,
        state: StatesGroup | None = None
):
    if level == 0:
        return await view_slots_select_barber(session, level, page)
    if level == 1:
        text, kbds = await view_slots_select_date(session, level, barber_id, barber_name)
        return {"text": text, "photo": None, "kb": kbds}
    if level == 2:
        text, kbds = await view_slots(session, level, barber_id, barber_name, page, date)
        return {"text": text, "photo": None, "kb": kbds}
    if level == 3:
        await state.set_state(AdminDeleteRecordFSM.appointment_id)
        await state.update_data(barber_id=barber_id, barber_name=barber_name, date=date)

        date_obj = datetime.strptime(date, "%d.%m.%Y").date()
        appointments = await orm_get_appointments_for_view_slots(session, barber_id, date_obj)

        text_lines = [f"📅 Записи на <b>{date}</b> для барбера <b>{barber_name}</b>:\n"]
        text = "Введите ID записи для удаления:\n\n"

        for i, (app_id, time, name, phone, service_name, duration, status) in enumerate(appointments, start=1):
            time_str = time.strftime("%H:%M")
            text_lines.append(
                f"<b>{i}.</b> 🔖 <b>ID:</b> <code>{app_id}</code>\n"
                f"   🕒 <b>Время:</b> <i>{time_str}</i> — <i>{service_name}</i> ({duration} мин)\n"
                f"   👤 <b>Имя:</b> {name}\n"
                f"   📞 <b>Телефон:</b> {phone}\n"
            )
        text += "\n".join(text_lines)

        kbds = InlineKeyboardBuilder()
        kbds.row(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=AdminViewSlotsCallBack(
                    level=2,
                    barber_id=barber_id,
                    barber_name=barber_name,
                    page=1,
                    date=date
                ).pack()
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_admin"
            )
        )
        return {"text": text, "photo": None, "kb": kbds.as_markup()}