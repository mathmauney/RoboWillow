from discord.ext.commands import check
from robowillow.utils import database as db


async def is_raid_channel(ctx):
    if ctx.message.guild is None:
        return True
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'raids')


def raid_channel():
    return check(is_raid_channel)
