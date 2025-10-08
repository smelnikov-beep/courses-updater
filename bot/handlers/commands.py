import datetime
from dateutil.relativedelta import relativedelta

from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, MEMBER, KICKED, ADMINISTRATOR
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated, Message
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Channel
from bot.config_reader import config


router = Router(name="commands-router")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR))
async def bot_became_admin(update: ChatMemberUpdated, session: AsyncSession, bot: Bot):
    if update.chat.type != 'channel':
        return

    if not update.from_user.id in (config.main_admin_id, config.second_admin_id):
        return

    channel = await session.get(Channel, update.chat.id)
    if not channel:
        channel = Channel()
        channel.channel_id = update.chat.id
    channel.link = config.default_link
    channel.active_until = datetime.date(2222, 1, 1)

    session.add(channel)
    await session.commit()


@router.my_chat_member(lambda update: update.new_chat_member.status != ChatMemberStatus.ADMINISTRATOR)
async def bot_lost_admin(update: ChatMemberUpdated, session: AsyncSession, bot: Bot):
    if update.chat.type != 'channel':
        return

    channel = await session.get(Channel, update.chat.id)
    if channel:
        await session.delete(channel)
        await session.commit()


@router.message(Command("add"))
async def add_channel(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot
):
    if not message.from_user.id in (config.main_admin_id, config.second_admin_id):
        return
    try:
        channel_id, link, months = command.args.split(' ')
        if not channel_id.startswith('-100'):
            channel_id = '-100' + channel_id
        channel_id = int(channel_id)
        months = int(months)
    except:
        await message.answer("Нужно ровно три аргумента -- id канала, ссылка для него и число месяцев")
        return

    today = datetime.date.today()

    is_new_channel = False

    channel = await session.get(Channel, channel_id)
    if not channel:
        channel = Channel()
        channel.channel_id = channel_id
        is_new_channel = True

    channel.link = link
    channel.active_until = today + relativedelta(months=months)
    session.add(channel)
    await session.commit()

    await message.answer('Успешно добавлено!' if is_new_channel else 'Успешно изменено!')
