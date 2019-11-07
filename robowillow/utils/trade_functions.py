import pymongo
from robowillow.utils import pokemap
import urllib.parse as urlparse

host = "mongodb://localhost:27017/"
my_client = pymongo.MongoClient(host)
trade_db = my_client['trade_test']
users = trade_db['users']
offers = trade_db['offers']


def add_user(discord_id):
    if not isinstance(discord_id, int):
        discord_id = int(discord_id)
    check = {"discord_id": discord_id}
    user = users.find_one(check)
    if user is None:
        user_dict = {"name": '',
                     "discord_id": discord_id,
                     "offers": [],
                     "communities": [],
                     "friends": []}
        users.insert_one(user_dict)
        return get_user(discord_id)
    else:
        raise ValueError("User already exists")


def set_name(user, pogo_name=None):
    if pogo_name is None:
        update_dict = {'$set': {'name': ''}}
    else:
        check = {"name": pogo_name}
        check_user = users.find_one(check)
        if check_user is not None:
            if check_user != users.find_one(user):
                raise ValueError("Name already used")
        update_dict = {'$set': {'name': pogo_name}}
    users.update_one(user, update_dict)
    user_offer_ids = users.find_one(user)['offers']
    offers.update_many({'_id': {'$in': user_offer_ids}}, update_dict)


def add_community(user, community_id):
    if community_id not in users.find_one(user)['communities']:
        update_dict = {'$addToSet': {'communities': int(community_id)}}
        users.update(user, update_dict)
        user_offer_ids = users.find_one(user)['offers']
        offers.update_many({'_id': {'$in': user_offer_ids}}, update_dict)


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


def get_user(discord_id):
    if not isinstance(discord_id, int):
        discord_id = int(discord_id)
    find_dict = {'discord_id': discord_id}
    return_dict = {}
    user = users.find_one(find_dict, return_dict)
    return user


def find_user(pogo_name):
    find_dict = {'name': pogo_name}
    return_dict = {}
    user = users.find_one(find_dict, return_dict)
    return user


def delete_user(discord_id):
    user = get_user(discord_id)
    for offer in users.find_one(user)['offers']:
        offers.delete_one({'_id': offer})
    users.delete_one(user)


def add_offer(user, offer_name):
    if isinstance(user, int):
        user = get_user(user)
    user_dict = users.find_one(user)
    user_communities = user_dict['communities']
    user_friends = user_dict['friends']
    offer_dict = {"offer_name": offer_name.lower(),
                  "user": user,
                  "name": user_dict['name'],
                  "haves": [],
                  "wants": [],
                  "communities": user_communities,
                  "friends": user_friends,
                  "friends_only": False,
                  "value": 0,
                  "notified": []}
    result = offers.insert_one(offer_dict)
    update_dict = {'$addToSet': {'offers': result.inserted_id}}
    users.update(user, update_dict)


def find_offer(user, offer_name):
    if isinstance(user, int):
        user = get_user(user)
    find_dict = {'offer_name': offer_name.lower(),
                 'user': user}
    return_dict = {}
    offer = offers.find_one(find_dict, return_dict)
    return offer


def find_offers(user):
    if isinstance(user, int):
        user = get_user(user)
    offer_names = []
    offer_list = users.find_one(user)['offers']
    for offer in offer_list:
        offer_dict = offers.find_one({'_id': offer})
        if offer_dict is not None:
            offer_names.append(offer_dict['offer_name'])
    return offer_names


def add_haves(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$addToSet': {'haves': pokemon}}
    elif isinstance(pokemon, list):
        update_dict = {'$addToSet': {'haves': {'$each': pokemon}}}
    offers.update(offer, update_dict)


def add_wants(offer, pokemon):
    if isinstance(pokemon, str):
        update_dict = {'$addToSet': {'wants': pokemon}}
    elif isinstance(pokemon, list):
        update_dict = {'$addToSet': {'wants': {'$each': pokemon}}}
    offers.update(offer, update_dict)


def remove_haves(offer, pokemon):
    if pokemon == 'all':
        update_dict = {'$set': {'haves': []}}
    elif isinstance(pokemon, str):
        update_dict = {'$pull': {'haves': pokemon}}
    if isinstance(pokemon, list):
        update_dict = {'$pullAll': {'haves': pokemon}}
    offers.update(offer, update_dict)


def remove_wants(offer, pokemon):
    if pokemon == 'all':
        update_dict = {'$set': {'wants': []}}
    elif isinstance(pokemon, str):
        update_dict = {'$pull': {'wants': pokemon}}
    if isinstance(pokemon, list):
        update_dict = {'$pullAll': {'wants': pokemon}}
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
                   'user': {'$not': _offer['user']},
                   '$or': [{'friends': _user_id},
                           {'communities': {'$in': _communities}}]}
    matches = offers.find(search_dict)
    return matches


def parse_matches(offer):
    matches = find_matches(offer)
    offer_dict = offers.find_one(offer)
    parsed = []
    for match in matches:
        discord_id = users.find_one(match['user'])['discord_id']
        matching_wants = [pokemon for pokemon in offer_dict['wants'] if pokemon in match['haves']]
        matching_haves = [pokemon for pokemon in offer_dict['haves'] if pokemon in match['wants']]
        parsed.append((matching_wants, matching_haves, discord_id, match['_id']))
    return parsed


def set_notified(offer, user_id):
    update_dict = {'$addToSet': {'notified': user_id}}
    offers.update(offer, update_dict)


def delete_offer(offer):
    offer_dict = offers.find_one(offer)
    user = offer_dict['user']
    offers.delete_one(offer)
    update_dict = {'$pull': {'offers': offer_dict['_id']}}
    users.update(user, update_dict)


def clean_pokemon_list(pokemon_list, all_shinies=False):
    if 'leekduck' in pokemon_list[0]:
        url_str = pokemon_list[0]
        cleaned_list = parse_leekduck(url_str)
        return cleaned_list
    cleaned_list = []
    numbered_pokemon = ['Unown', 'Spinda']
    form = None
    shiny = False
    alolan = False
    prev_space = False
    for (i, poke) in enumerate(pokemon_list):
        poke = poke.strip(',')
        if poke.title() == 'Shiny':
            shiny = True
        elif poke.title() == 'Alolan':
            alolan = True
        elif poke.title() == 'Shinies':
            all_shinies = True
        else:
            matched_poke = pokemap.match_pokemon(poke)
            if all_shinies is True:
                shiny = True
            if matched_poke is None and prev_space is False:
                with open('pokemonwithspaces.txt') as file:
                    if poke.title() in file.read():
                        prev_space = True
                        print('Found spacey boi')
                        new_poke = pokemon_list[i-1] + ' ' + poke
                        print('Trying to match %s' % new_poke)
                        matched_poke = pokemap.match_pokemon(new_poke)
                        if matched_poke is None:
                            new_poke = poke + ' ' + pokemon_list[i+1]
                            print('Trying to match %s' % new_poke)
                            matched_poke = pokemap.match_pokemon(new_poke)
            else:
                prev_space = False
            if form is not None and matched_poke is not None:
                matched_form = pokemap.match_form(matched_poke, form)
                if matched_form is not None:
                    matched_poke = matched_form
            if matched_poke is not None:
                if matched_poke in numbered_pokemon:
                    if '-' in poke:
                        modifier = poke.split('-')[1]
                        if len(modifier) == 1:
                            matched_poke = matched_poke + '-' + modifier.title()
                    else:
                        try:
                            if len(pokemon_list[i+1]) == 1:
                                matched_poke = matched_poke + '-' + pokemon_list[i+1].title()
                                prev_space = True
                        except IndexError:
                            pass
                elif matched_poke == 'Giratina' and '-' in poke:
                    modifier = poke.split('-')[1].title()
                    if modifier.startswith('O'):
                        matched_poke = 'Origin Forme Giratina'
                    elif modifier.startswith('A'):
                        matched_poke = 'Altered Forme Giratina'
                elif i+1 != len(pokemon_list):
                    with open('forms.txt') as file:
                        if matched_poke in file.read():
                            matched_form = pokemap.match_form(matched_poke, pokemon_list[i+1])
                            if matched_form != matched_poke and matched_form is not None:
                                matched_poke = matched_form
                                prev_space = True
                if shiny is True and alolan is True:
                    cleaned_list.append('Shiny Alolan ' + matched_poke)
                    shiny = False
                    alolan = False
                    form = None
                elif shiny is True:
                    cleaned_list.append('Shiny ' + matched_poke)
                    shiny = False
                    form = None
                elif alolan is True:
                    cleaned_list.append('Alolan ' + matched_poke)
                    alolan = False
                    form = None
                else:
                    cleaned_list.append(matched_poke)
                    form = None
            else:
                if form is None:
                    form = poke
                else:
                    form = form + ' ' + poke
    return cleaned_list


def parse_leekduck(url_str):
    parsed = urlparse.urlparse(url_str)
    query_parsed = urlparse.parse_qs(url_str)
    return_list = []
    if 'leekduck' not in parsed[1]:
        raise InvalidUrl
        return
    pokemon_list = query_parsed['https://leekduck.com/shiny/?dex'][0].split('-')
    for pokemon in pokemon_list:
        if '_' in pokemon:
            if pokemon.split('_')[1] == '61':
                poke_str = 'Alolan ' + pokemap.match_pokemon(int(pokemon.split('_')[0]))
            if pokemon.split('_')[0] == '327':
                poke_str = 'Spinda-' + str(int(pokemon.split('_')[1])-10)
            else:
                poke_str = pokemap.match_form(pokemon)
        elif 'Fall' in pokemon:
            poke_str = pokemap.match_form(pokemon)
        else:
            poke_str = pokemap.match_pokemon(int(pokemon))
        if poke_str is not None:
            return_list.append('Shiny ' + poke_str)
        else:
            print('Unable to find %s' % pokemon)
    return return_list


def search_haves(user, pokemon):
    user_dict = users.find_one(user)
    search_dict = {'haves': pokemon,
                   '$and': [{'name': {'$ne': ''}}, {'name': {'$exists': True}}],
                   'user': {'$ne': user},
                   '$or': [{'friends': user_dict['discord_id']},
                           {'communities': {'$in': user_dict['communities']}}]}
    matches = offers.find(search_dict)
    output = []
    for match in matches:
        matched_user = users.find_one(match['user'])
        output.append((matched_user['discord_id'], matched_user['name'], match['offer_name']))
    return output


def search_wants(user, pokemon):
    user_dict = users.find_one(user)
    search_dict = {'wants': pokemon,
                   '$and': [{'name': {'$ne': ''}}, {'name': {'$exists': True}}],
                   'user': {'$ne': user},
                   '$or': [{'friends': user_dict['discord_id']},
                           {'communities': {'$in': user_dict['communities']}}]}
    matches = offers.find(search_dict)
    output = []
    for match in matches:
        matched_user = users.find_one(match['user'])
        output.append((matched_user['discord_id'], matched_user['name'], match['offer_name']))
    return output


class TradeException(Exception):
    """Base class for the module so all module exceptions can be caught together if needed."""

    def __init__(self):
        """Add default message."""
        self.message = 'No error message set, contact maintainer'


class InvalidUrl(TradeException):
    """Exception for when stop not found with the given search string."""

    def __init__(self):
        """Add message based on context of error."""
        self.message = "Unexpected URL type."
