from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationship
from sqlalchemy import String, Text, Float, DateTime, func, Integer, Date, Time, ForeignKey, Table, Column, Boolean

from datetime import date, time, datetime

from sqlalchemy import Enum as SQLEnum

import enum









# Базовая таблица  
class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(),onupdate=func.now())


# Таблица с пользователями
class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)


# Таблица для барберов их имя и.т.д
class Barbers(Base):
    __tablename__ = "barbers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(Text)
    experience: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    photo_path: Mapped[str] = mapped_column(String(300), nullable=True)  # Добавлено поле

    rating_sum: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    services = relationship(
        "Services",
        secondary="barber_services",
        back_populates="barbers",
        viewonly=True
    )


# Таблица где храняться админов
class Admins(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    admin_name: Mapped[str] = mapped_column(Text)

    logs = relationship("AdminLog", back_populates="admin")


# Таблица где храняться сервисы (Стрижки там разные)
class Services(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(Text)
    service_price: Mapped[float] = mapped_column(Float(asdecimal=True), nullable=False)
    service_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    service_category: Mapped[str] = mapped_column(Text)

    barbers = relationship(
        "Barbers",
        secondary="barber_services",
        back_populates="services",
        viewonly=True
    )


# Таблицы для записи
class AppointmentStatus(enum.Enum):
    PENDING = "ожидает подтверждения"
    CONFIRMED = "подтверждён"
    CANCELLED = "отменён пользователем"
    ADDED_BY_ADMIN = "добавлена админом"  


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    date_appointment: Mapped[date] = mapped_column(Date, nullable=False)
    time_appointment: Mapped[time] = mapped_column(Time, nullable=False)

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="SET NULL"), nullable=True)

    # сохраняем дублирующую информацию
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    service_price: Mapped[int] = mapped_column(Integer, nullable=False)

    barber_name: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING)


# Таблица для всей истории добовлений  
class AppointmentHistory(Base):
    __tablename__ = "appointment_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    date_appointment: Mapped[date] = mapped_column(Date, nullable=False)
    time_appointment: Mapped[time] = mapped_column(Time, nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id"))
    status: Mapped[AppointmentStatus] = mapped_column(SQLEnum(AppointmentStatus),default=AppointmentStatus.PENDING)
    canceled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Таблица для графика барберов
class BarberSchedule(Base):
    __tablename__ = "barber_schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="CASCADE"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0 — Пн, 6 — Вс
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)


# Таблица для связи барбера и сервиса типо один барбер может выполнять много услуг, и одна услуга может выполняться несколькими барберами
class BarberService(Base):
    __tablename__ = "barber_services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    barber_id: Mapped[int] = mapped_column(ForeignKey("barbers.id", ondelete="CASCADE"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))


# Таблица чтобы отслеживать действия админов
class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    admin_name = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admins", back_populates="logs")






class BarberRatingHistory(Base):
    __tablename__ = "barber_rating_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    barber_id: Mapped[int] = mapped_column(
        ForeignKey("barbers.id", ondelete="SET NULL"),
        nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=True)  # от 1 до 5
    declined: Mapped[bool] = mapped_column(Boolean, default=False)



