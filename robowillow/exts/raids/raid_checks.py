"""Checks used in the raid cog."""
from discord.ext.commands import check
from robowillow.utils import database as db


async def is_raid_channel(ctx):
    """Check if the channel has been approved for raid commands."""
    if ctx.message.guild is None:
        return True
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'raids')


def raid_channel():
    """Return discord check for raid permissions."""
    return check(is_raid_channel)
