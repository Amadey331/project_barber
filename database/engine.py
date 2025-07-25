import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base

# сам движок
engine = create_async_engine(os.getenv('DB_LITE'),echo = True)

# Создание ссесии

session_maker = async_sessionmaker(bind= engine, class_=AsyncSession, expire_on_commit= False)


# Создание базы данных если её ещё не существует
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drom_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)