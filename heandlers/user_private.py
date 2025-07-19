from aiogram import  types , Router, F
from aiogram.filters import CommandStart,Command, or_f, StateFilter,and_f
from aiogram.fsm.state import StatesGroup,State
from aiogram.fsm.context import FSMContext
from aiogram.utils.formatting import as_list, as_marked_section, Bold
from aiogram.types import CallbackQuery,FSInputFile
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter


from kbds.inline_user import UserServiceslistCallBack,UserAddRecordCallBack,UserRateBarberCallback,UserRateDeclineCallback,UserRememberOkCallback,UserViewRecordsCallback, get_main_inlineBtns_user, get_callback_btns

from kbds.replay_user_kb import get_send_number_kb_user

from database.models import AppointmentStatus

from heandlers.user_services_list_processing import get_user_servives_list_content
from heandlers.user_view_records_processing import get_user_records_list

from heandlers.user_record_prcessing import get_add_record_menu_user

from database.orm_query import orm_add_barber_rating,orm_add_appointment_user,orm_get_service_by_id,orm_get_barber_by_id,orm_update_appointment_status,orm_check_daily_limit,orm_get_user_by_id,orm_add_user,orm_get_appointment_by_id,orm_check_rating_exists, orm_add_rating_decline

from datetime import datetime, timedelta

from fsm.user import UserRecordStates

from scheduler import schedule_reminder,schedule_rating_request


import logging



user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))







class StartStates(StatesGroup):
    waiting_for_contact = State()








# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# Стортовоые команды при начальной работе бота

@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    # Удаляем пользовательское /start
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"[START] Не удалось удалить сообщение: {e}")

    user = await orm_get_user_by_id(session, message.from_user.id)

    if user:
        sent = await message.answer(
            "👋 <b>Добро пожаловать обратно!</b>\n\nВыберите действие из меню ниже.",
            reply_markup=get_main_inlineBtns_user(),
            parse_mode="HTML"
        )
        await state.update_data(last_msg_id=sent.message_id)
        await state.clear()
    else:
        text = (
            "<b>👋 Привет!</b>\n\n"
            "Чтобы начать работу с ботом, пожалуйста, отправьте свой номер телефона, "
            "используя кнопку ниже.\n\n"
            "——————————————\n"
            "<i>«Пользуясь этим ботом, вы соглашаетесь на обработку персональных данных»</i>\n\n"
            "<b>Что мы храним:</b>\n"
            "• Имя пользователя\n"
            "• Номер телефона\n"
            "• Информация о записях\n\n"
            "<b>Зачем:</b>\n"
            "• Для оформления записи\n"
            "• Для напоминания о визите\n\n"
            "<b>Важно:</b>\n"
            "• Данные не передаются третьим лицам\n"
            "• Для удаления или изменения данных — свяжитесь с администратором"
        )

        sent = await message.answer(
            text,
            reply_markup=get_send_number_kb_user(),
            parse_mode="HTML"
        )
        await state.set_state(StartStates.waiting_for_contact)
        await state.update_data(last_msg_id=sent.message_id)


@user_private_router.message(StartStates.waiting_for_contact, F.contact)
async def process_contact(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"[CONTACT] Не удалось удалить сообщение: {e}")

    data = await state.get_data()

    # Удаляем приветственный текст с кнопкой
    await delete_last_message(message, data)

    # Сохраняем пользователя
    try:
        await orm_add_user(
            session=session,
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            phone=str(message.contact.phone_number).replace("+", "")
        )
    except Exception:
        err = await message.answer("❌ Ошибка при сохранении данных. Попробуйте позже.")
        await state.update_data(last_msg_id=err.message_id)
        return
    
    sent = await message.answer(
        "✅ Спасибо, регистрация завершена!\n\n"
        "📌 Вы можете:\n"
        "➕ записаться на услуги\n"
        "📋 просматривать свои записи\n"
        "🏠 ознакомиться с нашими услугами\n"
        "📞 обратиться в техподдержку\n"
        "ℹ️ и узнать больше о нас!",
        reply_markup=get_main_inlineBtns_user()
    )
    await state.update_data(last_msg_id=sent.message_id)
    await state.clear()

# Если пользователь ввёл что-то не то
@user_private_router.message(StartStates.waiting_for_contact)
async def handle_invalid_contact(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except Exception as e:
        logging.warning(f"[INVALID CONTACT] Не удалось удалить сообщение: {e}")

    data = await state.get_data()
    await delete_last_message(message, data)

    msg = await message.answer(
        "⚠️ Пожалуйста, используйте кнопку ниже, чтобы отправить свой номер телефона.",
        reply_markup=get_send_number_kb_user()
    )
    await state.update_data(last_msg_id=msg.message_id)











# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\


# Запись пользователя
#..................................................................................................................................................
#..................................................................................................................................................





@user_private_router.callback_query(F.data == "record_user")
async def add_record_user(callback_query: CallbackQuery, session: AsyncSession):
    text, photo_path, kbds = await get_add_record_menu_user(session, level=0)
    sent_msg = await safe_edit_or_send_new(
        bot=callback_query.bot,
        message=callback_query.message,
        text=text,
        photo_path=photo_path,
        kb=kbds
    )
    await callback_query.answer()




@user_private_router.callback_query(UserAddRecordCallBack.filter())
async def add_record_menu_user(
    callback_query: CallbackQuery,
    callback_data: UserAddRecordCallBack,
    state: FSMContext,
    session: AsyncSession
):
    text, photo_path, kbds = await get_add_record_menu_user(
        session=session,
        level=callback_data.level,
        service_category=callback_data.service_category,
        service_id=callback_data.service_id,
        barber_id=callback_data.barber_id,
        name_btn=callback_data.name_btn,
        page=callback_data.page,
        date=callback_data.date,
        time=callback_data.time,
        state=state,
        callback_query=callback_query
    )

    if callback_data.level == 6:
        # 1️⃣ Редактируем старое сообщение с итогом
        try:
            await callback_query.message.edit_text(
                text,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.warning(f"Не удалось отредактировать финальное сообщение: {e}")

        # 2️⃣ Отправляем маленькое разделительное сообщение
        await callback_query.message.answer(
            "➖➖➖➖➖➖➖➖➖",
            parse_mode="HTML"
        )

        # 3️⃣ Отправляем отдельное сообщение — главное меню
        sent_msg = await callback_query.message.answer(
            "📋 Вы в главном меню. Выберите действие:",
            reply_markup=get_main_inlineBtns_user(),
            parse_mode="HTML"
        )
    else:
        # Промежуточные шаги — универсальный safe_edit_or_send_new для фото и текста
        sent_msg = await safe_edit_or_send_new(
            bot=callback_query.bot,
            message=callback_query.message,
            text=text,
            photo_path=photo_path,
            kb=kbds
        )

    await state.update_data(last_msg_id=sent_msg.message_id)
    await callback_query.answer()
    





















# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\





# Вывод доступных сервисов для пользователя
#..................................................................................................................................................
#..................................................................................................................................................
#..................................................................................................................................................
@user_private_router.callback_query(F.data == "view_service_user")
async def user_services_list_start(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    text, kbds = await get_user_servives_list_content(session=session, level=0)
    await safe_edit_or_resend(callback_query.bot, callback_query.message, text, kbds, state)
    await callback_query.answer()



# Отлавливает все уникальные калбеки ServiceslistCallBack
@user_private_router.callback_query(UserServiceslistCallBack.filter())
async def user_services_list_menu(callback_query: CallbackQuery, state: FSMContext, callback_data: UserServiceslistCallBack, session: AsyncSession):
    text, kbds = await get_user_servives_list_content(
        session=session,
        level=callback_data.level,
        category=callback_data.service_category,
        page=callback_data.page,
    )
    await safe_edit_or_resend(callback_query.bot, callback_query.message, text, kbds, state)
    await callback_query.answer()









# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\






# Вывод записей пользователя
#..................................................................................................................................................
#..................................................................................................................................................
#..................................................................................................................................................

@user_private_router.callback_query(F.data == "my_records")
async def user_records_start(callback_query: CallbackQuery, session: AsyncSession):
    text, kbds = await get_user_records_list(session=session, level=0, user_id=callback_query.from_user.id)
    await safe_edit_message_text(callback_query.message, text, reply_markup=kbds)
    await callback_query.answer()


@user_private_router.callback_query(UserViewRecordsCallback.filter())
async def user_record_menu(callback_query: CallbackQuery, callback_data: UserViewRecordsCallback, session: AsyncSession):
    text, kbds = await get_user_records_list(
        session=session,
        level=callback_data.level,
        user_id=callback_query.from_user.id,
        page=callback_data.page,
        appointment_id=callback_data.appointment_id
    )
    await safe_edit_message_text(callback_query.message, text, reply_markup=kbds)
    await callback_query.answer()














#..................................................................................................................................................
#..................................................................................................................................................
#..................................................................................................................................................




# Команда О нас 
# Команда О нас 
@user_private_router.callback_query(F.data == "about")
async def about_cmd(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # 1. Удаляем предыдущее сообщение с кнопкой
    try:
        await callback_query.message.delete()
    except Exception as e:
        logging.warning(f"[USER] Не удалось удалить сообщение 'О нас': {e}")

    # 2. Отправляем локацию
    latitude = 55.7558
    longitude = 37.6176

    loc_msg = await bot.send_location(
        chat_id=callback_query.message.chat.id,
        latitude=latitude,
        longitude=longitude
    )
    await state.update_data(last_msg_id=loc_msg.message_id)

    # 3. Формируем и отправляем текст "О нас"
    text = (
        "<b>О нас 💈</b>\n\n"
        "Добро пожаловать в <b>[Ваше название]</b> – место, где стрижка становится искусством! ✂️\n\n"
        "<b>🔥 Почему выбирают нас?</b>\n"
        "• Профессиональные барберы с опытом\n"
        "• Современные и классические стрижки\n"
        "• Атмосфера мужского клуба\n"
        "• Уход за бородой и усами\n"
        "• Только топовые средства\n\n"
        "<b>📍 Где мы находимся?</b>\n"
        "🏠 Адрес: [Ваш адрес]\n"
        "🕒 Время работы: [Ваш график] ежедневно\n\n"
        "<b>📞 Контакты:</b>\n"
        "📲 Телефон: +7 (999) 123-45-67\n"
        "💬 Telegram: @admin_username\n"
        "🌍 Instagram: https://instagram.com/yourbarbershop"
    )

    about_msg = await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=text,
        reply_markup=get_callback_btns(btns={"🔙 Назад": "cancel_user"}),
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=about_msg.message_id)

    await callback_query.answer()
    





# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\






    





@user_private_router.callback_query(UserRememberOkCallback.filter())
async def confirmation_record(callback_query: CallbackQuery, callback_data: UserRememberOkCallback, session: AsyncSession):

# Получаем запись
    appointment = await orm_get_appointment_by_id(session, callback_data.appointment_id)

    if not appointment:
        await callback_query.answer("⚠️ Запись не найдена.")
        await callback_query.message.delete()
        return

    # Проверка срока
    appointment_datetime = datetime.combine(appointment.date_appointment, appointment.time_appointment)
    now = datetime.now()

    if now > appointment_datetime + timedelta(hours=2):
        await callback_query.answer("⚠️ Время подтверждения записи истекло.")
        await callback_query.message.delete()
        return

    # Проверка, не подтвердил ли пользователь уже
    if appointment.status in [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED]:
        await callback_query.answer("⚠️ Запись уже обработана.")
        return

    # Обновляем статус
    status_map = {
        "confirm": AppointmentStatus.CONFIRMED,
        "cancel": AppointmentStatus.CANCELLED
    }
    updated = await orm_update_appointment_status(session, callback_data.appointment_id, status_map[callback_data.status])

    # Удаляем сообщение
    try:
        await callback_query.message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение с кнопками: {e}")

    # Ответ пользователю
    if updated and callback_data.status == "confirm":
        remind_for_rating_time = appointment_datetime + timedelta(hours=1)
        await schedule_rating_request(
            bot=callback_query.bot,
            chat_id=callback_query.message.chat.id,
            barber_id=appointment.barber_id,
            appointment_id=callback_data.appointment_id,
            barber_name=appointment.barber_name,
            send_time=remind_for_rating_time
        )
        text = "✅ Спасибо за подтверждение!"
    elif updated:
        text = "❌ Вы отменили запись."
    else:
        text = "⚠️ Запись не найдена или устарела."

    await callback_query.answer(text)



@user_private_router.callback_query(UserRateBarberCallback.filter())
async def process_barber_rating(callback_query: CallbackQuery, callback_data: UserRateBarberCallback, session: AsyncSession):

    already_rated = await orm_check_rating_exists(session, callback_data.appointment_id)
    if already_rated:
        await callback_query.answer("⚠️ Вы уже оставили оценку.", show_alert=True)
        return

    await orm_add_barber_rating(
        session,
        appointment_id=callback_data.appointment_id,
        barber_id=callback_data.barber_id,
        user_id=callback_query.from_user.id,
        score=callback_data.score
    )

    try:
        await callback_query.message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение с кнопками оценки: {e}")

    await callback_query.answer(f"✅ Спасибо за вашу оценку: {callback_data.score} ⭐️!")

@user_private_router.callback_query(UserRateDeclineCallback.filter())
async def process_rating_decline(callback_query: CallbackQuery, callback_data: UserRateDeclineCallback, session: AsyncSession):

    already_rated = await orm_check_rating_exists(session, callback_data.appointment_id)
    if already_rated:
        await callback_query.answer("⚠️ Вы уже ответили на запрос оценки.", show_alert=True)
        return

    await orm_add_rating_decline(
        session,
        appointment_id=callback_data.appointment_id,
        barber_id=callback_data.barber_id,
        user_id=callback_query.from_user.id
    )

    try:
        await callback_query.message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение с кнопками оценки: {e}")

    await callback_query.answer("❌ Оценка отменена.")


# Команда для того что бы пользователь мог узнать свой id
@user_private_router.message(Command("id"))
async def signup_cmd(message:types.Message):
    await message.answer(f"Ваш id: {message.from_user.id}")






















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







async def replace_message_with_photo_or_text(bot, message, text, photo_path, kb):
    chat_id = message.chat.id

    # Пытаемся удалить старое сообщение
    try:
        await message.delete()
        logging.info(f"Удалено сообщение перед заменой: id={message.message_id}")
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение (id={message.message_id}): {e}")

    # Если есть путь к фото — пробуем отправить фото
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
        except FileNotFoundError:
            logging.error(f"Фото не найдено: {photo_path}")
            return await bot.send_message(
                chat_id=chat_id,
                text=f"{text}\n⚠️ Фото не найдено на сервере.",
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Ошибка при отправке фото: {e}")
            return await bot.send_message(
                chat_id=chat_id,
                text=f"{text}\n⚠️ Не удалось загрузить фото.",
                reply_markup=kb,
                parse_mode="HTML"
            )

    # Иначе просто отправляем текст
    try:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке текста: {e}")





async def safe_edit_or_resend(bot, message, text, reply_markup, state):
    """
    Унифицированная функция: редактирует если можно, иначе удаляет и отправляет новое.
    Сохраняет новый message_id в state.
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
        await state.update_data(last_msg_id=message.message_id)
        return
    except Exception as e:
        logging.warning(f"Не удалось редактировать сообщение (id={message.message_id}): {e}")

    # Падение редактирования — удаляем и отправляем заново
    try:
        await message.delete()
    except Exception:
        pass

    new_msg = await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await state.update_data(last_msg_id=new_msg.message_id)





async def safe_edit_message_text(message, text, reply_markup=None, parse_mode="HTML"):
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Просто игнорируем ситуацию, когда текст не изменился
            return
        raise







    
# Кнопка для отмены 
@user_private_router.callback_query(StateFilter("*"), F.data == "cancel_user")
async def cancel_user(callback_query: CallbackQuery, state: FSMContext):  
    await state.clear()
    await callback_query.answer()
    main_menu_text = (
        "<b>🏠 Главное меню</b>\n\n"
        "✅ Выберите одно из действий ниже:\n")
    sent_message = None

    # 1️⃣ Попытка редактировать
    try:
        sent_message = await callback_query.message.edit_text(
            main_menu_text,
            reply_markup=get_main_inlineBtns_user()
        )
    except Exception as e:
        logging.warning(f"Не удалось отредактировать сообщение: {e}")

    # 2️⃣ Если редактирование не удалось — попытка удалить
    if sent_message is None:
        try:
            await callback_query.message.delete()
            logging.info("Сообщение удалено перед отправкой нового.")
        except Exception as e:
            logging.warning(f"Не удалось удалить сообщение: {e}")

        # 3️⃣ В любом случае отправляем новое
        sent_message = await callback_query.message.answer(
            main_menu_text,
            reply_markup=get_main_inlineBtns_user()
        )

    await state.update_data(last_msg_id=sent_message.message_id)








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