import pymongo

host = "mongodb://mathmauney.no-ip.org:27017/"
my_client = pymongo.MongoClient(host)
trade_db = my_client['trade_test']
users = trade_db['users']
offers = trade_db['offers']


def add_new_user(discord_id, pogo_name):
    check = {'$or': [{"name": pogo_name},
                     {"discord_id": discord_id}]}
    user = users.find_one(check)
    if user is None:
        user_dict = {"name": pogo_name,
                     "discord_id": discord_id,
                     "offers": [],
                     "communities": [],
                     "friends": []}
        users.insert_one(user_dict)
    else:
        raise KeyError("User already exists")


def add_community(user, community_id):
    update_dict = {'$addToSet': {'communities': community_id}}
    users.update(user, update_dict)
    user_offer_ids = users.find_one(user)['offers']
    user_offers = offers.find({'_id': {'$in': user_offer_ids}})
    for user_offer in user_offers:
        offers.update(user_offer, update_dict)


def add_friend(user1, user2):
    user1_dict = users.find_one(user1)
    user2_dict = users.find_one(user2)
    update_dict1 = {'$addToSet': {'friends': user2_dict['_id']}}
    update_dict2 = {'$addToSet': {'friends': user1_dict['_id']}}
    users.update(user1, update_dict1)
    users.update(user2, update_dict2)
    user_offer_ids1 = users.find_one(user1)['offers']
    user_offer_ids2 = users.find_one(user2)['offers']
    user_offers1 = offers.find({'_id': {'$in': user_offer_ids1}})
    user_offers2 = offers.find({'_id': {'$in': user_offer_ids2}})
    for user_offer1 in user_offers1:
        offers.update(user_offer1, update_dict1)
    for user_offer2 in user_offers2:
        offers.update(user_offer2, update_dict2)


def find_user(discord_id):
    find_dict = {'discord_id': discord_id}
    return_dict = {}
    user = users.find_one(find_dict, return_dict)
    return user


def add_offer(user, offer_name):
    if isinstance(user, int):
        user = find_user(user)
    user_dict = users.find_one(user)
    user_communities = user_dict['communities']
    user_friends = user_dict['friends']
    offer_dict = {"offer_name": offer_name,
                  "user": user,
                  "haves": [],
                  "wants": [],
                  "communities": user_communities,
                  "friends": user_friends,
                  "friends_only": False,
                  "value": 0}
    result = offers.insert_one(offer_dict)
    update_dict = {'$addToSet': {'offers': result.inserted_id}}
    users.update(user, update_dict)


def find_offer(user, offer_name):
    if isinstance(user, int):
        user = find_user(user)
    find_dict = {'offer_name': offer_name,
                 'user': user}
    return_dict = {}
    offer = offers.find_one(find_dict, return_dict)
    return offer


def add_have(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$addToSet': {'haves': {'$each': pokemon}}}
    if isinstance(pokemon, list):
        update_dict = {'$addToSet': {'haves': {'$each': pokemon}}}
    offers.update(offer, update_dict)


def add_want(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$addToSet': {'wants': pokemon}}
    if isinstance(pokemon, list):
        update_dict = {'$addToSet': {'wants': {'$each': pokemon}}}
    offers.update(offer, update_dict)


def get_offer_contents(offer):
    _offer = offers.find_one(offer)
    return (_offer['wants'], _offer['haves'])


def find_matches(offer):
    _offer = offers.find_one(offer)
    _wants = _offer['wants']
    _haves = _offer['haves']
    _user_id = _offer['user']['_id']
    _communities = _offer['communities']
    search_dict = {'wants': {'$in': _haves},
                   'haves': {'$in': _wants},
                   '$or': [{'friends': _user_id},
                           {'communities': {'$in': _communities}}]}
    matches = offers.find(search_dict)
    return matches
