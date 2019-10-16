import pymongo

host = "mongodb://mathmauney.no-ip.org:27017/"
my_client = pymongo.MongoClient(host)
trade_db = my_client['trade_test']
users = trade_db['users']
offers = trade_db['offers']

def add_new_user(discord_id, pogo_name):
    user_dict = {"name": pogo_name,
                 "discord_id": discord_id,
                 "offers": []}
    users.insert_one(user_dict)

def find_user(discord_id):
    find_dict = {'discord_id': discord_id}
    return_dict = {}
    user = users.find_one(find_dict, return_dict)
    return user

def add_offer(user, offer_name):
    offer_dict = {"offer_name": offer_name,
                  "user": user,
                  "haves": [],
                  "wants": [],
                  "friends_only": False,
                  "value": 0}
    offers.insert_one(offer_dict)

def find_offer(user, offer_name):
    find_dict = {'offer_name': offer_name,
                 'user': user}
    return_dict = {}
    offer = offers.find_one(find_dict, return_dict)
    return offer

def add_have(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$push': {'haves': pokemon}}
    if isinstance(pokemon, list):
        update_dict = {'$push': {'haves': {'$each': pokemon}}}
    offers.update(offer, update_dict)

def add_want(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$push': {'wants': pokemon}}
    if isinstance(pokemon, list):
        update_dict = {'$push': {'wants': {'$each': pokemon}}}
    offers.update(offer, update_dict)

def get_offer_contents(offer):
    _offer = offers.find_one(offer)
    return (_offer['wants'], _offer['haves'])
