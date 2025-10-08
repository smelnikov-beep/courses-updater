import sys
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot.config_reader import config
from bot.handlers import commands
from bot.middlewares import DbSessionMiddleware


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    engine = create_async_engine(url=config.db_url, echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode='HTML'))

    # Setup dispatcher and bind routers to it
    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    # Automatically reply to all callbacks
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    # Register handlers
    dp.include_router(commands.router)

    # Run bot
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
