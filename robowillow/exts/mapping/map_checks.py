from discord.ext.commands import check
from robowillow.utils import database as db


async def is_map_channel(ctx):
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'research')


async def is_map_ready(ctx, _map=None):
    channel_id = ctx.channel.id

    def check_ready(_map):
        """Check if the map has the required fields."""
        if 'bounds' in _map._data and 'loc' in _map._data and 'timezone' in _map._data:
            print("True")
            return True
        else:
            print("False")
            return False
    if _map is None:
        try:
            _map = ctx.bot.maps[channel_id]
            return db.check_permission(channel_id, 'research') and check_ready(_map)
        except (KeyError):
            return False
    return db.check_permission(channel_id, 'research') and check_ready(_map)


def map_channel():
    return check(is_map_channel)


def map_ready():
    return check(is_map_ready)
