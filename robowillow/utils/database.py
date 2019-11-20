import pymongo

host = "mongodb://localhost:27017/"
my_client = pymongo.MongoClient(host)
main_db = my_client['main']
permissions = main_db['permissions']


def add_channel(channel_id):
    if not isinstance(channel_id, int):
        channel_id = int(channel_id)
    perm_dict = {"discord_id": channel_id,
                 "trade": False,
                 "research": False,
                 "map_ready": False,
                 "notifier": False}
    permissions.insert_one(perm_dict)


def set_permission(channel_id, permission, value):
    find_dict = {'discord_id': channel_id}
    channel = permissions.find_one(find_dict)
    if channel is None:
        add_channel(channel_id)
    update_dict = {'$set': {permission: value}}
    permissions.update_one(find_dict, update_dict)


def check_permission(channel_id, permission):
    find_dict = {'discord_id': channel_id}
    channel = permissions.find_one(find_dict)
    if channel is None:
        add_channel(channel_id)
        return False
    try:
        return channel[permission]
    except KeyError:
        return False
