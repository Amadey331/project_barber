from sqlalchemy.ext.asyncio import AsyncSession

from kbds.inline_admin import (
    get_admin_services_category_btns,
    get_admin_services_list_btns
    
)


from database.orm_query import (
    orm_get_services,
    orm_delete_service_by_id,
    orm_get_service_by_id,
    orm_log_admin_action
    
)


from utils.paginator import Paginator


from aiogram.utils.keyboard import InlineKeyboardBuilder



from aiogram.types import InlineKeyboardButton

from kbds.inline_admin import AdminServicesListCallBack



def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns



async def admin_service_list_category(session, level,):
    kbds = get_admin_services_category_btns(level = level)
    text = "📌 Укажите категорию услуги"
    return text, kbds



async def admin_service_cur_category_list(
    session,
    level,
    category,
    page,
    service_id,
    name_btn,
    admin_id=None  # добавим admin_id
):
    services = await orm_get_services(session, category)

    if not services:
        text = "⚠️ В этой категории пока нет добавленных услуг."
        kbds = InlineKeyboardBuilder()
        kbds.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=AdminServicesListCallBack(level=0).pack()
        ))
        return text, kbds.as_markup()

    if name_btn == "delete":
        service_name = await orm_delete_service_by_id(session, service_id=service_id)

        # 🔴 Логирование удаления
        if admin_id:
            await orm_log_admin_action(
                session=session,
                admin_id=admin_id,
                action="Удаление услуги",
                description=f"Удалена услуга '{service_name}' (ID: {service_id})"
            )

        text = f"✅ Услуга с наименованием: <b>{service_name}</b> успешно удалена."
        kbds = get_admin_services_category_btns(level=0)
        return text, kbds
    

    




    paginator = Paginator(services, page=page)
    service = paginator.get_page()[0]

    text = f"""
<b>📌 Услуга:</b> {service.service_name}
💰 <b>Цена:</b> {round(service.service_price, 2)} руб.
⏳ <b>Длительность:</b> {service.service_duration} мин.
🏷 <b>Категория:</b> {service.service_category}

<strong>Услуга {paginator.page} из {paginator.pages}</strong>
"""

    pagination_btns = pages(paginator)

    kbds = get_admin_services_list_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        service_id=service.id
    )

    return text, kbds



async def get_admin_servives_list_content(
    session: AsyncSession,
    level: int,
    category: str | None = None,
    page: int | None = None,
    service_id: int | None = None,
    name_btn: str | None = None,
    admin_id: int | None = None  # добавили admin_id
):
    if level == 0:
        return await admin_service_list_category(session, level)
    if level == 1:
        return await admin_service_cur_category_list(
            session,
            level,
            category,
            page,
            service_id,
            name_btn,
            admin_id=admin_id  # передаём сюда
        )