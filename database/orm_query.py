from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,update, delete, and_ , extract, func
from sqlalchemy.exc import IntegrityError

from database.models import Admins,Services,Barbers, BarberSchedule,Users, Appointment,AppointmentHistory, BarberService, AdminLog,AppointmentStatus,BarberRatingHistory

from datetime import time, datetime, timedelta, date

from sqlalchemy.orm import selectinload, joinedload



SERVICE_CATEGORIES_REVERSED = {
    "haircut": "✂️ Стрижки",
    "beard": "🧔 Борода и бритьё",
    "care": "💆‍♂️ Уход за волосами и кожей",
    "styling": "🎭 Стайлинг",
    "combo": "🎟 Комплексные услуги"}



async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Проверяет, является ли пользователь админом в БД."""
    stmt = select(Admins).where(Admins.admin_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None




# Добавление адимна в бд
async def orm_add_admin_to_db(
    admin_id: int,
    admin_name: str,
    actor_id: int,
    session: AsyncSession
) -> bool:
    # Проверка: уже существует?
    existing_admin_result = await session.execute(
        select(Admins).where(Admins.admin_id == admin_id)
    )
    if existing_admin_result.scalar():
        return False

    # Добавление нового админа
    new_admin = Admins(admin_id=admin_id, admin_name=admin_name)
    session.add(new_admin)
    await session.commit()
    return True



# Получение текущих администраторов
async def get_admins_list(session: AsyncSession):
    result = await session.execute(select(Admins))
    admins = result.scalars().all()
    if not admins:
        return "❌ В списке нет администраторов."
    
    admins_text = "\n".join([f"🔹 <b>{admin.admin_name}</b> (ID: <code>{admin.admin_id}</code>)" for admin in admins])
    return f"📋 <b>Список администраторов:</b>\n\n{admins_text}"


# Функция которая вызываетя при начале запуска бота что бы у неё всегда был начальный админ
async def add_main_admin(session: AsyncSession):
    admin_id = 896957462  # ID главного админа

    # Проверяем, есть ли уже этот админ в базе
    stmt = select(Admins).where(Admins.admin_id == admin_id)
    result = await session.execute(stmt)
    existing_admin = result.scalar_one_or_none()

    if not existing_admin:
        obj = Admins(admin_id=admin_id, admin_name="Admin")
        session.add(obj)
        await session.commit()
        print("Главный админ добавлен.")
    else:
        print("Главный админ уже есть в базе.")




async def orm_get_admin_name_by_id(admin_id: int, session: AsyncSession):
    result = await session.execute(select(Admins).where(Admins.admin_id == admin_id))
    admin = result.scalars().first()
    return admin.admin_name if admin else None





async def orm_del_admin_by_id(
    admin_id: int,            # ID удаляемого админа
    session: AsyncSession
):
    try:
        # Получаем удаляемого админа
        result = await session.execute(select(Admins).where(Admins.admin_id == admin_id))
        admin = result.scalar_one_or_none()
        if not admin:
            return False

        # Удаляем администратора
        await session.delete(admin)

        #
        
        await session.commit()
        return True
    except:
        return False
    




async def orm_add_barber(data, session: AsyncSession):
    existing_barber = await session.execute(
        select(Barbers).where(
            Barbers.name == data["name"],
            Barbers.phone == data["phone"]
        )
    )
    if existing_barber.scalars().first():
        return None, f"⚠️ Барбер <b>{data['name']}</b> с таким номером уже существует!"

    new_barber = Barbers(
        name=data["name"],
        phone=data["phone"],
        experience=data.get("experience", 0),
        specialization=data["specialization"],
        photo_path=data.get("photo_path")
    )
    session.add(new_barber)
    await session.commit()
    await session.refresh(new_barber)

    return new_barber.id, f"✅ Барбер <b>{data['name']}</b> успешно добавлен!"





async def orm_add_service(data, session: AsyncSession) -> str:
    try:
        existing_service = await session.execute(
            select(Services).where(Services.service_name == data["name"])
        )
        if existing_service.scalars().first():
            return f"⚠️ Услуга <b>{data['name']}</b> уже существует!"

        obj = Services(
            service_name=data["name"],
            service_price=data["price"],
            service_duration=data["duration"],
            service_category=data["category"]
        )
        session.add(obj)


        await session.commit()
        return f"✅ Услуга <b>{data['name']}</b> успешно добавлена!"

    except Exception as err:
        return False





async def orm_update_service(data: dict, session: AsyncSession) -> str:
    try:
        obj = data.get("obj")
        if not obj:
            return "❌ Ошибка: не найдена услуга для обновления."

        stmt = (
            update(Services)
            .where(Services.id == obj.id)
            .values(
                service_name=data.get("name"),
                service_price=data.get("price"),
                service_duration=data.get("duration"),
                service_category=data.get("category")
            )
            .execution_options(synchronize_session="fetch")
        )

        await session.execute(stmt)

        # Логирование
        actor_id = data.get("actor_id")
        if actor_id:
            actor_result = await session.execute(select(Admins).where(Admins.admin_id == actor_id))
            actor = actor_result.scalar_one_or_none()
            actor_name = actor.admin_name if actor else "Неизвестный админ"

            log = AdminLog(
                admin_id=actor_id,
                admin_name=actor_name,
                action="Редактирование услуги",
                description=(
                    f"Обновлена услуга: ID — {obj.id}, Название: {data.get('name')}, "
                    f"Цена: {data.get('price')}, Длительность: {data.get('duration')}, "
                    f"Категория: {data.get('category')}"
                )
            )
            session.add(log)

        await session.commit()
        return f"✅ Услуга <b>{data['name']}</b> успешно обновлена!"
    except Exception as ex:
        return False





# Связь барбера и услуги
async def orm_link_barber_to_service(session: AsyncSession, barber_id: int, service_id: int) -> bool:
    # Проверка на существующую связку
    result = await session.execute(
        select(BarberService).where(
            BarberService.barber_id == barber_id,
            BarberService.service_id == service_id
        )
    )
    existing_link = result.scalar_one_or_none()
    
    if existing_link:
        return False  # Такая связка уже есть

    # Добавляем новую связку
    link = BarberService(barber_id=barber_id, service_id=service_id)
    session.add(link)
    try:
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False  # Вдруг дубль из-за гонки





async def orm_get_services_by_barber_id(session: AsyncSession, barber_id: int):
    result = await session.execute(
        select(Services)
        .join(BarberService)
        .where(BarberService.barber_id == barber_id)
        .options(selectinload(Services.barbers))  # если есть связь
    )
    return result.scalars().all()





async def orm_update_barber_info(data: dict, session: AsyncSession) -> str:
    obj = data.get("obj")
    if not obj:
        return "❌ Ошибка: не найдена услуга для обновления."

    stmt = (
        update(Barbers)
        .where(Barbers.id == obj.id)
        .values(
            name=data.get("name"),
            phone=data.get("phone"),
            experience=data.get("experience"),
            specialization=data.get("specialization"),
            photo_path=data.get("photo_path")
        )
        .execution_options(synchronize_session="fetch")
    )

    await session.execute(stmt)
    await session.commit()
    return f"✅ Информация о барбере с именем <b>{data["name"]}</b> успешно обновлена!"





async def orm_update_barber_schedule(session: AsyncSession, barber_id: int, new_schedule: dict):
    await session.execute(
        delete(BarberSchedule).where(BarberSchedule.barber_id == barber_id)
    )

    for weekday, time_range in new_schedule.items():
        start_str, end_str = time_range.split("-")
        schedule = BarberSchedule(
            barber_id=barber_id,
            weekday=weekday,
            start_time=datetime.strptime(start_str, "%H:%M").time(),
            end_time=datetime.strptime(end_str, "%H:%M").time(),
        )
        session.add(schedule)

    await session.commit()





async def orm_get_services(session: AsyncSession, category: str):
    result = await session.execute(
        select(Services).where(Services.service_category == category)
    )

    services = result.scalars().all()
    return services  # Возвращаем список объектов Services





async def orm_get_all_barbers(session: AsyncSession):
    result = await session.execute(select(Barbers))
    barbers = result.scalars().all()
    return barbers  # Возвращаем список объектов Barbers





async def orm_delete_service_by_id(session: AsyncSession, service_id: int) -> str | None:
    service = await session.get(Services, service_id)
    if service:
        service_name = service.service_name

        # Удаляем связи услуги с барберами
        await session.execute(
            delete(BarberService).where(BarberService.service_id == service_id)
        )

        # Удаляем саму услугу
        await session.delete(service)
        await session.commit()

        return service_name

    return None





async def orm_delete_barber_by_id(session: AsyncSession, barber_id: int) -> str | None:
    barber = await session.get(Barbers, barber_id)
    if barber:
        barber_name = barber.name

        # Удаляем график работы барбера
        await session.execute(
            delete(BarberSchedule).where(BarberSchedule.barber_id == barber_id)
        )

        # Удаляем связи барбера с услугами
        await session.execute(
            delete(BarberService).where(BarberService.barber_id == barber_id)
        )

        # Удаляем самого барбера
        await session.delete(barber)
        await session.commit()

        return barber_name

    return None





async def orm_get_service_by_id(session: AsyncSession, service_id: int):
    query = select(Services).where(Services.id == service_id)
    result = await session.execute(query)
    return result.scalar()





async def orm_get_barber_by_id(session: AsyncSession, barber_id: int):
    query = select(Barbers).where(Barbers.id == barber_id)
    result = await session.execute(query)
    return result.scalar()





# Получение графика работы барбера
async def orm_get_barber_schedule_by_id(session: AsyncSession, barber_id: int) :
    result = await session.execute(
        select(BarberSchedule.weekday, BarberSchedule.start_time, BarberSchedule.end_time)
        .where(BarberSchedule.barber_id == barber_id)
    )
    schedule = {}
    for weekday, start_time, end_time in result.all():
        schedule[weekday] = (start_time, end_time)
    return schedule





async def orm_get_appointments_by_barber(session: AsyncSession, barber_id: int):
    result = await session.execute(
        select(Appointment.date_appointment, Appointment.time_appointment)
        .where(Appointment.barber_id == barber_id)
    )
    return result.all()  # Вернёт список кортежей (date, time)





async def orm_save_barber_schedule(session: AsyncSession, barber_id: int, schedule: dict[int, str]) -> None:
    def normalize_time_str(s: str) -> str:
        parts = s.split(":")
        if len(parts) != 2:
            return s
        hour, minute = parts
        hour = hour.zfill(2)
        return f"{hour}:{minute}"

    schedule_objs = []
    for weekday, time_range in schedule.items():
        try:
            start_str, end_str = time_range.split("-")
            start_str = normalize_time_str(start_str.strip())
            end_str = normalize_time_str(end_str.strip())
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
        except ValueError:
            continue  # Пропускаем некорректный формат

        schedule_objs.append(
            BarberSchedule(
                barber_id=barber_id,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time
            )
        )

    session.add_all(schedule_objs)
    await session.commit()





async def orm_unlink_service_from_barber(session: AsyncSession, barber_id: int, service_id: int):
    result = await session.execute(
        select(BarberService).where(
            BarberService.barber_id == barber_id,
            BarberService.service_id == service_id
        )
    )
    link = result.scalar_one_or_none()
    print("DEBUG: связь найдена:", link)

    if link:
        await session.execute(
            delete(BarberService).where(
                BarberService.barber_id == barber_id,
                BarberService.service_id == service_id
            )
        )
        await session.commit()
    else:
        print("DEBUG: связи не существует")





# получнеие только тех барберов которые заеимаются конеретной услугой
async def orm_get_barbers_by_service_id(session: AsyncSession, service_id: int):
    stmt = (
        select(Barbers)
        .join(Barbers.services)
        .where(Services.id == service_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()





# Получения списка текущих достпуных дат для конерктного барбера и услуги на 14 дней
async def orm_get_available_dates(session, barber_id: int, service_id: int):


    result_dates = []
    today = datetime.now().date()
    service: Services = await session.get(Services, service_id)
    duration = timedelta(minutes=service.service_duration)

    for i in range(14):
        current_date = today + timedelta(days=i)
        weekday = current_date.weekday()

        # Получаем расписание барбера на этот день недели
        stmt = select(BarberSchedule).where(
            BarberSchedule.barber_id == barber_id,
            BarberSchedule.weekday == weekday
        )
        schedule = (await session.execute(stmt)).scalar_one_or_none()
        if not schedule:
            continue

        # Получаем уже занятые записи на текущую дату
        appointments_stmt = select(Appointment.time_appointment).where(
            Appointment.barber_id == barber_id,
            Appointment.date_appointment == current_date
        )
        existing_times = {r[0] for r in (await session.execute(appointments_stmt)).all()}

        # Генерация слотов
        slots = []
        current_time = datetime.combine(current_date, schedule.start_time)
        end_time = datetime.combine(current_date, schedule.end_time)

        while current_time + duration <= end_time:
            if current_time.time() not in existing_times:
                slots.append(current_time.time())
            current_time += duration

        if slots:
            result_dates.append(current_date)

    return result_dates





# Генерация свободных слотов формат данных выходных данных словарь
async def orm_get_free_time_slots(session: AsyncSession, barber_id: int, service_id: int, date_obj: date):
    weekday = date_obj.weekday()

    # график работы
    schedule_stmt = select(BarberSchedule).where(
        and_(
            BarberSchedule.barber_id == barber_id,
            BarberSchedule.weekday == weekday
        )
    )
    schedule_result = await session.execute(schedule_stmt)
    schedule: BarberSchedule | None = schedule_result.scalar_one_or_none()
    if not schedule:
        return []

    # длительность выбранной услуги (для генерации слотов)
    service_stmt = select(Services.service_duration).where(Services.id == service_id)
    service_result = await session.execute(service_stmt)
    selected_service_duration: int = service_result.scalar_one_or_none()
    if selected_service_duration is None:
        return []

    #  уже занятые записи с их временем начала и длительностью
    appointments_stmt = select(Appointment.time_appointment, Appointment.service_duration).where(
        and_(
            Appointment.barber_id == barber_id,
            Appointment.date_appointment == date_obj
        )
    )
    appointments_result = await session.execute(appointments_stmt)
    busy_slots = []
    for time_start, duration in appointments_result.all():
        start_dt = datetime.combine(date_obj, time_start)
        end_dt = start_dt + timedelta(minutes=duration)
        busy_slots.append((start_dt, end_dt))

    # генерация доступных слотов доступные слоты
    free_slots = []
    current_time = datetime.combine(date_obj, schedule.start_time)
    end_time = datetime.combine(date_obj, schedule.end_time)

    while current_time + timedelta(minutes=selected_service_duration) <= end_time:
        overlaps = any(start <= current_time < end for start, end in busy_slots)
        if not overlaps:
            free_slots.append(current_time.time())
        current_time += timedelta(minutes=30)  # или другой шаг

    return free_slots





# Финальное добовление в таблицу appointment данных . Админ
async def orm_add_appontment_admin(
    session: AsyncSession,
    data: dict,
    date: date,
    time: time
) -> tuple[str, str | None, str | None]:

    try:
        service_id = int(data["service_id"])
        barber_id = int(data["barber_id"])

        service = await orm_get_service_by_id(session, service_id)
        barber = await orm_get_barber_by_id(session, barber_id)

        if not service or not barber:
            return "❌ Услуга или барбер не найдены. Невозможно создать запись.", None, None

        # 🔎 Новая проверка: свободен ли слот
        is_taken = await orm_check_barber_slot_taken(session, barber_id, date, time)
        if is_taken:
            return (
                "⚠️ Выбранный слот уже занят другим клиентом.\n"
                "Пожалуйста, выберите другую дату или время.", 
                None, None
            )

        # ✅ Если слот свободен — создаём запись
        appointment = Appointment(
            client_name=data["client_name"],
            phone=data["phone"],
            date_appointment=date,
            time_appointment=time,
            service_id=service.id,
            service_name=service.service_name,
            service_price=float(service.service_price),
            service_duration=service.service_duration,
            barber_id=barber.id,
            barber_name=barber.name,
            status=AppointmentStatus.ADDED_BY_ADMIN
        )

        session.add(appointment)
        await session.commit()

        return "✅ Запись успешно добавлена!", service.service_name, barber.name

    except Exception as ex:
        await session.rollback()
        return f"❌ Ошибка при добавлении записи: {ex}", None, None
    




async def orm_get_available_dates_for_view_slots(session: AsyncSession, barber_id: int, days: int = 14) -> list[date]:
    """Возвращает список дат, когда у барбера есть рабочее время (на ближайшие N дней)."""
    today = date.today()
    available_dates = []

    for offset in range(days):
        target_date = today + timedelta(days=offset)
        weekday = target_date.weekday()

        stmt = select(BarberSchedule).where(
            and_(
                BarberSchedule.barber_id == barber_id,
                BarberSchedule.weekday == weekday
            )
        )
        result = await session.execute(stmt)
        schedule = result.scalar_one_or_none()

        if schedule and schedule.start_time != schedule.end_time:
            available_dates.append(target_date)

    return available_dates





# Информация для вывода слотов в админке
async def orm_get_appointments_for_view_slots(session: AsyncSession, barber_id: int, date_obj: date):
    stmt = select(
        Appointment.id,
        Appointment.time_appointment,
        Appointment.client_name,
        Appointment.phone,
        Appointment.service_name,
        Appointment.service_duration,
        Appointment.status
    ).where(
        and_(
            Appointment.barber_id == barber_id,
            Appointment.date_appointment == date_obj
        )
    ).order_by(Appointment.time_appointment)

    result = await session.execute(stmt)
    return result.all()





# Удаление записи по id
async def orm_delete_appointment_by_id(session: AsyncSession, appointment_id: int) -> bool:
    
    stmt = delete(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0  # True если запись была удалена





# Для логирования действий админа
async def orm_log_admin_action(session: AsyncSession, admin_id: int, action: str, description: str):
    admin_name = await orm_get_admin_name_by_id(session=session, admin_id=admin_id)
    
    log = AdminLog(
        admin_id=admin_id,
        admin_name=admin_name if admin_name else "Неизвестный админ",
        action=action,
        description=description
    )
    session.add(log)
    await session.commit()





# Для вывода данных о действия админов за определённый промежуток вермени 
async def orm_get_admin_logs(session: AsyncSession, start_date: datetime, end_date: datetime):
    # Обрезаем время у даты начала и устанавливаем конец дня для даты окончания
    start_dt = datetime.combine(start_date.date(), datetime.min.time())
    end_dt = datetime.combine(end_date.date(), datetime.max.time())

    stmt = (
        select(AdminLog)
        .where(
            and_(
                AdminLog.timestamp >= start_dt,
                AdminLog.timestamp <= end_dt
            )
        )
        .order_by(AdminLog.timestamp.asc())
    )
    result = await session.execute(stmt)
    logs = result.scalars().all()
    return logs





# обычное добавление записи пользователя 
async def orm_add_appointment_user(
    session: AsyncSession,
    client_name: str,
    phone: str,
    date_str: str,
    time_str: str,
    service_id: int,
    barber_id: int
) -> tuple[bool, str, int | None]:
    try:
        # Загружаем дату и время
        date_appointment = datetime.strptime(date_str, "%d.%m.%Y").date()
        time_appointment = datetime.strptime(time_str.replace("_", ":"), "%H:%M").time()

        # Получаем сервис и барбера
        service = await orm_get_service_by_id(session, service_id)
        barber = await orm_get_barber_by_id(session, barber_id)

        if not service or not barber:
            return False, "❌ Услуга или барбер не найдены. Невозможно создать запись.", None

        # Преобразуем Decimal -> float
        service_price = float(service.service_price) if service.service_price is not None else 0.0

        # Сохраняем запись
        appointment = Appointment(
            client_name=client_name,
            phone=phone,
            date_appointment=date_appointment,
            time_appointment=time_appointment,
            service_id=service.id,
            service_name=service.service_name,
            service_price=service_price,
            service_duration=service.service_duration,
            barber_id=barber.id,
            barber_name=barber.name,
            status=AppointmentStatus.PENDING
        )

        session.add(appointment)
        await session.commit()

        # Формируем красивый текст для пользователя
        response_message = (
            f"✅ Ваша запись успешно добавлена!\n\n"
            f"📅 <b>Дата:</b> {date_appointment.strftime('%d.%m.%Y')}\n"
            f"⏰ <b>Время:</b> {time_appointment.strftime('%H:%M')}\n"
            f"💈 <b>Барбер:</b> {barber.name}\n"
            f"🛠 <b>Услуга:</b> {service.service_name}\n"
            f"💰 <b>Стоимость:</b> {round(service_price, 2)} ₽"
        )

        return True, response_message, appointment.id

    except Exception as ex:
        await session.rollback()
        return False, f"❌ Ошибка при добавлении записи: {ex}", None





# Обновление статуса записи
async def orm_update_appointment_status(session: AsyncSession, appointment_id: int, new_status: AppointmentStatus):
    appointment = await session.get(Appointment, appointment_id)
    if appointment:
        appointment.status = new_status
        await session.commit()
        return True
    return False





async def orm_check_daily_limit(session: AsyncSession, phone: str, date: date, limit: int = 2) -> bool:
    result = await session.execute(
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.phone == phone,
            Appointment.date_appointment == date
        )
    )
    count = result.scalar()
    return count >= limit





async def orm_get_user_by_id(session: AsyncSession, user_id: int):
    query = select(Users).where(Users.user_id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()





async def orm_add_user(session: AsyncSession, user_id: int, full_name: str, phone: str):
    user = Users(user_id=user_id, full_name=full_name, phone=phone)
    session.add(user)
    await session.commit()





async def orm_get_actual_appointments_by_user_id(session: AsyncSession, user_id: int) -> list[Appointment]:
    # Шаг 1: Получаем пользователя
    stmt_user = select(Users).where(Users.user_id == user_id)
    result_user = await session.execute(stmt_user)
    user = result_user.scalar_one_or_none()

    if not user:
        return []

    now = datetime.now()

    # Шаг 2: Получаем только будущие записи (либо текущие)
    stmt_appointments = (
        select(Appointment)
        .where(
            and_(
                Appointment.phone == user.phone,
                # дата позже сегодня, или если дата сегодня — время позже текущего
                (Appointment.date_appointment > now.date()) |
                ((Appointment.date_appointment == now.date()) &
                 (Appointment.time_appointment > now.time()))
            )
        )
        .order_by(Appointment.date_appointment, Appointment.time_appointment)
    )

    result_appointments = await session.execute(stmt_appointments)
    return result_appointments.scalars().all()





# Удаление записи пользователем если это возмножно(за 3 часа до записи)
async def orm_delete_appointment_if_possible(session: AsyncSession, appointment_id: int) -> bool:
    stmt = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(stmt)
    appointment = result.scalar_one_or_none()

    if not appointment:
        return False  # такой записи нет

    appointment_datetime = datetime.combine(appointment.date_appointment, appointment.time_appointment)
    now = datetime.now()

    if appointment_datetime - now < timedelta(hours=3):
        return False  # нельзя удалить — менее 3 часов

    # удаление
    await session.delete(appointment)
    await session.commit()
    return True





# сохраняем в историю
async def orm_save_to_history(
    session: AsyncSession,
    client_name: str,
    phone: str,
    date_: date,
    time_: time,
    service_id: int,
    barber_id: int
):
    new_record = AppointmentHistory(
        client_name=client_name,
        phone=phone,
        date_appointment=date_,
        time_appointment=time_,
        service_id=service_id,
        barber_id=barber_id
    )
    session.add(new_record)
    await session.commit()






# проверка была ли уже запись
async def orm_slot_exists_in_history(session: AsyncSession, phone: str, date_: date, time_: time) -> bool:
    stmt = select(AppointmentHistory).where(
        AppointmentHistory.phone == phone,
        AppointmentHistory.date_appointment == date_,
        AppointmentHistory.time_appointment == time_
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None



async def orm_add_barber_rating(session: AsyncSession, barber_id: int, score: int):
    barber = await orm_get_barber_by_id(session, barber_id)
    if not barber:
        return False

    barber.rating_sum += score
    barber.rating_count += 1

    await session.commit()
    return True


async def orm_get_appointment_by_id(session: AsyncSession, appointment_id: int) -> Appointment | None:
    query = select(Appointment).where(Appointment.id == appointment_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()






async def orm_check_barber_slot_taken(session: AsyncSession, barber_id: int, date_: date, time_: time) -> bool:
    result = await session.execute(
        select(Appointment)
        .where(Appointment.barber_id == barber_id)
        .where(Appointment.date_appointment == date_)
        .where(Appointment.time_appointment == time_)
        .where(Appointment.status != AppointmentStatus.CANCELLED)
    )
    return result.scalar() is not None



async def orm_add_barber_rating(
    session: AsyncSession,
    appointment_id: int,
    barber_id: int,
    user_id: int,
    score: int
):
    new_rating = BarberRatingHistory(
        appointment_id=appointment_id,
        barber_id=barber_id,
        user_id=user_id,
        score=score
    )
    session.add(new_rating)
    await session.commit()


async def orm_add_rating_decline(
    session: AsyncSession,
    appointment_id: int,
    barber_id: int,
    user_id: int
):
    new_decline = BarberRatingHistory(
        appointment_id=appointment_id,
        barber_id=barber_id,
        user_id=user_id,
        declined=True
    )
    session.add(new_decline)
    await session.commit()



async def orm_check_rating_exists(session: AsyncSession, appointment_id: int) -> bool:
    result = await session.execute(
        select(BarberRatingHistory).where(BarberRatingHistory.appointment_id == appointment_id)
    )
    return result.scalars().first() is not None


async def orm_check_user_double_booking(session, phone, date_, time_):
    stmt = select(Appointment).where(
        Appointment.phone == phone,
        Appointment.date_appointment == date_,
        Appointment.time_appointment == time_,
        Appointment.status != AppointmentStatus.CANCELLED
    )
    result = await session.execute(stmt)
    return result.scalars().first() is not None