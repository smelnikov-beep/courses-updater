import asyncio
import datetime
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, SwitchInlineQueryChosenChat
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import requests

from bot.config_reader import config
from bot.db.models import Channel


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode='HTML'))
engine = create_async_engine(url=config.db_url_local, echo=True)
sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


def get_course(coin_id: int):
    url = f'https://api.coinlore.net/api/ticker/?id={coin_id}'
    res = requests.get(url).json()
    res = float(res[0]['price_usd'])
    if res > 1000:
        return f'{round(res):_}'.replace('_', ' ')
    return res


def get_message():
    ton_id = 54683
    btc_id = 90
    eth_id = 80

    return f'''📊 BTC ${get_course(btc_id)}
 • ETH ${get_course(eth_id)}
 • TON ${get_course(ton_id)}'''


def make_keyboard(link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Купить', url=link))
    return builder.as_markup()


async def check_bot_admin_in_channel(bot: Bot, channel_id: int) -> bool:
    """
    Checks if the bot is an administrator in the specified channel.

    :param bot: The Aiogram Bot instance.
    :param channel_id: The unique identifier for the target channel (e.g., -1001234567890)
    :return: True if the bot is an administrator, False otherwise.
    """
    try:
        # Get information about the bot in the channel
        chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=bot.id)

        # Check if the bot's status is 'administrator' or 'creator'
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        return False


async def check_message_exists(bot: Bot, chat_id: int, message_id: int) -> bool:
    try:
        await bot.set_message_reaction(chat_id, message_id, None)

        return True

    except Exception as e:

        error_message = str(e).lower()

        if 'reaction' in error_message:
            return True

        return False


async def send():
    async with bot.session:
        today = datetime.date.today()
        updated_message = get_message()
        async with sessionmaker() as session:
            stmt = select(Channel)
            result = await session.execute(stmt)
            channels = result.scalars().all()

            for channel in channels:
                try:
                    if not channel.active_until or channel.active_until < today:
                        continue
                    bot_is_admin = await check_bot_admin_in_channel(bot, channel.channel_id)
                    if not bot_is_admin:
                        continue
                    if channel.post_id:
                        is_actual = await check_message_exists(bot, channel.channel_id, channel.post_id)
                    if not channel.post_id or not is_actual:
                        message = await bot.send_message(channel.channel_id,
                                    updated_message, reply_markup=make_keyboard(channel.link))
                        channel.post_id = message.message_id
                        session.add(channel)
                    else:
                        try:
                            await bot.edit_message_text(text=updated_message,
                                chat_id=channel.channel_id,
                                message_id=channel.post_id,
                                reply_markup=make_keyboard(channel.link))
                        except:
                            ...
                except:
                    ...
            await session.commit()


if __name__ == "__main__":
    asyncio.run(send())