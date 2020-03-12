"""Checks used in the mapping cog."""
from discord.ext.commands import check
from robowillow.utils import database as db


async def is_map_channel(ctx):
    """Check the permissions database for mapping status."""
    channel_id = ctx.channel.id
    return db.check_permission(channel_id, 'research')


async def is_map_ready(ctx, _map=None):
    """Check if the server map has been properly set up."""
    channel_id = ctx.channel.id

    def check_ready(_map):
        """Check if the map has the required fields."""
        if 'bounds' in _map._data and 'loc' in _map._data and 'timezone' in _map._data:
            return True
        else:
            return False

    if db.check_permission(channel_id, 'map_ready') is False:
        if _map is None:
            try:
                _map = ctx.bot.maps[channel_id]
            except (KeyError):
                return False
        if check_ready(_map) is True:
            db.set_permission(channel_id, 'map_ready', True)
    return db.check_permission(channel_id, 'research') and db.check_permission(channel_id, 'map_ready')


async def is_where_ready(ctx, _map=None):
    """Check if the server map has been properly set up."""
    channel_id = ctx.channel.id

    def check_ready(_map):
        """Check if the map has the required fields."""
        if 'bounds' in _map._data and 'loc' in _map._data and 'timezone' in _map._data:
            return True
        else:
            return False

    if db.check_permission(channel_id, 'map_ready') is False:
        if _map is None:
            try:
                _map = ctx.bot.maps[channel_id]
            except (KeyError):
                return False
        if check_ready(_map) is True:
            db.set_permission(channel_id, 'map_ready', True)
    return (db.check_permission(channel_id, 'raids') or db.check_permission(channel_id, 'research')) and db.check_permission(channel_id, 'map_ready')


def map_channel():
    """Return discord check for map permission."""
    return check(is_map_channel)


def map_ready():
    """Return discord check for map ready."""
    return check(is_map_ready)


def where_ready():
    """Return discord check for map ready."""
    return check(is_where_ready)
