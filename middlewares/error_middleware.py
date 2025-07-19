import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)

class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"❗ Unhandled exception: {e}")
            
            # Попытка отправить пользователю "всплывающее уведомление" вместо обычного сообщения
            try:
                # Если это callback_query — отправляем answer
                if hasattr(event, 'answer'):
                    await event.answer(
                        text="⚠️ Произошла ошибка. Попробуйте позже.",
                        show_alert=False  # False = всплывающее уведомление внизу
                    )
                # Если это сообщение — можно проигнорировать или отправить сообщение
                elif hasattr(event, 'message') and hasattr(event.message, 'answer'):
                    await event.message.answer(
                        "⚠️ Произошла ошибка. Попробуйте позже."
                    )
            except TelegramAPIError as inner:
                logger.warning(f"❗ Couldn't notify user about error: {inner}")
            raise
