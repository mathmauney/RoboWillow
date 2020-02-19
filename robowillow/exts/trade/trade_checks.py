"""Checks used in the trade cog."""
from discord.ext.commands import check
from robowillow.utils import database as db


async def is_trade_channel(ctx):
    """Check if the channel has been approved for trade commands."""
    if ctx.message.guild is None:
        return True
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'trade')


def trade_channel():
    """Return discord check for trade permissions."""
    return check(is_trade_channel)
