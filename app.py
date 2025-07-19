import os

import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from heandlers.user_private import user_private_router
from heandlers.admin_private import admin_private_router

from common.bot_cmds_list import private

from database.engine import drom_db,create_db
from database.engine import session_maker

from database.orm_query import add_main_admin

from middlewares.db import DataBaseSession

from scheduler import start_scheduler

from middlewares.error_middleware import ErrorMiddleware

# не добвляется в журнал адиеномв едаление записи






bot = Bot(token=os.getenv("TOKEN"),default=DefaultBotProperties(parse_mode=ParseMode.HTML ))



db = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)

db.include_routers(user_private_router,admin_private_router)

async def on_startup(bot):
    run_param = False
    print("Бот запускается")
    if run_param:
        await drom_db()

    
    await create_db()
    async with session_maker() as session:
        
        await add_main_admin(session)       

    # 🔔 Запуск планировщика
    start_scheduler()

async def on_shutdown(bot):
    print("Бот остановил работу")

# Запуск бота 
async def main():
    db.startup.register(on_startup)
    db.shutdown.register(on_shutdown)
    
    db.update.middleware(DataBaseSession(session_pool=session_maker))
    db.update.middleware(ErrorMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)
    # Добавить меню о командах
    await bot.set_my_commands(commands=private,scope=types.BotCommandScopeAllPrivateChats())
    # Удалить меню о командах
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await db.start_polling(bot,allowed_updates= db.resolve_used_update_types())

asyncio.run(main())


































