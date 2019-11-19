from discord.ext.commands import check
from robowillow.utils import database as db


async def is_trade_channel(ctx):
    if ctx.message.server is None:
        return True
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'trade')


def trade_channel():
    return check(is_trade_channel)
