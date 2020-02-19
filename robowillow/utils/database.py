"""Robowillow database operations in pymongo."""
import pymongo

host = "mongodb://localhost:27017/"
my_client = pymongo.MongoClient(host)
main_db = my_client['main']
permissions = main_db['permissions']
settings = main_db['settings']


def add_channel(channel_id):
    """Add default permissions for a new channel."""
    if not isinstance(channel_id, int):
        channel_id = int(channel_id)
    perm_dict = {"discord_id": channel_id,
                 "trade": False,
                 "research": False,
                 "map_ready": False,
                 "notifier": False,
                 "raids": False}
    permissions.insert_one(perm_dict)


def set_permission(channel_id, permission, value):
    """Set a permission for a discord channel."""
    find_dict = {'discord_id': channel_id}
    channel = permissions.find_one(find_dict)
    if channel is None:
        add_channel(channel_id)
    update_dict = {'$set': {permission: value}}
    permissions.update_one(find_dict, update_dict)


def check_permission(channel_id, permission):
    """Check a permission for a discord channel."""
    find_dict = {'discord_id': channel_id}
    channel = permissions.find_one(find_dict)
    if channel is None:
        add_channel(channel_id)
        return False
    try:
        return channel[permission]
    except KeyError:
        return False


def raid_pokemon(pokemon=None):
    """Check or set the current 5* raid boss."""
    find_dict = {'category': 'Raid Pokemon'}
    raid_settings = settings.find_one(find_dict)
    if raid_settings is None:
        new_dict = {"category": "Raid Pokemon",
                    "5*": None}
        permissions.insert_one(new_dict)
    if pokemon is None:
        return raid_settings['5*']
    else:
        update_dict = {'$set': {'5*': pokemon}}
        settings.update_one(find_dict, update_dict)
