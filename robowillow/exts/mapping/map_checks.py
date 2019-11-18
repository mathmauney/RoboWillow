from discord.ext.commands import check
from robowillow.utils import database as db


async def is_map_channel(ctx):
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'research')


async def is_map_ready(ctx):
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'research') and ctx.bot.maps[channel_id].check_ready()


def map_channel():
    return check(is_map_channel)


def map_ready():
    return check(is_map_ready)
