from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot
from datetime import datetime, timedelta

from kbds.inline_user import get_callback_btns, get_remember_ok_kb,get_rating_inline_kb

from aiogram import  types

import logging

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.start()

async def send_reminder(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"Ошибка при отправке напоминания: {e}")

def schedule_reminder(bot: Bot, chat_id: int, remind_time: datetime, text: str, appointment_id: int):
    async def send_reminder():
        try:
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=get_remember_ok_kb(
                    message_id=0,  # временно, обновим ниже
                    chat_id=chat_id,
                    appointment_id=appointment_id
                )
            )

            # Перегенерируем с правильным message_id
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message.message_id,
                reply_markup=get_remember_ok_kb(
                    message_id=message.message_id,
                    chat_id=chat_id,
                    appointment_id=appointment_id
                )
            )
            delete_time = remind_time + timedelta(hours=2)
            schedule_message_deletion(bot, chat_id, message.message_id, delete_time)
        except Exception as e:
            print(f"Ошибка при отправке напоминания: {e}")

    scheduler.add_job(
        send_reminder,
        trigger='date',
        run_date=remind_time,
        id=f"reminder_{chat_id}_{remind_time.timestamp()}",
        misfire_grace_time=60,
    )


async def schedule_rating_request(
    bot: Bot,
    chat_id: int,
    barber_id: int,
    appointment_id: int,
    barber_name: str,
    send_time: datetime
):
    async def send_rating():
        text = (
            f"🙏 Пожалуйста, оцените обслуживание барбера!\n"
            f"Вы были записаны к {barber_name}"
        )
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_rating_inline_kb(barber_id, appointment_id)
        )

    scheduler.add_job(
        send_rating,
        trigger='date',
        run_date=send_time,
        id=f"rate_{chat_id}_{appointment_id}",
        misfire_grace_time=60,
    )


def schedule_message_deletion(bot: Bot, chat_id: int, message_id: int, delete_time: datetime):
    async def delete_message_job():
        try:
            await bot.delete_message(chat_id, message_id)
            logging.info(f"Удалено устаревшее сообщение с кнопками (id={message_id})")
        except Exception as e:
            logging.warning(f"Не удалось удалить устаревшее сообщение (id={message_id}): {e}")

    scheduler.add_job(
        delete_message_job,
        trigger='date',
        run_date=delete_time,
        id=f"delete_{chat_id}_{message_id}_{delete_time.timestamp()}",
        misfire_grace_time=60,
    )