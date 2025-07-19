from sqlalchemy.ext.asyncio import AsyncSession



from database.orm_query import (
    orm_get_services,
    orm_delete_service_by_id,
    orm_get_service_by_id
)

from utils.paginator import Paginator

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.types import InlineKeyboardButton

from kbds.inline_user import get_user_services_category_btns,UserServiceslistCallBack, get_user_services_list_btns


SERVICE_CATEGORIES_REVERSED = {
    "haircut": "✂️ Стрижки",
    "beard": "🧔 Борода и бритьё",
    "care": "💆‍♂️ Уход за волосами и кожей",
    "styling": "🎭 Стайлинг",
    "combo": "🎟 Комплексные услуги"}


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def user_service_list_category(session, level,):
    kbds = get_user_services_category_btns(level = level)
    text = "📌 Укажите категорию услуги"
    return text, kbds


async def user_service_cur_category_list(session, level, category, page=None):
    services = await orm_get_services(session, category)

    if not services:
        text = "⚠️ В этой категории пока нет добавленных услуг."
        kbds = InlineKeyboardBuilder()
        kbds.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=UserServiceslistCallBack(level=0).pack()
        ))
        return text, kbds.as_markup()

    text = f"<b>📋 Услуги категории: {SERVICE_CATEGORIES_REVERSED[category]}</b>\n\n"
    for idx, service in enumerate(services, start=1):
        text += (
            f"{idx}. <b>{service.service_name}</b>\n"
            f"💰 {round(service.service_price, 2)} руб. | ⏳ {service.service_duration} мин.\n\n"
        )

    kbds = InlineKeyboardBuilder()
    kbds.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=UserServiceslistCallBack(level=0).pack()
    ))

    return text.strip(), kbds.as_markup()







async def get_user_servives_list_content(
        session: AsyncSession,
        level: int,
        category: str | None = None,
        page: int| None = None,
        service_id : int| None = None,
        name_btn: str | None = None

):
    if level == 0:
        return await user_service_list_category(session,level)
    if level == 1:
        return await user_service_cur_category_list(session, level, category, page)