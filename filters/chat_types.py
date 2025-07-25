from aiogram.filters import Filter
from aiogram import Bot,types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import is_admin



# Добавление фильтра которые проверяет на админа



class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]):
        self.chat_types = chat_types

    async def __call__(self, message: types.Message):
        return message.chat.type in self.chat_types
    
class IsAdmin(Filter):
    def __init__(self):
        pass

    async def __call__(self, message: types.Message, session: AsyncSession) -> bool:
        """Фильтр проверки админа через БД (сессия приходит из middleware)"""
        return await is_admin(message.from_user.id, session)