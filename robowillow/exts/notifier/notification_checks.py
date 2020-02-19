"""Checks used in the notification cog."""
from discord.ext.commands import check
from robowillow.utils import database as db


async def is_notification_channel(ctx):
    """Check if the channel has been approved for notifications."""
    if ctx.message.guild is None:
        return True
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'notifier')


def notification_channel():
    """Return discord check format."""
    return check(is_notification_channel)
