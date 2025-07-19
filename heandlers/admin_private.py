from aiogram import  types , Router, F
from aiogram.filters import CommandStart,Command, or_f, StateFilter
from aiogram.fsm.state import StatesGroup,State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery,FSInputFile
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode
from heandlers.admin_services_list_processing import get_admin_servives_list_content, pages
from heandlers.admin_add_record_processing import get_add_record_menu_admin
from heandlers.admin_view_slots_proccesing import get_view_slots_menu_admin

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter, IsAdmin

import re

import logging

from kbds.inline_admin import (
    get_callback_btns,
    AdminServicesListCallBack,
    AdminBarbersListCallback,
    AdminViewSlotsCallBack,
    AdminAddRecordCallBack,

    get_main_inlineBtns_admin,
    get_barbers_list_what_do_inline,
    get_barbers_list_btns_admin,
    get_weekday_selection_kb_admin,
    get_confirm_delete_barber_kb

)

from database.orm_query import (
    orm_add_admin_to_db,
    orm_log_admin_action,
    orm_get_admin_logs,
    get_admins_list,

    orm_get_admin_name_by_id,
    orm_del_admin_by_id,

    orm_add_service,
    orm_get_service_by_id,
    orm_update_service,

    orm_add_barber,
    orm_get_all_barbers,
    orm_get_barber_by_id,
    orm_update_barber_info,
    orm_delete_barber_by_id,

    orm_save_barber_schedule,
    orm_get_barber_schedule_by_id,
    orm_update_barber_schedule,

    orm_link_barber_to_service,
    orm_get_services_by_barber_id,
    orm_unlink_service_from_barber,

    orm_get_appointments_by_barber,
    orm_add_appontment_admin,
    orm_delete_appointment_by_id,
)

import re

from utils.paginator import Paginator
from utils.plular_years import plural_years

from datetime import date, timedelta, datetime

from fsm.admin import AdminAddRecordFSM,AdminDeleteRecordFSM

from utils.format import format_rating

from kbds.inline_user import get_main_inlineBtns_user

admin_private_router = Router()
admin_private_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# Машина состояния

# Класс для добавления админа
class AddAdmin(StatesGroup):
    name = State()
    admin_id = State()

# Класс для удаления аодмина
class DeleteAdmin(StatesGroup):
    admin_id = State()
    correct = State()


class AddBarbers(StatesGroup):
    name = State()
    phone = State()
    experience = State()
    specialization = State()
    photo = State()  
    schedule_action = State()
    work_days = State()
    work_time_input = State()


# Класс для добовления услуги
class AddService(StatesGroup):
    name = State()
    price = State()
    duration = State()
    category = State()

    select_barber_to_link = State()

# Класс для отвязки услуги
class UnlinkServiceState(StatesGroup):
    choosing_service = State()




class AdminLogFSM(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    viewing_logs = State()


SERVICE_CATEGORIES_REVERSED = {
    "haircut": "✂️ Стрижки",
    "beard": "🧔 Борода и бритьё",
    "care": "💆‍♂️ Уход за волосами и кожей",
    "styling": "🎭 Стайлинг",
    "combo": "🎟 Комплексные услуги"}

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
# Команды администратора

@admin_private_router.message(Command("admin"))
async def get_admin_kbds(message: types.Message, state:FSMContext):

    await message.delete()

    
    sent_message = await message.answer(":Панель администратора:", reply_markup=get_main_inlineBtns_admin())
    await state.update_data(last_msg_id=sent_message.message_id)










# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

# Добавление записи адимином
@admin_private_router.callback_query(F.data == "add_recod_admin")
async def add_record_admin(callback_query: CallbackQuery, session: AsyncSession):
    result = await get_add_record_menu_admin(session, level=0)

    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=result["text"],
        photo_path=result["photo"],
        kb=result["kb"]
    )

    await callback_query.answer()



@admin_private_router.callback_query(AdminAddRecordCallBack.filter())
async def add_record_menu_admin(callback_query: CallbackQuery, callback_data: AdminAddRecordCallBack, state: FSMContext, session: AsyncSession):
    result = await get_add_record_menu_admin(
        session=session,
        level=callback_data.level,
        service_category=callback_data.service_category,
        service_id=callback_data.service_id,
        barber_id=callback_data.barber_id,
        name_btn=callback_data.name_btn,
        page=callback_data.page,
        date=callback_data.date,
        time=callback_data.time,
        state=state
    )

    if callback_data.level == 5:
        # попытка удалить старое
        data = await state.get_data()
        try:
            if "last_msg_id" in data:
                await callback_query.bot.delete_message(callback_query.message.chat.id, data["last_msg_id"])
        except Exception as e:
            logging.warning(f"Не удалось удалить предыдущее сообщение запроса имени: {e}")

        # отправка нового
        sent_message = await callback_query.message.answer(
            result["text"],
            reply_markup=result["kb"]
        )

        await state.update_data(last_msg_id=sent_message.message_id)
        await callback_query.answer()
        return
    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=result["text"],
        photo_path=result["photo"],
        kb=result["kb"]
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await callback_query.answer()



@admin_private_router.message(AdminAddRecordFSM.waiting_for_client_name)
async def process_client_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # удаляем вопрос "Введите имя клиента"
    try:
        if "last_msg_id" in data:
            await message.bot.delete_message(message.chat.id, data["last_msg_id"])
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение с запросом имени: {e}")

    # удаляем сам пользовательский ответ
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить ответ пользователя: {e}")

    await state.update_data(client_name=message.text)

    # новый вопрос про номер
    msg = await message.answer(
        "📞 Введите номер телефона клиента (пример 79672636102):"
    )

    await state.update_data(last_msg_id=msg.message_id)
    await state.set_state(AdminAddRecordFSM.waiting_for_client_phone)



@admin_private_router.message(AdminAddRecordFSM.waiting_for_client_phone)
async def process_client_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(phone=message.text)
    data = await state.get_data()

    # удаляем вопрос про телефон
    try:
        if "last_msg_id" in data:
            await message.bot.delete_message(message.chat.id, data["last_msg_id"])
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение с запросом телефона: {e}")

    # удаляем сам пользовательский ответ
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить ответ пользователя: {e}")

    # далее всё как есть
    date_obj = datetime.strptime(data["date"], "%d.%m.%Y").date()
    time_obj = datetime.strptime(data["time"].replace("_", ":"), "%H:%M").time()

    result_text, service_name, barber_name = await orm_add_appontment_admin(session, data, date_obj, time_obj)

    if service_name and barber_name:
        await orm_log_admin_action(
            session=session,
            admin_id=message.from_user.id,
            action="Добавление записи",
            description=(
                f"Запись клиента '{data['client_name']}' на {data['date']} {data['time']} "
                f"к барберу '{barber_name}' на услугу '{service_name}'"
            )
        )

    msg = await message.answer(result_text, reply_markup=get_main_inlineBtns_admin())
    await state.update_data(last_msg_id=msg.message_id)
    await state.clear()

















# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Список слотов на конекретную дату по барберу



@admin_private_router.callback_query(F.data == "view_slots_admin")
async def view_slots_admin(callback_query: CallbackQuery, session: AsyncSession):
    result = await get_view_slots_menu_admin(session, level=0)

    sent_msg = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=result["text"],
        photo_path=result["photo"],
        kb=result["kb"]
    )
    await callback_query.answer()



@admin_private_router.callback_query(AdminViewSlotsCallBack.filter())
async def view_slots_menu_admin(callback_query: CallbackQuery, callback_data: AdminViewSlotsCallBack, state: StatesGroup, session: AsyncSession):
    result = await get_view_slots_menu_admin(
        session=session,
        level=callback_data.level,
        barber_id=callback_data.barber_id,
        barber_name=callback_data.barber_name,
        page=callback_data.page,
        date=callback_data.date,
        state=state
    )

    sent_msg = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=result["text"],
        photo_path=result["photo"],
        kb=result["kb"]
    )

    await state.update_data(last_msg_id=sent_msg.message_id)
    await callback_query.answer()


@admin_private_router.message(AdminDeleteRecordFSM.appointment_id)
async def view_slots_delete_admin(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    # Удаляем предыдущее сообщение-запрос, если было
    try:
        if "last_msg_id" in data:
            await message.bot.delete_message(message.chat.id, data["last_msg_id"])
    except Exception as e:
        logging.warning(f"[ADMIN] Не удалось удалить сообщение с запросом ID: {e}")

    # Удаляем пользовательский ответ (сам ID)
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"[ADMIN] Не удалось удалить ответ пользователя: {e}")

    # Парсинг ID
    try:
        appointment_id = int(message.text.strip())
    except ValueError:
        sent = await message.answer("❌ Введите корректный ID (целое число):")
        await state.update_data(last_msg_id=sent.message_id)
        return

    # Удаляем запись из БД
    deleted = await orm_delete_appointment_by_id(session, appointment_id)
    admin_id = message.from_user.id

    if deleted:
        sent = await message.answer(
            f"✅ Запись с ID <code>{appointment_id}</code> успешно удалена.",
            reply_markup=get_main_inlineBtns_admin(),
            parse_mode="HTML"
        )

        await orm_log_admin_action(
            session=session,
            admin_id=admin_id,
            action="Удаление записи",
            description=f"Удалена запись с ID {appointment_id}"
        )

    else:
        sent = await message.answer(
            f"⚠️ Запись с ID <code>{appointment_id}</code> не найдена.",
            parse_mode="HTML"
        )

        await orm_log_admin_action(
            session=session,
            admin_id=admin_id,
            action="Попытка удаления записи",
            description=f"Попытка удалить несуществующую запись с ID {appointment_id}"
        )

    
    await state.clear()

    await state.update_data(last_msg_id=sent.message_id)

















# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Редактирование
@admin_private_router.callback_query(F.data == "edit")
async def edit(callback_query: CallbackQuery, session: AsyncSession):
    await callback_query.answer()
    await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="Что отредактировать?",
        kb=get_callback_btns(btns={
            "💼 Список услуг": "edit_servisec_what_do",
            "✂️ Барберы": "edit_barbers_what_do",
            "🔙 Отмена": "cancel_admin"
        })
    )
    

# Выбор что сделать со списком барберов
@admin_private_router.callback_query(F.data == "edit_barbers_what_do")
async def edit_barbers_what_do(callback_query: CallbackQuery, session: AsyncSession):
    await callback_query.answer()
    await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="Что вы хотите сделать со списком барберов?",
        kb=get_barbers_list_what_do_inline()
    )


# Начало машины состояния для добавления барбера
@admin_private_router.callback_query(F.data == "add_barber")
async def add_barber(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback_query.answer()
    
    text = (
        "🆕 <b>Добавление нового барбера</b>\n\n"
        "✏️ Введите <b>имя барбера</b> 📝"
    )
    
    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=text,
        kb=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddBarbers.name)
    await state.update_data(obj=None)


# Состояние добовления имени барбера
@admin_private_router.message(AddBarbers.name, F.text)
async def add_barber_name(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    obj = data.get("obj")

    # Удаляем предыдущее системное сообщение с кнопками
    await delete_last_message(message, data)

    # Пробуем удалить сообщение пользователя (оно может быть уже удалено)
    try:
        await message.delete()
    except Exception:
        pass

    # Сохраняем имя
    if obj and message.text.strip() == ".":
        name = obj.name
    else:
        name = message.text.strip()

    await state.update_data(name=name)

    # Готовим текст следующего шага
    if obj:
        text = (
            f"📞 <b>Введите номер телефона барбера</b>, текущий: <code>{obj.phone}</code>\n"
            "Отправьте <code>.</code>, чтобы оставить без изменений.\n"
            "Формат: только цифры, например <code>79622718309</code> 📝"
        )
    else:
        text = (
            "📞 <b>Введите номер телефона барбера</b> в числовом формате:\n"
            "<code>79622718309</code> 📝"
        )

    # Отправляем новый запрос
    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddBarbers.phone)




# Оброботчик ошибки если формат неверный
@admin_private_router.message(AddBarbers.name)
async def add_barber_name_err(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ Неверный формат данных. Введите текст для имени барбера.\n\n✏️ Попробуйте снова:",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)




# Добавлениеy номера телефона барбера
@admin_private_router.message(AddBarbers.phone, F.text)
async def add_barber_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    obj = data.get("obj")
    text = message.text.strip()

    if obj and text == ".":
        phone = obj.phone
    elif text.isdigit():
        phone = text
    else:
        return await add_barber_phone_err(message, state)

    await state.update_data(phone=phone)

    # Удаляем старое системное сообщение
    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    exp_text = f", текущее: <b>{obj.experience}</b> (отправьте <code>.</code> чтобы оставить)" if obj else ":"

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text=f"⏳ <b>Введите опыт работы в годах</b> (если меньше года — 0){exp_text}",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddBarbers.experience)



# Ошибка, если формат телефона неверный
@admin_private_router.message(AddBarbers.phone)
async def add_barber_phone_err(message: types.Message, state: FSMContext):
    data = await state.get_data()

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ <b>Введите корректный номер</b> (только цифры, например <code>79622718309</code>):",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)


# Добавление опыта работы барбера
@admin_private_router.message(AddBarbers.experience, F.text)
async def add_barber_experience(message: types.Message, state: FSMContext):
    data = await state.get_data()
    obj = data.get("obj")
    text = message.text.strip()

    if obj and text == ".":
        experience = obj.experience
    elif text.isdigit() and int(text) >= 0:
        experience = int(text)
    else:
        return await add_barber_experience_err(message, state)

    await state.update_data(experience=experience)
    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    specialization_name = BARBER_SPECIALIZATIONS.get(obj.specialization) if obj and obj.specialization else None

    msg_text = "📌 <b>Укажите специализацию барбера</b> 🧭"
    if specialization_name:
        msg_text += f"\n(Текущая: <code>{specialization_name}</code>, нажмите любую другую или отправьте)"

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text=msg_text,
        reply_markup=get_callback_btns(btns={
            "💈 Классический барбер": "classic_barber",
            "🧔‍♂️ Бородист": "beard_specialist",
            "🎨 Стайлист": "stylist_barber",
            "🎯 Барбер-универсал": "universal_barber",
            "❌ Отмена": "cancel_admin"
        }),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddBarbers.specialization)


# Ошибка, если формат продолжительности неверный
@admin_private_router.message(AddBarbers.experience)
async def add_barber_experience_err(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ Введите корректный опыт работы (только целое число, например <code>3</code>):",
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=sent_message.message_id)


@admin_private_router.callback_query(AddBarbers.specialization, F.data)
async def add_admin_specialization(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await delete_last_message(callback_query, await state.get_data())
    await state.update_data(specialization=callback_query.data)

    data = await state.get_data()
    obj = data.get("obj")

    text = (
        "📸 Пришлите новое фото барбера (или отправьте \".\" чтобы оставить текущее) 🖼️"
        if obj else
        "📸 Пришлите фото барбера (или отправьте \".\" чтобы пропустить) 🖼️"
    )

    sent_message = await callback_query.message.bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=text,
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddBarbers.photo)
    await callback_query.answer()

@admin_private_router.message(AddBarbers.photo)
async def add_barber_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    obj = data.get("obj")

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    photo_path = None

    if message.text and message.text.strip() == ".":
        photo_path = obj.photo_path if obj else None
    elif message.photo:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        photo_bytes = await message.bot.download_file(file.file_path)

        import os
        os.makedirs("barber_photos", exist_ok=True)
        photo_path = f"barber_photos/{message.from_user.id}_{photo.file_unique_id}.jpg"
        with open(photo_path, "wb") as f:
            f.write(photo_bytes.getvalue())
    else:
        sent = await message.bot.send_message(
            chat_id=message.chat.id,
            text="⚠️ Пришлите фото или отправьте \".\" для пропуска.",
            reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=sent.message_id)
        return

    await state.update_data(photo_path=photo_path)

    # Переход дальше
    if obj:
        sent = await message.bot.send_message(
            chat_id=message.chat.id,
            text="Выберите действие с графиком барбера:",
            reply_markup=get_callback_btns(btns={
                "✏️ Изменить график": "edit_schedule",
                "✅ Оставить как есть": "keep_schedule"
            })
        )
        await state.update_data(last_msg_id=sent.message_id)
        await state.set_state(AddBarbers.schedule_action)
    else:
        sent = await message.bot.send_message(
            chat_id=message.chat.id,
            text="<b>📅 Составление графика работы</b>\n\nВыберите дни недели, в которые барбер будет работать.",
            reply_markup=get_weekday_selection_kb_admin(),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent.message_id)
        await state.set_state(AddBarbers.work_days)





@admin_private_router.callback_query(AddBarbers.work_days)
async def handle_day_selection(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    data_btn = callback_query.data
    data = await state.get_data()

    await delete_last_message(callback_query, data)

    if data_btn == "cancel_admin":
        await state.clear()
        await callback_query.answer()
        sent = await callback_query.message.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="Выберите нужное действие:",
            reply_markup=get_main_inlineBtns_admin()
        )
        await state.update_data(last_msg_id=sent.message_id)
        return

    if data_btn.startswith("day_"):
        weekday = int(data_btn.split("_")[1])
        await state.update_data(current_weekday=weekday)

        sent = await callback_query.message.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"🕒 <b>Введите рабочее время для {WEEKDAY_LABELS[weekday]}</b> (например, 10:00-19:00):",
            reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent.message_id)
        await state.set_state(AddBarbers.work_time_input)
        await callback_query.answer()
        return

    elif data_btn == "weekday_selection_done":
        schedule = data.get("work_schedule", {})

        if not schedule:
            await callback_query.answer("Вы не выбрали ни одного дня!", show_alert=True)
            return

        obj = data.get("obj")
        if obj:
            # Редактирование существующего барбера
            await orm_update_barber_info(data, session)
            await orm_update_barber_schedule(session, obj.id, schedule)

            await orm_log_admin_action(
                session=session,
                admin_id=callback_query.from_user.id,
                action="Редактирование барбера",
                description=f"Обновлён барбер: {data['name']}, телефон: {data['phone']}, опыт: {data['experience']}, ID: {obj.id}"
            )

            message = f"✅ Барбер <b>{data['name']}</b> успешно обновлён!\n\n"
        else:
            # Добавление нового барбера
            barber_id, message = await orm_add_barber(data, session)
            await state.update_data(barber_id=barber_id)
            await orm_save_barber_schedule(session, barber_id, schedule)

            if barber_id:
                await orm_log_admin_action(
                    session=session,
                    admin_id=callback_query.from_user.id,
                    action="Добавление барбера",
                    description=f"Добавлен барбер: {data['name']}, телефон: {data['phone']}, опыт: {data['experience']}, ID: {barber_id}"
                )
            else:
                await orm_log_admin_action(
                    session=session,
                    admin_id=callback_query.from_user.id,
                    action="Попытка добавить барбера",
                    description=f"Барбер с именем '{data['name']}' и номером '{data['phone']}' уже существует."
                )

        # Формируем текст с графиком
        message += "<b>График работы барбера:</b>\n\n"
        for day, time in sorted(schedule.items()):
            message += f"📅 {WEEKDAY_LABELS[day]} — {time}\n"

        message += "\nЧто вы хотите сделать со списком барберов?"

        sent = await callback_query.message.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=message,
            reply_markup=get_barbers_list_what_do_inline(),
            parse_mode="HTML"
        )
        
        await state.clear()
        await state.update_data(last_msg_id=sent.message_id)
        await callback_query.answer()



@admin_private_router.message(AddBarbers.work_time_input)
async def input_time(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if not re.match(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$", text):
        await delete_last_message(message, await state.get_data())
        await message.delete()

        sent_msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text="⚠️ Неверный формат! Введите как: <code>10:00-18:00</code>",
            reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent_msg.message_id)
        return

    data = await state.get_data()
    weekday = data.get("current_weekday")
    schedule = data.get("work_schedule", {})
    schedule[weekday] = text
    await state.update_data(work_schedule=schedule)

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    schedule_lines = ""
    for day, time in sorted(schedule.items()):
        schedule_lines += f"📅 {WEEKDAY_LABELS[day]} — {time}\n"

    if not schedule_lines:
        schedule_lines = "⏳ Пока ничего не выбрано."

    final_text = (
        "<b>✅ Выберите следующий день или нажмите ✅ Готово:</b>\n\n"
        "<b>Ваш текущий график:</b>\n"
        f"{schedule_lines}"
    )

    sent_msg = await message.bot.send_message(
        chat_id=message.chat.id,
        text=final_text,
        reply_markup=get_weekday_selection_kb_admin(),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=sent_msg.message_id)
    await state.set_state(AddBarbers.work_days)





# Вывод списка с барберами

@admin_private_router.callback_query(AdminBarbersListCallback.filter())
async def admin_barbers_list_menu(callback_query: CallbackQuery, state: FSMContext,  callback_data: AdminBarbersListCallback, session: AsyncSession):
    data = await state.get_data()
    await delete_last_message(callback_query, data)
    if callback_data.name_btn == "delete":
        barber = await orm_get_barber_by_id(session, callback_data.barber_id)
        if not barber:
            await callback_query.answer("⚠️ Барбер не найден!", show_alert=True)
            return

        text = (
            f"⚠️ <b>Вы уверены, что хотите удалить барбера:</b> <code>{barber.name}</code>?\n"
            f"Это действие необратимо."
        )

        sent_message = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text,
            kb=get_confirm_delete_barber_kb(barber.id)
        )
        
        await state.update_data(last_msg_id=sent_message.message_id)
        await callback_query.answer()
        return
    
    
    if callback_data.name_btn == 'edit':
        obj = await orm_get_barber_by_id(session, callback_data.barber_id)
        await state.update_data(obj=obj)
        text = (
            f"✏️ Введите имя барбера, текущее: <b>{obj.name}</b> "
            "(Отправьте <code>.</code>, чтобы оставить) 📝📝📝"
        )
        sent_message = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text,
            kb=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
        )
        
        await state.set_state(AddBarbers.name)
        await state.update_data(last_msg_id=sent_message.message_id)
        await callback_query.answer()
        return

    if callback_data.name_btn == "unlink_service":
        services = await orm_get_services_by_barber_id(session, callback_data.barber_id)

        if not services:
            await callback_query.answer("❌ Услуги не привязаны.")
            return

        text = "<b>Выберите номер услуги для удаления связи:</b>\n\n"
        for i, service in enumerate(services, start=1):
            text += f"{i}. {service.service_name} ({service.service_duration} мин — {round(service.service_price, 2)}₽)\n"

        await state.update_data(barber_id=callback_data.barber_id, services=services)

        sent_msg = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text + "\nОтправьте номер услуги, которую хотите отвязать.",
            kb=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
        )

        await state.set_state(UnlinkServiceState.choosing_service)
        await state.update_data(last_msg_id=sent_msg.message_id)
        await callback_query.answer()
        return

    barbers = await orm_get_all_barbers(session)
    paginator = Paginator(barbers, page=callback_data.page)

    
    
    if not paginator.get_page():
        await callback_query.answer("⚠️ Барберов не найдено.")
        return

    barber = paginator.get_page()[0]
    rating_text = format_rating(barber.rating_sum, barber.rating_count)
    text = (
    f"<b>👤 Имя барбера:</b> {barber.name}\n"
    f"📞 <b>Телефон:</b> <code>{barber.phone}</code>\n"
    f"💼 <b>Стаж:</b> {plural_years(barber.experience)}\n"
    f"🎯 <b>Специализация:</b> {BARBER_SPECIALIZATIONS[barber.specialization]}\n"
    f"⭐️ <b>{rating_text}</b>\n"
)
    # Получение расписания барбера
    schedule = await orm_get_barber_schedule_by_id(session, barber.id)
    if schedule:
        text += "\n<b>📅 График работы:</b>\n"
        for weekday in sorted(schedule):
            start, end = schedule[weekday]
            text += f"• {WEEKDAY_LABELS[weekday]} — {start.strftime('%H:%M')}–{end.strftime('%H:%M')}\n"
    else:
        text += "\n📅 <i>График не задан</i>\n"
    text+= f"\n<b>🔢 Барбер {paginator.page} из {paginator.pages}</b>"
    kbds = get_barbers_list_btns_admin(
        page=callback_data.page,
        pagination_btns=pages(paginator),
        barber_id=barber.id
    )
    # Получегие услуг с с котрыми связан этот барбер
    services = await orm_get_services_by_barber_id(session, barber.id)
    if services:
        text += "\n<b>🛠 Услуги барбера:</b>\n"
        for service in services:
            text += f"• {service.service_name} — {service.service_price:.0f}₽ ({service.service_duration} мин)\n"
    else:
        text += "\n🛠 <i>Услуги не связаны</i>\n"

    # Удаляем старое сообщение и отправляем новое
    await delete_last_message(callback_query, await state.get_data())
    
    if barber.photo_path:
        sent = await callback_query.bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=FSInputFile(barber.photo_path),
            caption=text,
            reply_markup=kbds,
            parse_mode="HTML"
        )
    else:
        sent = await callback_query.bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=text,
            reply_markup=kbds,
            parse_mode="HTML"
        )
    
    await state.update_data(last_msg_id=sent.message_id)
    await callback_query.answer()



@admin_private_router.callback_query(F.data.startswith("confirm_delete_barber_"))
async def confirm_delete_barber(callback_query: CallbackQuery, session: AsyncSession):
    barber_id = int(callback_query.data.split("_")[-1])

    barber = await orm_get_barber_by_id(session, barber_id)
    if not barber:
        await callback_query.answer("⚠️ Барбер не найден!", show_alert=True)
        return

    deleted_name = await orm_delete_barber_by_id(session, barber_id)

    await orm_log_admin_action(
        session=session,
        admin_id=callback_query.from_user.id,
        action="Удаление барбера",
        description=f"Удален барбер: {barber.name}, ID: {barber.id}, Телефон: {barber.phone}"
    )

    await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=f"✅ Барбер <b>{deleted_name}</b> успешно удалён.\n\nЧто вы хотите сделать со списком барберов?",
        kb=get_barbers_list_what_do_inline()
    )

    await callback_query.answer()






# Состояния для выбора номера услуги
@admin_private_router.message(UnlinkServiceState.choosing_service)
async def unlink_service_from_barber(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    services = data.get("services", [])
    barber_id = data.get("barber_id")
    barber = await orm_get_barber_by_id(session, barber_id)

    try:
        index = int(message.text.strip()) - 1
        if not (0 <= index < len(services)):
            raise ValueError
    except ValueError:
        await delete_last_message(message, data)
        await message.delete()
        sent = await message.answer(
            "⚠️ Пожалуйста, введите корректный номер услуги.",
            reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=sent.message_id)
        return

    service = services[index]

    await orm_unlink_service_from_barber(session, barber_id, service.id)
    await orm_log_admin_action(
        session=session,
        admin_id=message.from_user.id,
        action="Удаление связи услуги с барбером",
        description=f"Связь услуги и барбера удалена: Барбер - {barber.name}, услуга - {service.service_name}."
    )

    await delete_last_message(message, data)
    await message.delete()
    await state.clear()

    sent = await message.answer(
        f"✅ Услуга <b>{service.service_name}</b> успешно удалена у барбера.\n"
        "Что вы хотите сделать со списком барберов?",
        reply_markup=get_barbers_list_what_do_inline(),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=sent.message_id)



# Что сделать с графиком работы отредактировать или оставить при редактировании барбера
@admin_private_router.callback_query(AddBarbers.schedule_action)
async def handle_schedule_action(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    action = callback_query.data
    data = await state.get_data()

    await delete_last_message(callback_query, data)

    if action == "edit_schedule":
        sent = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text="<b>📅 Составление графика работы</b>\n\nВыберите дни недели, в которые барбер будет работать.",
            kb=get_weekday_selection_kb_admin()
        )
        await state.update_data(last_msg_id=sent.message_id)
        await state.set_state(AddBarbers.work_days)
        await callback_query.answer()
        return

    if action == "keep_schedule":
        obj = data.get("obj")
        state_data = await state.get_data()
        if obj:
            sent = await safe_edit_or_send_new(
                bot=callback_query.bot,
                message=callback_query.message,
                text=f"✅ Данные барбера обновлены: {obj.name}\nЧто вы хотите сделать со списком барберов?",
                kb=get_barbers_list_what_do_inline()
            )
            
            await orm_log_admin_action(
                session=session,
                admin_id=callback_query.from_user.id,
                action="Редактирование барбера",
                description=f"Барбер отредактирован без изменения графика: {obj.name}, ID: {obj.id}"
            )
        await orm_update_barber_info(state_data, session)
        await state.clear()
        await state.update_data(last_msg_id=sent.message_id)
        await callback_query.answer()













# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Выбор что сделать с сервисами
@admin_private_router.callback_query(F.data == "edit_servisec_what_do")
async def edit_servisec_what_do(callback_query: CallbackQuery,state:FSMContext, session: AsyncSession):
    await callback_query.answer()
    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="Что вы хотите сделать со списком сервисов?",
        kb=get_callback_btns(btns={
            "➕ Добавить": "add_services",
            "📜 Список": "admin_services_list",
            "🔙 Назад": "cancel_admin"
        })
    )
    await state.update_data(last_msg_id=sent_message.message_id)
# Стартовая команда для добавления услуги в бд
@admin_private_router.callback_query(F.data == "add_services")
async def add_service(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback_query.answer()
    await delete_last_message(callback_query, await state.get_data())
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    text = (
        "🆕 <b>Добавление новой услуги</b>\n\n"
        "✏️ Введите <b>название услуги</b>:\n"
        "<i>Например: Стрижка мужская</i>"
    )

    sent_message = await callback_query.bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=text,
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.update_data(obj=None)
    await state.set_state(AddService.name)





# Добавление/редактирование наименования услуги
@admin_private_router.message(AddService.name, F.text)
async def add_service_name(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    obj = data.get("obj")

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    if obj and message.text.strip() == ".":
        name = obj.service_name
    else:
        name = message.text.strip()

    await state.update_data(name=name)

    if obj:
        text = (
            f"💰 <b>Изменение цены услуги</b>\n\n"
            f"Текущее значение: <b>{round(obj.service_price, 2)} руб.</b>\n"
            "✏️ Введите <b>новую цену</b> или отправьте <code>.</code> чтобы оставить без изменений."
        )
    else:
        text = (
            "💰 <b>Установка цены услуги</b>\n\n"
            "✏️ Введите <b>стоимость услуги</b> в рублях.\n"
            "<i>Например: 1200</i>"
        )

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddService.price)


# Оброботчик ошибки если формат неверный
@admin_private_router.message(AddService.name)
async def add_service_name_err(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ Неверный формат данных. Введите текст для наименования услуги.\n\n✏️ Попробуйте снова:",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)


# Добавление стоимости услуги
@admin_private_router.message(AddService.price, F.text)
async def add_service_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    obj = data.get("obj")

    if obj and message.text.strip() == ".":
        price = obj.service_price
    elif message.text.strip().isdigit():
        price = int(message.text.strip())
    else:
        return await add_service_price_err(message, state)

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(price=price)

    if obj:
        await state.update_data(duration=obj.service_duration)
        service_name = SERVICE_CATEGORIES_REVERSED.get(obj.service_category) if obj.service_category else None

        msg_text = "📌 Укажите категорию услуги:"
        if service_name:
            msg_text += f"\n(Текущая: {service_name}, нажмите любую другую или оставьте как есть)"

        sent_message = await message.bot.send_message(
            chat_id=message.chat.id,
            text=msg_text,
            reply_markup=get_callback_btns(btns={
                "✂️ Стрижки": "haircut",
                "🧔 Борода и бритьё": "beard",
                "💆‍♂️ Уход за волосами и кожей": "care",
                "🎭 Стайлинг": "styling",
                "🎟 Комплексные услуги": "combo",
                "🔙 Отмена": "cancel_admin"
            }),
            parse_mode="HTML"
        )

        await state.update_data(last_msg_id=sent_message.message_id)
        await state.set_state(AddService.category)
        return

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="⏳ Введите продолжительность услуги в минутах:",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddService.duration)



# Ошибка, если формат цены неверный
@admin_private_router.message(AddService.price)
async def add_service_price_err(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ Введите корректную цену (только цифры, например 500):",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)



# Добавление продолжительности услуги
@admin_private_router.message(AddService.duration, F.text)
async def add_service_duration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()

    if not text.isdigit():
        return await add_service_duration_err(message, state)

    duration = int(text)
    await state.update_data(duration=duration)

    await delete_last_message(message, data)
    try:
        await message.delete()
    except Exception:
        pass

    msg_text = "📌 Укажите категорию услуги:"

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text=msg_text,
        reply_markup=get_callback_btns(btns={
            "✂️ Стрижки": "haircut",
            "🧔 Борода и бритьё": "beard",
            "💆‍♂️ Уход за волосами и кожей": "care",
            "🎭 Стайлинг": "styling",
            "🎟 Комплексные услуги": "combo",
            "🔙 Отмена": "cancel_admin"
        }),
        parse_mode="HTML"
    )

    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddService.category)



# Ошибка, если формат продолжительности неверный
@admin_private_router.message(AddService.duration)
async def add_service_duration_err(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())
    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.bot.send_message(
        chat_id=message.chat.id,
        text="❌ Введите корректную продолжительность (только целое число, например 30):",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"}),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=sent_message.message_id)



# Добавление категории услуги и занесение в базу данных
@admin_private_router.callback_query(AddService.category, F.data)
async def add_admin_service_category(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback_query.answer()
    await delete_last_message(callback_query, await state.get_data())
    try:
        await callback_query.message.delete()
    except Exception:
        pass

    await state.update_data(category=callback_query.data)
    await state.update_data(actor_id=callback_query.from_user.id)

    data = await state.get_data()

    if data.get("obj"):  # Редактирование существующей услуги
        message_text = await orm_update_service(data, session)

        await orm_log_admin_action(
            session=session,
            admin_id=data["actor_id"],
            action="Обновление услуги",
            description=(
                f"Услуга обновлена: "
                f"название — {data['name']}, "
                f"цена — {data['price']}, "
                f"длительность — {data['duration']}, "
                f"категория — {SERVICE_CATEGORIES_REVERSED[data['category']][2:]}"
            )
        )
    else:  # Добавление новой услуги
        message_text = await orm_add_service(data, session)
        if message_text:
            await orm_log_admin_action(
                session=session,
                admin_id=callback_query.from_user.id,
                action="Добавление услуги",
                description=(
                    f"Услуга добавлена: "
                    f"{data['name']} — {data['price']}₽, "
                    f"{data['duration']} мин, "
                    f"категория — {SERVICE_CATEGORIES_REVERSED[data['category']][2:]}"
                )
            )

    sent_message = await callback_query.bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=message_text,
        reply_markup=get_callback_btns(btns={
            "➕ Добавить": "add_services",
            "📜 Список": "admin_services_list",
            "🔙 Назад": "cancel_admin"
        }),
        parse_mode="HTML"
    )

    
    await state.clear()
    await state.update_data(last_msg_id=sent_message.message_id)

    



# Список текущих услуг
@admin_private_router.callback_query(F.data == "admin_services_list")
async def admin_services_list(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback_query.answer()
    await delete_last_message(callback_query, await state.get_data())

    text, kbds = await get_admin_servives_list_content(session, level=0)
    sent = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=text,
        kb=kbds
    )
    await state.update_data(last_msg_id=sent.message_id)




# Отлавливает все уникальные калбеки ServiceslistCallBack
@admin_private_router.callback_query(AdminServicesListCallBack.filter())
async def admin_services_list_menu(callback_query: CallbackQuery, state: FSMContext, callback_data: AdminServicesListCallBack, session: AsyncSession):
    data = await state.get_data()
    await delete_last_message(callback_query, data)

    if callback_data.name_btn == "edit":
        obj = await orm_get_service_by_id(session, callback_data.service_id)
        await state.update_data(obj=obj)

        text = (
            f"✏️ Введите название услуги, текущее: <b>{obj.service_name}</b> "
            "(Отправьте <code>.</code> чтобы оставить) 📝📝📝"
        )

        sent = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text,
            kb=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
        )
        await state.set_state(AddService.name)
        await state.update_data(last_msg_id=sent.message_id)
        await callback_query.answer()
        return

    if callback_data.name_btn == "link_barber":
        barbers = await orm_get_all_barbers(session)
        if not barbers:
            await callback_query.answer("⚠️ Нет доступных барберов для выбора.", show_alert=True)
            return

        await state.update_data(barbers=barbers, service_id=callback_data.service_id)

        text = "<b>Выберите барбера для привязки к услуге:</b>\n\n"
        for i, barber in enumerate(barbers, start=1):
            text += f"{i}) {barber.name} (опыт: {barber.experience} лет)\n"

        sent = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text,
            kb=get_callback_btns(btns={"❌ Отмена": "cancel_admin"})
        )
        await state.set_state(AddService.select_barber_to_link)
        await state.update_data(last_msg_id=sent.message_id)
        await callback_query.answer()
        return

    # Получаем список услуг по категории и пагинации
    text, kbds = await get_admin_servives_list_content(
        session=session,
        level=callback_data.level,
        category=callback_data.service_category,
        page=callback_data.page,
        service_id=callback_data.service_id,
        name_btn=callback_data.name_btn,
        admin_id=callback_query.from_user.id
    )

    sent = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=text,
        kb=kbds
    )
    await state.update_data(last_msg_id=sent.message_id)
    await callback_query.answer()














# Вход в сосотяния выбора барбера для услуги
@admin_private_router.message(AddService.select_barber_to_link)
async def process_link_barber_to_service(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    barbers = data["barbers"]
    service_id = data["service_id"]
    admin_id = message.from_user.id

    # Удаляем сообщение пользователя (его ввод)
    try:
        await message.delete()
    except Exception:
        pass

    # Проверяем корректность номера
    try:
        index = int(message.text.strip()) - 1
        if not (0 <= index < len(barbers)):
            raise ValueError
    except ValueError:
        # Неверный ввод — удаляем старое меню и показываем новое с предупреждением
        await delete_last_message(message, data)

        text = (
            "⚠️ Введите корректный номер барбера.\n\n"
            "<b>Выберите барбера для привязки к услуге:</b>\n\n"
        )
        for i, barber in enumerate(barbers, start=1):
            text += f"{i}) {barber.name} (опыт: {barber.experience} лет)\n"

        sent = await message.bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=get_callback_btns(btns={"❌ Отмена": "cancel_admin"}),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent.message_id)
        return

    # Удаляем старое меню
    await delete_last_message(message, data)

    barber = barbers[index]
    service = await orm_get_service_by_id(session, service_id)
    service_name = service.service_name if service else "Неизвестная услуга"

    # Пробуем привязать
    try:
        check = await orm_link_barber_to_service(session, barber.id, service_id)
        if check:
            result_text = f"✅ Барбер <b>{barber.name}</b> теперь связан с услугой.\n"
            await orm_log_admin_action(
                session=session,
                admin_id=admin_id,
                action="Привязка барбера к услуге",
                description=(
                    f"Барбер: {barber.name} (ID: {barber.id}) успешно привязан к услуге: {service_name} (ID: {service_id})"
                )
            )
        else:
            result_text = f"🔴 Барбер <b>{barber.name}</b> уже связан с этой услугой!\n"
            await orm_log_admin_action(
                session=session,
                admin_id=admin_id,
                action="Повторная попытка привязки барбера",
                description=(
                    f"Барбер: {barber.name} (ID: {barber.id}) уже был связан с услугой: {service_name} (ID: {service_id})"
                )
            )
    except Exception as e:
        result_text = "❌ Произошла ошибка при связывании барбера с услугой."
        await orm_log_admin_action(
            session=session,
            admin_id=admin_id,
            action="Ошибка при привязке барбера",
            description=(
                f"Ошибка при привязке барбера: {barber.name} (ID: {barber.id}) к услуге: {service_name} (ID: {service_id}). "
                f"Ошибка: {str(e)}"
            )
        )

    # Загружаем обновлённый список услуг
    list_text, kbds = await get_admin_servives_list_content(session, level=0)
    final_text = result_text + list_text

    sent = await message.bot.send_message(
        chat_id=message.chat.id,
        text=final_text,
        reply_markup=kbds,
        parse_mode="HTML"
    )
    
    await state.clear()
    await state.update_data(last_msg_id=sent.message_id)
















# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Журнал действий
@admin_private_router.callback_query(F.data == "list_admin")
async def list_admin_logs(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AdminLogFSM.waiting_for_start_date)
    msg = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="📅 Укажите начальную дату (ГГГГ-ММ-ДД):",
        kb=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=msg.message_id, admin_log_msg_ids=[msg.message_id])
    await callback_query.answer()





@admin_private_router.message(AdminLogFSM.waiting_for_start_date)
async def select_start_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await delete_last_message(message, data)

    try:
        start_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        await state.update_data(start_date=start_date)

        try:
            await message.delete()
        except Exception:
            pass

        msg = await safe_edit_or_send_new(
            bot=message.bot,
            message=message,
            text="📅 Укажите конечную дату (ГГГГ-ММ-ДД):",
            kb=get_callback_btns(btns={"Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=msg.message_id)
        await state.set_state(AdminLogFSM.waiting_for_end_date)

    except ValueError:
        try:
            await message.delete()
        except Exception:
            pass

        msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text="❌ Неверный формат. Попробуйте снова: ГГГГ-ММ-ДД",
            reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=msg.message_id)






@admin_private_router.message(AdminLogFSM.waiting_for_end_date)
async def select_end_date(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await delete_last_message(message, data)

    try:
        end_date = datetime.strptime(message.text.strip(), "%Y-%m-%d")
        start_date = data.get("start_date")

        try:
            await message.delete()
        except Exception:
            pass

        logs = await orm_get_admin_logs(session, start_date, end_date)
        if not logs:
            msg = await message.bot.send_message(
                chat_id=message.chat.id,
                text="📭 Логи не найдены.",
                reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
            )
            await state.update_data(last_msg_id=msg.message_id)
            return

        paginator = Paginator(logs, page=1, per_page=10)

        msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text="Загрузка логов...",
        )
        await state.update_data(admin_log_msg_ids=[msg.message_id])

        await show_log_page(msg, state, paginator)

        await state.set_state(AdminLogFSM.viewing_logs)
        await state.update_data(
            paginator=paginator,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError:
        try:
            await message.delete()
        except Exception:
            pass

        msg = await message.bot.send_message(
            chat_id=message.chat.id,
            text="❌ Неверный формат. Попробуйте снова: ГГГГ-ММ-ДД",
            reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=msg.message_id)


@admin_private_router.callback_query(AdminLogFSM.viewing_logs, F.data.in_({"previous", "next"}))
async def paginate_logs(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    paginator: Paginator = data.get("paginator")

    if callback_query.data == "next" and paginator.has_next():
        paginator.page += 1
    elif callback_query.data == "previous" and paginator.has_previous():
        paginator.page -= 1

    await state.update_data(paginator=paginator)
    await show_log_page(callback_query.message, state, paginator)
    await callback_query.answer()






async def show_log_page(message_or_obj, state: FSMContext, paginator: Paginator):
    logs = paginator.get_page()
    data = await state.get_data()

    text = f"📘 Журнал действий (стр. {paginator.page} из {paginator.pages}):\n\n"
    for log in logs:
        text += (
            f"🕓 {log.timestamp.strftime('%d.%m.%Y %H:%M')}\n"
            f"👤 {log.admin_name} | 🛠 {log.action}\n"
            f"📄 {log.description}\n\n"
        )

    nav_buttons = pages(paginator)
    nav_buttons["Отмена"] = "cancel_admin"
    keyboard = get_callback_btns(btns=nav_buttons)

    msg_id = data.get("admin_log_msg_ids", [None])[0]
    if msg_id:
        try:
            await message_or_obj.bot.edit_message_text(
                chat_id=message_or_obj.chat.id,
                message_id=msg_id,
                text=text[:4096],
                reply_markup=keyboard
            )
        except Exception:
            sent = await message_or_obj.bot.send_message(
                chat_id=message_or_obj.chat.id,
                text=text[:4096],
                reply_markup=keyboard
            )
            await state.update_data(admin_log_msg_ids=[sent.message_id])
    else:
        sent = await message_or_obj.bot.send_message(
            chat_id=message_or_obj.chat.id,
            text=text[:4096],
            reply_markup=keyboard
        )
        await state.update_data(admin_log_msg_ids=[sent.message_id])





# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ 
# Реализация команд для добавления или удаления админа

@admin_private_router.callback_query(F.data == "edit_admin_list")
async def edit_admins(callback_query: CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query, await state.get_data())
    await callback_query.answer()

    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="Выберите нужное действие", 
        kb=get_callback_btns(btns={
            "➕ Добавить админа": "add_admin",
            "❌ Удалить админа": "delete_admin",
            "📜 Список админов": "admin_list",
            "🔙 Отмена": "cancel_admin"
        })
    )
    await state.update_data(last_msg_id=sent_message.message_id)


# Начало состояния добавления админа
# Добавление админа (запрос имени)

@admin_private_router.callback_query(F.data == "add_admin")
async def add_admin(callback_query: CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query, await state.get_data())
    await callback_query.answer()
    await delete_last_message(callback_query, await state.get_data())

    sent_message = await callback_query.message.answer("Введите имя администратора 📝📝📝",reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"}))
    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(AddAdmin.name)




# Добавление имени администратора
@admin_private_router.message(AddAdmin.name, F.text)
async def add_admin_name(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())

    await state.update_data(name=message.text.strip())

    sent_message = await message.answer(
        "Введите ID администратора 📝📝📝",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)

    try:
        await message.delete()
    except Exception:
        pass

    await state.set_state(AddAdmin.admin_id)

# В случае если пользователь ввел неверное имя
@admin_private_router.message(AddAdmin.name)
async def add_admin_invalid_name(message: types.Message, state: FSMContext):
    await delete_last_message(message, await state.get_data())

    try:
        await message.delete()
    except Exception:
        pass

    sent_message = await message.answer(
        "❌ Введён неверный формат. Введите текст.",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)


# Обработка ID администратора
@admin_private_router.message(AddAdmin.admin_id, F.text)
async def add_admin_id(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    if not message.text.strip().isdigit():
        await delete_last_message(message, data)

        sent_message = await message.answer(
            "❌ ID должен содержать только цифры. Попробуйте снова.",
            reply_markup=get_callback_btns(btns={"Отмена": "cancel_admin"})
        )
        await state.update_data(last_msg_id=sent_message.message_id)

        try:
            await message.delete()
        except Exception:
            pass

        return

    await state.update_data(admin_id=message.text.strip())
    data = await state.get_data()

    await delete_last_message(message, data)

    try:
        await message.delete()
    except Exception:
        pass

    await state.clear()

    res = await orm_add_admin_to_db(
        admin_id=int(data['admin_id']),
        admin_name=data['name'],
        actor_id=message.from_user.id,
        session=session
    )

    if res:
        await orm_log_admin_action(
            session=session,
            admin_id=message.from_user.id,
            action="Добавление администратора",
            description=f"Добавлен администратор: ID — {data['admin_id']}, Имя — {data['name']}"
        )

        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f'''✅ Администратор добавлен!
Имя: <strong>{data['name']}</strong>
ID: <strong>{data['admin_id']}</strong>

🔙 Возвращение в главное меню:''',
            reply_markup=get_main_inlineBtns_admin(),
            parse_mode="HTML"
        )
    else:
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f'''❌ Администратор уже существует!
Имя: <strong>{data['name']}</strong>
ID: <strong>{data['admin_id']}</strong>

🔙 Возвращение в главное меню:''',
            reply_markup=get_main_inlineBtns_admin(),
            parse_mode="HTML"
        )








# Начало состояния для удаленя админа
@admin_private_router.callback_query(F.data == "delete_admin")
async def delete_admin(callback_query: CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query, await state.get_data())
    await callback_query.answer()

    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text="Введите ID администратора 📝",
        kb=get_callback_btns(btns={"Отмена": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(DeleteAdmin.admin_id)


# Для полученя id удаляемого админа
@admin_private_router.message(DeleteAdmin.admin_id, F.text)
async def delete_admin_id(message: types.Message, state: FSMContext, session: AsyncSession):
    await delete_last_message(message, await state.get_data())

    admin_id = message.text.strip()
    await state.update_data(admin_id=admin_id)

    try:
        await message.delete()
    except Exception:
        pass

    admin_name = await orm_get_admin_name_by_id(admin_id, session)

    if admin_name is None:
        sent_message = await message.answer(
            "⚠️ <b>Администратор с таким ID не найден!</b>\n\n"
            "Проверьте корректность ID и выберите действие:",
            reply_markup=get_callback_btns(btns={
                "➕ Добавить админа": "add_admin",
                "❌ Удалить админа": "delete_admin",
                "📜 Список админов": "admin_list",
                "🔙 Отмена": "cancel_admin"
            }),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent_message.message_id)
        await state.clear()
        return

    await state.update_data(admin_name=admin_name)

    sent_message = await message.answer(
        f"✅ <b>Администратор {admin_name} (ID: {admin_id}) найден!</b>\n"
        "Вы действительно хотите его удалить?",
        reply_markup=get_callback_btns(btns={
            "✔️ Подтвердить удаление": f"confirm_delete_admin_{admin_id}",
            "🔙 Отмена": "cancel_admin"
        }),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=sent_message.message_id)
    await state.set_state(DeleteAdmin.correct)


@admin_private_router.callback_query(DeleteAdmin.correct, F.data.startswith("confirm_delete_admin_"))
async def delete_admin_from_db(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await delete_last_message(callback_query, await state.get_data())
    data = await state.get_data()

    del_admin = await orm_del_admin_by_id(
        admin_id=int(data["admin_id"]),
        session=session
    )

    await callback_query.answer()

    if del_admin:
        await orm_log_admin_action(
            session=session,
            admin_id=callback_query.from_user.id,
            action="Удаление администратора",
            description=(
                f"Удалён администратор: ID — {data['admin_id']}, "
                f"Имя — {data['admin_name']}"
            )
        )

        sent_message = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=(
                f"✅ <b>Администратор {data['admin_name']} (ID: {data['admin_id']}) успешно удалён!</b>\n\n"
                "Выберите следующее действие:"
            ),
            kb=get_main_inlineBtns_admin()
        )
        await state.update_data(last_msg_id=sent_message.message_id)
    else:
        sent_message = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=(
                f"❌ <b>Не удалось удалить администратора {data['admin_name']} (ID: {data['admin_id']}).</b>\n\n"
                "Попробуйте позже или выберите другое действие:"
            ),
            kb=get_main_inlineBtns_admin()
        )
        await state.update_data(last_msg_id=sent_message.message_id)

    await state.clear()






# Команда для вывода всех администраторов
@admin_private_router.callback_query(F.data == "admin_list")
async def get_admins_list_cmd(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    await delete_last_message(callback_query, await state.get_data())
    await callback_query.answer()

    admin_list_text = await get_admins_list(session)

    sent_message = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=admin_list_text,
        kb=get_callback_btns(btns={
            "Назад": "edit_admin_list"
        })
    )
    await state.update_data(last_msg_id=sent_message.message_id)






# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



# Команда что бы вернутсья в главное меню
@admin_private_router.callback_query(F.data == "exit_admin")
async def back_main_menu(callback_query: CallbackQuery, state: FSMContext):
    main_menu_text = (
        "<b>🏠 Главное меню</b>\n\n"
        "✅ Выберите одно из действий ниже:\n")
    await callback_query.answer()

    try:
        await callback_query.message.delete()
    except Exception as e:
        logging.warning(f"Ошибка при удалении сообщения при выходе из админки: {e}")
        await callback_query.message.answer(main_menu_text,reply_markup= get_main_inlineBtns_user())
    await state.clear()


# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\


# Руководство пользователя вывод
@admin_private_router.callback_query(F.data == "anagement")
async def show_user_guide(callback_query: CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query, await state.get_data())
    await callback_query.answer()

    text = (
        "📕 <b>Руководство администратора</b> 📕\n\n"
        "👋 Добро пожаловать в админ-панель Telegram-бота для записи клиентов.\n\n"
        "🔧 <b>Пошаговая настройка:</b>\n"
        "1️⃣ Зайдите в раздел <b>✏️ Редактировать</b>.\n"
        "2️⃣ Добавьте <b>барберов</b> — с расписанием и фото.\n"
        "3️⃣ Добавьте <b>услуги</b> — укажите цену и длительность.\n"
        "4️⃣ Свяжите услуги и барберов — кто что выполняет.\n"
        "5️⃣ Проверьте все данные перед запуском.\n\n"
        "📋 <b>Основное меню администратора:</b>\n"
        "➕ <b>Записать</b> — вручную записать клиента с именем и телефоном.\n"
        "📝 <b>Записи</b> — просмотр и удаление записей (если клиент отменяет по звонку).\n"
        "✏️ <b>Редактировать</b> — управление барберами, услугами, их связями и расписанием.\n"
        "📜 <b>Журнал</b> — история всех действий администраторов с выбором периода.\n"
        "🔧 <b>Админы</b> — управление доступом администраторов.\n"
        "📕 <b>Руководство</b> — это подробное описание.\n\n"
        "❗️ <b>Важно:</b> после изменений проверяйте актуальность данных. Все изменения видны в журнале.\n\n"
        "⚠️ <b>Важно:</b> если планируете удалить барбера, обязательно заранее запишите все данные о его записях, "
        "так как после удаления их нельзя будет просмотреть через бота."
    )

    sent = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=text,
        kb=get_callback_btns(btns={"⬅️ Назад": "cancel_admin"})
    )
    await state.update_data(last_msg_id=sent.message_id)










# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\






# @admin_private_router.callback_query(StateFilter("*"), F.data == "cancel_admin")
# async def cancel_admin(callback_query: CallbackQuery, state: FSMContext):  
#     await state.clear()
#     await callback_query.answer()

#     try:
#         sent_message = await callback_query.message.edit_text(
#             "Выберете нужное действие:",
#             reply_markup=get_main_inlineBtns_admin()
#         )
#     except TelegramBadRequest:
#         await callback_query.message.delete()
#         sent_message = await callback_query.message.answer(
#             "Выберете нужное действие:",
#             reply_markup=get_main_inlineBtns_admin()
#         )

#     await state.update_data(last_msg_id=sent_message.message_id)


# Кнопка для отмены в адмнике
@admin_private_router.callback_query(F.data == "cancel_admin")
async def cancel_admin(callback_query: CallbackQuery, state: FSMContext):  
    await state.clear()
    await callback_query.answer()

    sent_message = None

    # 1. Попытка редактирования сообщения
    try:
        sent_message = await callback_query.message.edit_text(
            "Выберете нужное действие:",
            reply_markup=get_main_inlineBtns_admin()
        )
    except Exception as e:
        logging.warning(f"Не удалось отредактировать сообщение админа: {e}")

    # 2. Если редактирование не удалось — попытка удаления
    if sent_message is None:
        try:
            await callback_query.message.delete()
            logging.info("Сообщение админа успешно удалено перед отправкой нового.")
        except Exception as e:
            logging.warning(f"Не удалось удалить сообщение админа: {e}")

        # 3. В любом случае отправляем новое
        sent_message = await callback_query.message.answer(
            "Выберете нужное действие:",
            reply_markup=get_main_inlineBtns_admin()
        )

    # 4. Обновляем данные состояния
    await state.update_data(last_msg_id=sent_message.message_id)
    






    
# функция для удаления послежнего сообщения
async def delete_last_message(env, data):
    """
    Удаляет последнее сообщение с кнопками, если оно есть.
    Игнорирует любые ошибки (например, если сообщение слишком старое).
    """
    if "last_msg_id" not in data:
        return

    chat_id = env.message.chat.id if isinstance(env, CallbackQuery) else env.chat.id
    bot = env.bot if isinstance(env, CallbackQuery) else env._bot
    last_msg_id = data["last_msg_id"]

    try:
        await bot.delete_message(chat_id, last_msg_id)
        logging.info(f"Удалено сообщение: id={last_msg_id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение (id={last_msg_id}): {e}")




#
async def send_split_messages(state: FSMContext, text: str, chat_id: int, bot: Bot):
    max_length = 4096
    data = await state.get_data()
    message_ids = data.get("admin_log_msg_ids", [])
    for i in range(0, len(text), max_length):
        sent = await bot.send_message(chat_id=chat_id, text=text[i:i+max_length])
        message_ids.append(sent.message_id)
    await state.update_data(admin_log_msg_ids=message_ids)





async def safe_edit_or_send_new(
    bot: Bot,
    message: types.Message,
    text: str,
    photo_path: str | None = None,
    kb: types.InlineKeyboardMarkup | None = None
) -> types.Message:
    chat_id = message.chat.id

    # 1️⃣ Попытка редактировать
    try:
        if photo_path is None:
            return await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            # Для фото в Telegram нет edit_caption без фото — считаем фото новым
            raise Exception("Редактирование фото недопустимо — сразу переходим к отправке нового.")
    except Exception as e:
        logging.warning(f"Не удалось отредактировать сообщение (id={message.message_id}): {e}")

    # 2️⃣ Попытка удалить
    try:
        await message.delete()
        logging.info(f"Удалено старое сообщение (id={message.message_id})")
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение (id={message.message_id}): {e}")

    # 3️⃣ Отправляем новое сообщение
    if photo_path:
        try:
            photo_file = FSInputFile(photo_path)
            return await bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке фото: {e}")
            return await bot.send_message(
                chat_id=chat_id,
                text=f"{text}\n⚠️ Фото не загружено.",
                reply_markup=kb,
                parse_mode="HTML"
            )
    else:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )




    
