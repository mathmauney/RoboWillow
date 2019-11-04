"""Discord bot for mapping out pokemon go research and other misc functions."""
import asyncio
import pokemap
import pickle
import discord
import inspect
from datetime import datetime
from discord import Game
from discord.ext.commands import Bot, has_permissions
from config import discord_token
import urllib.parse as urlparse

# Setup Variables
bot_prefix = ("?")   # Tells bot which prefix(or prefixes) to look for. Multiple prefixes can be specified in a tuple, however all help messages will use the first item for examples
map_dir = '/var/www/html/maps/'  # Path the saved map, in geojson format. http://geojson.io/ can be used to create basic maps, or the bot can do it interactively
task_path = 'tasklist.pkl'   # Location to save the tasklist to and load it from if the bot is restarted
map_url = 'http://robowillow.ddns.net'
bot_game = "with maps at robowillow.net"
maintainer_handle = '@mathmauney'
maintainer_id = 200038656021364736


# Load In Saved Data
# Initialize Map Object
maps = {}
prev_message_was_stop = {}
prev_message_stop = {}
prev_message = {}
prev_matches = {}
prev_views = {}
prev_search = {}
# Import the tasklist object or create new one
try:
    with open(task_path, 'rb') as file_input:
        tasklist = pickle.load(file_input)
except FileNotFoundError:
    tasklist = pokemap.Tasklist()

# Startup Bot Instance
client = Bot(command_prefix=bot_prefix)


# Sets the bots playing status
@client.event
async def on_ready():
    """Take actions on login."""
    await client.change_presence(game=Game(name=bot_game))  # Sets the game presence
    print("Logged in as " + client.user.name)  # Logs sucessful login
    for server in client.servers:
        print(server.id)
        map_path = map_dir + str(server.id) + '.json'
        try:
            taskmap = pokemap.load(map_path)
            reset_bool = taskmap.reset_old()
            if reset_bool:
                taskmap.save(map_path)
            print('Map successfully loaded, map time is: ' + taskmap.now().strftime("%Y.%m.%d.%H%M%S"))
        except FileNotFoundError:
            taskmap = pokemap.new()
            print('No map found at: ' + map_path + '. Creating new map now')
        taskmap._data['path'] = map_path
        maps[server.id] = taskmap
        prev_message_was_stop[server.id] = False


@client.event
async def on_server_join(server):
    """Take actions on server join."""
    print(server.id)
    map_path = map_dir + str(server.id) + '.json'
    try:
        taskmap = pokemap.load(map_path)
        reset_bool = taskmap.reset_old()
        if reset_bool:
            taskmap.save(map_path)
        print('Map successfully loaded, map time is: ' + taskmap.now().strftime("%Y.%m.%d.%H%M%S"))
    except FileNotFoundError:
        taskmap = pokemap.new()
        print('No map found at: ' + map_path + '. Creating new map now')
    taskmap._data['path'] = map_path
    maps[server.id] = taskmap


# Bot Command Definitions
async def bot_respond(message, response):
    """Send a simple response.

    Command for the bot to send a simple response, checking to see if the channel has the correct permissions.
    If the bot can't say what it wants it sends the user a PM indicating that they tried to use a command in the wrong channel.
    """
    try:
        if message.server is None:
            await client.send_message(message.author, response)
        else:
            await client.send_message(message.channel, response)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")


async def bot_embed_respond(message, msg):
    """Send an embed as a response.

    Command for the bot to send an embed response, checking to see if the channel has the correct permissions.
    If the bot can't say what it wants it sends the user a PM indicating that they tried to use a command in the wrong channel.
    """
    try:
        if message.server is None:
            await client.send_message(message.author, embed=msg)
        else:
            await client.send_message(message.channel, embed=msg)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")


def pass_errors(func):
    """Pass library errors into a discord message."""
    async def decorator(*args, **kwargs):
        try:
            await func(*args, **kwargs)
            return
        except pokemap.PokemapException as e:
            await client.say(e.message)
            return
    decorator.__name__ = func.__name__
    decorator.__signature__ = inspect.signature(func)
    return decorator


async def bot_thumbsup(message):
    await client.add_reaction(message, '👍')


async def bot_x(message):
    await client.add_reaction(message, '❌')


async def process_matches(message, offer, reply=False):
    """Check for matches on an offer and notify both parties if there are matches."""
    matches = tf.parse_matches(offer)
    offer_dict = tf.offers.find_one(offer)
    sender = message.author
    # matches = [(['Squirtle', 'Charmander'], ['Bulbasaur', 'Pikachu', 'Raichu'], 200038656021364736)]
    embed_components = []
    for match in matches:
        if len(match[0]) == 1:
            want_str = match[0][0]
        elif len(match[0]) == 2:
            want_str = ' or '.join(match[0])
        else:
            want_str = ', '.join(match[0][:-1]) + ', or ' + match[0][-1]
        if len(match[1]) == 1:
            have_str = match[1][0]
        elif len(match[1]) == 2:
            have_str = ' or '.join(match[1])
        else:
            have_str = ', '.join(match[1][:-1]) + ', or ' + match[1][-1]
        embed_components.append((want_str, have_str, match[2]))
        match_user_id = match[2]
        if match_user_id not in offer_dict['notified']:
            notification = "Trade matched! Your %s for <@%s>'s %s" % (want_str, str(sender.id), have_str)
            match_user = await client.get_user_info(match_user_id)
            await client.send_message(match_user, notification)
            tf.set_notified(offer, match_user_id)
        other_offer = tf.offers.find_one(match[3])
        tf.set_notified(other_offer, int(sender.id))
    if embed_components != []:
        embed_strs = ['']
        embed_num = 0
        for component in embed_components:
            to_add = "Your %s for <@%s>'s %s.\n" % (component[1], str(component[2]), component[0])
            if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
                embed_num += 1
                embed_strs.append('')
            embed_strs[embed_num] += to_add
        prev_matches[message.author.id] = embed_strs
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.add_field(name='Matches', value=embed_strs[0], inline=False)
        embed.set_footer(text='Page 1 of %s. Use %smorematches n to see page n.' % (len(embed_strs), bot_prefix[0]))
        await bot_embed_respond(message, embed)
    elif reply is True:
        await bot_respond(message, 'No matches found')


@client.command(pass_context=True)
async def morematches(ctx, page):
    embed_strs = prev_matches.get(ctx.message.author.id, None)
    if int(page) > len(embed_strs):
        await bot_respond(ctx.message, 'Page out of range')
    if embed_strs is not None:
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.add_field(name='Matches', value=embed_strs[int(page)-1], inline=False)
        embed.set_footer(text='Page %s of %s. Use %smorematches n to see page n.' % (page, len(embed_strs), bot_prefix[0]))
        await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def moreresults(ctx, page):
    embed_strs = prev_search.get(ctx.message.author.id, None)
    if int(page) > len(embed_strs):
        await bot_respond(ctx.message, 'Page out of range')
    if embed_strs is not None:
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.add_field(name='Search Results', value=embed_strs[int(page)-1], inline=False)
        embed.set_footer(text='Page %s of %s. Use %smoreresults n to see page n.' % (page, len(embed_strs), bot_prefix[0]))
        await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def tradehere(ctx):
    """Find the server ID."""
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
        await client.send_message(ctx.message.author, "Adding you to community: " + str(ctx.message.server.id))


@client.command(pass_context=True)
async def addoffer(ctx, offer_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    if tf.find_offer(user, offer_name) is None:
        tf.add_offer(user, offer_name)
        await bot_thumbsup(ctx.message)
    else:
        await bot_respond(ctx.message, "Offer group already exists.")


@client.command(pass_context=True)
async def deleteoffer(ctx, offer_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    if offer is not None:
        tf.delete_offer(offer)
        await bot_thumbsup(ctx.message)
    else:
        await bot_respond(ctx.message, 'Unable to find offer')


@client.command(pass_context=True, aliases=['deletewants'])
async def deletewant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    if len(pokemon) == 0 or pokemon[0] == 'all':
        tf.remove_wants(offer, 'all')
        await bot_respond(ctx.message, 'Removed all wants')
    else:
        cleaned_list = tf.clean_pokemon_list(pokemon)
        tf.remove_wants(offer, cleaned_list)
        await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_list))


@client.command(pass_context=True, aliases=['deletehaves'])
async def deletehave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    if len(pokemon) == 0 or pokemon[0] == 'all':
        tf.remove_haves(offer, 'all')
        await bot_respond(ctx.message, 'Removed all haves')
    else:
        cleaned_list = tf.clean_pokemon_list(pokemon)
        tf.remove_haves(offer, cleaned_list)
        await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_list))


@client.command(pass_context=True, aliases=['addwants'])
async def addwant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon)
    tf.add_wants(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_list))
        await process_matches(ctx.message, offer)


@client.command(pass_context=True, aliases=['addhaves'])
async def addhave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon)
    tf.add_haves(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_list))
        await process_matches(ctx.message, offer)


@client.command(pass_context=True, aliases=['deleteshinywants'])
async def deleteshinywant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon, True)
    tf.remove_wants(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_list))


@client.command(pass_context=True, aliases=['deleteshinyhaves'])
async def deleteshinyhave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon, True)
    tf.remove_haves(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_list))


@client.command(pass_context=True, aliases=['addshinywants'])
async def addshinywant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon, True)
    tf.add_wants(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_list))
        await process_matches(ctx.message, offer)


@client.command(pass_context=True, aliases=['addshinyhaves'])
async def addshinyhave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_list = tf.clean_pokemon_list(pokemon, True)
    tf.add_haves(offer, cleaned_list)
    if len(cleaned_list) == 0:
        await bot_x(ctx.message)
    else:
        await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_list))
        await process_matches(ctx.message, offer)


@client.command(pass_context=True, aliases=['viewoffer'])
async def view(ctx, *args):
    if len(args) == 1:
        offer_name = args[0]
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.server is not None:
            tf.add_community(user, ctx.message.server.id)
        offer = tf.find_offer(user, offer_name)
        if offer is None:
            await bot_respond(ctx.message, 'Offer not found')
            return
        (wants, haves) = tf.get_offer_contents(offer)
        if haves == []:
            have_strs = ['None']
            want_strs = ['']
        else:
            i = 0
            have_strs = ['']
            want_strs = ['']
            for have in haves:
                if len(have_strs[i]) > 500:
                    i = i + 1
                    have_strs.append('')
                    want_strs.append('')
                have_strs[i] = have_strs[i] + have + '\n'
        if wants == []:
            want_strs[0] = 'None'
        else:
            i = 0
            for want in wants:
                if len(want_strs[i]) > 500:
                    i = i + 1
                    if i >= len(have_strs):
                        have_strs.append('')
                        want_strs.append('')
                want_strs[i] = want_strs[i] + want + '\n'
        prev_views[ctx.message.author.id] = (have_strs, want_strs)
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.set_footer(text='Page 1 of %s. Use %sviewmore n to see page n.' % (len(want_strs), bot_prefix[0]))
        embed.add_field(name='Have', value=have_strs[0], inline=False)
        embed.add_field(name='Want', value=want_strs[0], inline=False)
        await bot_embed_respond(ctx.message, embed)
    elif len(args) >= 2:
        pogo_name = args[0]
        user = tf.find_user(pogo_name.title())
        if user is None:
            await bot_respond(ctx.message, 'User not found')
        else:
            search_terms = args[1:]
            if len(search_terms) == 1:
                offer_name = search_terms[0]
                offer = tf.find_offer(user, offer_name)
                (wants, haves) = tf.get_offer_contents(offer)
                if haves == []:
                    have_strs = ['None']
                    want_strs = ['']
                else:
                    i = 0
                    have_strs = ['']
                    want_strs = ['']
                    for have in haves:
                        if len(have_strs[i]) > 500:
                            i = i + 1
                            have_strs.append('')
                            want_strs.append('')
                        have_strs[i] = have_strs[i] + have + '\n'
                if wants == []:
                    want_strs[0] = 'None'
                else:
                    i = 0
                    for want in wants:
                        if len(want_strs[i]) > 500:
                            i = i + 1
                            if i >= len(have_strs):
                                have_strs.append('')
                                want_strs.append('')
                        want_strs[i] = want_strs[i] + want + '\n'
                prev_views[ctx.message.author.id] = (have_strs, want_strs)
                embed = discord.Embed(colour=discord.Colour(0x186a0))
                embed.set_footer(text='Page 1 of %s. Use %sviewmore n to see page n.' % (len(want_strs), bot_prefix[0]))
                embed.add_field(name='Haves', value=have_strs[0], inline=False)
                embed.add_field(name='Wants', value=want_strs[0], inline=False)
                await bot_embed_respond(ctx.message, embed)
            else:
                await bot_respond(ctx.message, 'Too many arguments')


@client.command(pass_context=True)
async def viewmore(ctx, page):
    (have_strs, want_strs) = prev_views.get(ctx.message.author.id, (None, None))
    if int(page) > len(have_strs):
        await bot_respond(ctx.message, 'Page out of range')
    if have_strs is not None:
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        have_str = have_strs[int(page)-1]
        want_str = want_strs[int(page)-1]
        if have_str != '':
            embed.add_field(name='Haves', value=have_str, inline=False)
        if want_str != '':
            embed.add_field(name='Wants', value=want_str, inline=False)
        embed.set_footer(text='Page %s of %s. Use %sviewmore n to see page n.' % (page, len(want_strs), bot_prefix[0]))
        await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def check(ctx, offer_name=None):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    if offer_name is None:
        await bot_respond(ctx.message, "No offer group supplied")
        return
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    await process_matches(ctx.message, offer, True)


@client.command(pass_context=True, aliases=['viewoffers'])
async def listoffers(ctx, *args):
    if len(args) == 0:
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.server is not None:
            tf.add_community(user, ctx.message.server.id)
        offer_names = tf.find_offers(user)
        if offer_names == []:
            await bot_respond(ctx.message, 'No offers found')
        else:
            offer_str = '\n'.join(offer_names)
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Offer Names', value=offer_str, inline=False)
            await bot_embed_respond(ctx.message, embed)
    elif len(args) == 1:
        pogo_name = args[0]
        user = tf.find_user(pogo_name.title())
        if user is None:
            await bot_respond(ctx.message, 'User not found')
            return
        offer_names = tf.find_offers(user)
        if offer_names == []:
            await bot_respond(ctx.message, 'No offers found')
            return
        else:
            offer_str = '\n'.join(offer_names)
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Offer Names', value=offer_str, inline=False)
            await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def setname(ctx, pogo_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    try:
        tf.set_name(user, pogo_name.title())
        await bot_thumbsup(ctx.message)
    except ValueError:
        await bot_respond(ctx.message, 'Name already in use, please contact <@%s> if you think this is in error.' % maintainer_id)


@client.command(pass_context=True, aliases=['searchhaves'])
async def searchhave(ctx, *search_terms):
    cleaned_list = tf.clean_pokemon_list(search_terms)
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if len(cleaned_list) != 1:
        await bot_respond(ctx.message, 'Too many or too few pokemon matched: ' % ', '.join(cleaned_list))
        return
    results = tf.search_haves(user, cleaned_list[0])
    if len(results) == 0:
        await bot_respond(ctx.message, 'No public offers matching query found.')
        return
    embed_strs = ['']
    embed_num = 0
    for result in results:
        to_add = "%s (<@%s>)'s offer: %s.\n" % (result[1], str(result[0]), result[2])
        if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
            embed_num += 1
            embed_strs.append('')
        embed_strs[embed_num] += to_add
    prev_search[ctx.message.author.id] = embed_strs
    embed = discord.Embed(colour=discord.Colour(0x186a0))
    embed.add_field(name='Search Results', value=embed_strs[0], inline=False)
    embed.set_footer(text='Page 1 of %s. Use %smoreresults n to see page n.' % (len(embed_strs), bot_prefix[0]))
    await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True, aliases=['searchwants'])
async def searchwant(ctx, *search_terms):
    cleaned_list = tf.clean_pokemon_list(search_terms)
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if len(cleaned_list) != 1:
        await bot_respond(ctx.message, 'Too many or too few pokemon matched: ' % ', '.join(cleaned_list))
        return
    results = tf.search_wants(user, cleaned_list[0])
    if len(results) == 0:
        await bot_respond(ctx.message, 'No public offers matching query found.')
        return
    embed_strs = ['']
    embed_num = 0
    for result in results:
        to_add = "%s (<@%s>)'s offer: %s.\n" % (result[1], str(result[0]), result[2])
        if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
            embed_num += 1
            embed_strs.append('')
        embed_strs[embed_num] += to_add
    prev_search[ctx.message.author.id] = embed_strs
    embed = discord.Embed(colour=discord.Colour(0x186a0))
    embed.add_field(name='Search Results', value=embed_strs[0], inline=False)
    embed.set_footer(text='Page 1 of %s. Use %smoreresults n to see page n.' % (len(embed_strs), bot_prefix[0]))
    await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def addstop(ctx, *args):
    """Add a stop to the map, contains multiple ways of doing so.

    Expects either:
    !addstop stop name lat long             Stop name can be multiple words or symbols, but doesn't parse " marks correctly
    !addstop stop name ingress_url          ingress_url can be found from the ingress intel map, details in the help description
    """
    taskmap = maps[ctx.message.server.id]
    n_args = len(args)
    if args[-1].startswith('https:'):  # Checks if the lat/long has been given as an ingress intel URL
        url_str = args[-1]
        parsed = urlparse.urlparse(url_str)
        query_parsed = urlparse.parse_qs(url_str)
        if 'ingress' in parsed[1]:   # Check if ingress url
            name_args = args[0:n_args - 1]
            name = ' '.join(name_args)
            ingress_url = args[-1]
            pll_location = ingress_url.find('pll')  # Finds the part of the url that describes the portal location
            if pll_location != -1:
                comma_location = ingress_url.find(',', pll_location)  # Finds the comma in the portal location and then splits into lat and long
                lat = float(ingress_url[pll_location + 4:comma_location])
                long = float(ingress_url[comma_location + 1:])
            else:  # If no portal location data was found in the URL
                await client.say('No portal location data in URL.')
                return
        elif 'apple' in parsed[1]:  # Check if apple maps url
            name = query_parsed['q'][0]
            lat = float(query_parsed['ll'][0].split(',')[0])
            long = float(query_parsed['ll'][0].split(',')[1])
    elif n_args > 2:
        lat = float(args[n_args - 2])
        long = float(args[n_args - 1])
        name_args = args[0:n_args - 2]
        name = ' '.join(name_args)
    else:
        await client.say('Not enough arguments. Please give the stop a name and the latitude and longitude. Use the "' + bot_prefix[0] + 'help addstop" command for detailed instructions')
    try:
        taskmap.new_stop([long, lat], name)
        taskmap.save()
        await client.say('Creating stop named: ' + name + ' at [' + str(lat) + ', ' + str(long) + '].')
    except pokemap.PokemapException as e:
        await client.say(e.message)


@client.command(pass_context=True)
async def settask(ctx, *args):
    """Set a task to a stop."""
    taskmap = maps[ctx.message.server.id]
    n_args = len(args)
    if n_args > 1:
        try:
            task_str = args[0]
            stop_args = args[1:]
            stop_name = ' '.join(stop_args)
            stop_name = stop_name.title()
            stop = taskmap.find_stop(stop_name)
            task = tasklist.find_task(task_str)
            stop.set_task(task)
            if task_str.title() in task.rewards:
                stop.properties['Icon'] = task_str.title()
            await client.add_reaction(ctx.message, '👍')
            taskmap.save()
        except pokemap.PokemapException as e:
            await client.say(e.message)
    else:
        await client.say('Not enough arguments.')


@client.command(pass_context=True)
@pass_errors
async def resetstop(ctx, *args):
    """Reset the task associated with a stop."""
    taskmap = maps[ctx.message.server.id]
    stop_name = ' '.join(args)
    stop_name = stop_name
    stop = taskmap.find_stop(stop_name)
    stop.reset()
    taskmap.save()
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@pass_errors
async def addtask(ctx, reward, quest, shiny=False):
    """Add a task to a stop."""
    tasklist.add_task(pokemap.Task(reward, quest, shiny))
    tasklist.save(task_path)
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@pass_errors
async def resettasklist(ctx):
    """Backup and reset the tasklist."""
    backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
    tasklist.save(backup_name)
    tasklist.clear()
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@pass_errors
async def pulltasklist(ctx):
    """Pull tasks from TheSilphRoad."""
    global tasklist
    backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
    tasklist.save(backup_name)
    tasklist = pokemap.fetch_tasklist()
    tasklist.save(task_path)
    await client.add_reaction(ctx.message, '👍')


@client.command(aliases=['tasklist'])
@pass_errors
async def listtasks():
    """List the known tasks."""
    value_str = []
    str_num = 0
    value_str.append('')
    if tasklist.tasks == []:
        await client.say("No tasks known")
    else:
        for tasks in tasklist.tasks:
            to_add = tasks.quest + ' for a ' + tasks.reward
            if tasks.shiny is True:
                to_add += ' ✨'
            if tasks.reward_type == 'Rare Candy':
                to_add += ' 🍬'
            to_add += '\n'
            if (len(value_str[str_num]) + len(to_add) > 1000):
                str_num += 1
                value_str.append('')
            value_str[str_num] += to_add
        for i in range(len(value_str)):
            msg = discord.Embed(colour=discord.Colour(0x186a0))
            msg.add_field(name='Currently Known Tasks', value=value_str[i], inline=False)
            await client.say(embed=msg)


@client.command(pass_context=True)
@pass_errors
async def deletestop(ctx, *args):
    """Delete a stop."""
    taskmap = maps[ctx.message.server.id]
    stop_str = ' '.join(args)
    stop = taskmap.find_stop(stop_str)
    taskmap.remove_stop(stop)
    taskmap.save()
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@pass_errors
async def deletetask(ctx, task_str):
    """Delete a task."""
    task = tasklist.find_task(task_str)
    tasklist.remove_task(task)
    tasklist.save(task_path)
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@pass_errors
async def nicknamestop(ctx, stop_name, nickname):
    """Add a nickname to a stop."""
    taskmap = maps[ctx.message.server.id]
    stop = taskmap.find_stop(stop_name)
    stop.add_nickname(nickname)
    taskmap.save()
    await client.add_reaction(ctx.message, '👍')


@client.command()
@pass_errors
async def nicknametask(task_name, nickname):
    """Add a nickname to a task."""
    task = tasklist.find_task(task_name)
    task.add_nickname(nickname)
    tasklist.save(task_path)
    await client.add_reaction(ctx.message, '👍')


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def setlocation(ctx, lat, long):
    """Set the location of the map for the web view."""
    taskmap = maps[ctx.message.server.id]
    taskmap.set_location(float(lat), float(long))
    try:
        taskmap.save()
        await client.add_reaction(ctx.message, '👍')
    except ValueError:
        pass


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def resetall(ctx):
    """Set the location of the map for the web view."""
    taskmap = maps[ctx.message.server.id]
    taskmap.reset_all()
    taskmap.save()


@client.command(pass_context=True)
@pass_errors
async def resetmap(ctx, server_id):
    """Allow bot owner to reset any map remotely."""
    if int(ctx.message.author.id) == int(maintainer_id):
        taskmap = maps[server_id]
        taskmap.reset_all()
        taskmap.save()
        await client.add_reaction(ctx.message, '👍')
    else:
        await client.say("Sorry you can't do that" + ctx.message.author.id)


@client.command(pass_context=True)
@pass_errors
async def resetallmaps(ctx):
    """Allow bot owner to reset any map remotely."""
    if int(ctx.message.author.id) == int(maintainer_id):
        for taskmap in maps.values():
            taskmap.reset_all()
            taskmap.save()
            await client.say("Reset map: " + taskmap._data['path'])
    else:
        await client.say("Sorry you can't do that" + ctx.message.author.id)


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def setbounds(ctx, lat1, long1, lat2, long2):
    """Set the boundaries of the maps for checking when pokestops are added."""
    taskmap = maps[ctx.message.server.id]
    coords1 = [float(lat1), float(long1)]
    coords2 = [float(lat2), float(long2)]
    taskmap.set_bounds(coords1, coords2)
    try:
        taskmap.save()
        await client.add_reaction(ctx.message, '👍')
    except ValueError:
        pass


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def settimezone(ctx, tz_str):
    """Set the timezone of the map so it resets itself correctly."""
    taskmap = maps[ctx.message.server.id]
    taskmap.set_time_zone(tz_str)
    try:
        taskmap.save()
        await client.add_reaction(ctx.message, '👍')
    except ValueError:
        pass


@client.command(pass_context=True)
@pass_errors
async def want(ctx, *roles):
    """Set a given pokemon sighting role to a user."""
    all_pokemon = True
    bad = ''
    for role in roles:
        match = pokemap.match_pokemon(role)
        if match is not None:
            user = ctx.message.author
            role_obj = discord.utils.get(ctx.message.server.roles, name=match.lower())
            if role_obj is None:
                await client.create_role(ctx.message.server, name=match.lower(), mentionable=True)
                role_obj = discord.utils.get(ctx.message.server.roles, name=match.lower())
            await client.add_roles(user, role_obj)
        else:
            bad += ' ' + role
            all_pokemon = False
    if all_pokemon:
        await client.add_reaction(ctx.message, '👍')
    else:
        await client.say('Not all requests matched known pokemon. Unable to match:' + bad)


@client.command(pass_context=True)
@pass_errors
async def unwant(ctx, *roles):
    """Remove sighting role(s) from a user."""
    bad = ''
    for role in roles:
        role = role.strip(',')
        if role.lower() == 'all':
            user = ctx.message.author
            roles = ctx.message.author.roles
            for role in roles:
                match = pokemap.match_pokemon(role)
                if match is not None:
                    await client.remove_roles(user, role)
            await client.add_reaction(ctx.message, '👍')
            return
        else:
            match = pokemap.match_pokemon(role)
            if match is not None:
                user = ctx.message.author
                role_obj = discord.utils.get(user.server.roles, name=match.lower())
                await client.remove_roles(user, role_obj)
            else:
                bad += ' ' + role
    if bad == '':
        await client.add_reaction(ctx.message, '👍')
    else:
        await client.say('Not all requests matched known pokemon. Unable to match:' + bad)


@client.command(pass_context=True)
@pass_errors
async def listwants(ctx):
    """List all pokemon sighting roles a user has."""
    roles = ctx.message.author.roles
    pokemon = []
    embed_str = []
    str_num = 0
    embed_str.append('')

    with open('pokemon.txt') as file:
        line = file.readline()
        while line:
            for role in roles:
                if role.name.title() in line:
                    pokemon.append(role.name.title())
            line = file.readline()
    if pokemon == []:
        await client.say('No want roles found.')
    else:
        for mon in pokemon:
            to_add = mon + '\n'
            if (len(embed_str[str_num]) + len(to_add) > 1000):
                str_num += 1
                embed_str.append('')
            embed_str[str_num] += to_add
        for i in range(len(embed_str)):
            msg = discord.Embed(colour=discord.Colour(0x186a0))
            msg.add_field(name='You are looking for:', value=embed_str[i], inline=False)
            await client.say(embed=msg)


@client.command(pass_context=True)
@has_permissions(administrator=True)
async def serverid(context):
    """Find the server ID."""
    await client.say(context.message.server.id)


@client.event
async def on_message(message):
    """Respond to messages.

    Contains the help commands, and the bots ability to parse language.

    """
    message.content = message.content.replace(u"\u201C", '"')   # Fixes errors with iOS quotes
    message.content = message.content.replace(u"\u201D", '"')
    for role in message.role_mentions:
        role_str = '<@&' + str(role.id) + '>'
        message.content = message.content.replace(role_str, role.name)
    if message.server is not None:
        taskmap = maps[message.server.id]
    if message.author == client.user:
        return
    elif message.content.startswith(bot_prefix):
        if message.server is not None:
            prev_message_was_stop[message.server.id] = False
        msg = message.content.strip("".join(list(bot_prefix)))
        if msg.startswith('help'):
            if 'addstop' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'addstop'
                command_help = """This command is used to add a new stop to the map, and can be used in two different ways.\n
                The first is to specify the longitude and latitude like so '""" + bot_prefix[0] + """addstop test 42.46 -76.51'
                The second is to give an ingress intel url like so '""" + bot_prefix[0] + """addstop test https://intel.ingress.com/intel?ll=42.447358,-76.48151&z=18&pll=42.46,-76.51'

                A site like [this](geojson.io) can be used to find the latitude and longitude manually
                While the [Ingress Intel Map](https://intel.ingress.com/intel) can be used to generate the url by clicking on a portal then clicking the Link button at the top right of the page."""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await bot_embed_respond(message, msg)
            elif 'addtask' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'addtask'
                command_help = """This command lets you add a new task to the tasklist after research changes. If you do so please notify """ + maintainer_handle + """ so they can make sure new tasks show up correctly on the map.

                The correct syntax for the command is """ + bot_prefix[0] + """addtask reward quest shiny*
                Values should be put in quotations if they are more than single words (shiny is optional).
                shiny should be either 'True' or 'False'
                """
                msg.add_field(name=command_name, value=command_help, inline=False)
                await bot_embed_respond(message.channel, msg)
            elif 'listtasks' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'listtasks'
                command_help = 'This command instructs the bot to list all the tasks it currently knows.'
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'resetstop' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'resetstop'
                command_help = """This command removes any tasks associated with a stop. Use if a stop was misreported

                The correct syntax for the command is """ + bot_prefix[0] + """resetstop stop_name"""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'settask' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'settask'
                command_help = """This command assigns a task to a stop.

                The correct syntax for the command is """ + bot_prefix[0] + """settask reward stop_name
                If the reward is more than 1 word it should be enclosed with quotations marks

                Tasks can also be assigned by saying the name of a stop then the name of a task (in different messages). If this is successful the bot should give a thumbs up to both messages."""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'advanced' in message.content.lower():
                commands = {}
                commands[bot_prefix[0] + 'deletetask'] = 'Remove a task from the list.'
                commands[bot_prefix[0] + 'deletestop'] = 'Remove a stop from the local map.'
                commands[bot_prefix[0] + 'resettasklist'] = 'Completely clear the tasklist. Use only if the tasklist has become corrupted,' +\
                    ' otherwise use the deletetask command to remove unwanted tasks one by one.'
                commands[bot_prefix[0] + 'resetall'] = 'Reset all the stops in the map. Use when an event causes research changes (Requires admin).'
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                for command, description in commands.items():
                    msg.add_field(name=command, value=description, inline=False)
                await bot_embed_respond(message, msg)
            elif 'setup' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'Initial Setup Commands'
                command_help = '- First setup the location of your map by using "' + bot_prefix[0] + 'setlocation lat long", with lat and long being the latitude and longitude near the center of your map area.\n'
                command_help += '- Then define the bounds of your map using "' + bot_prefix[0] + 'setbounds lat1 long1 lat2 long2" where the latitudes and longitudes are from opposite corners of your map boundary (SW and NE recommended). '
                command_help += 'The extent of your boundary should be less than one degree of latitude and longitude.\n'
                command_help += '- Lastly set the timezone your map is in (so it resets at midnight correctly) using "' + bot_prefix[0] + 'settimezone timezone_str" where timezone_str is from the list https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones.'
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'research' in message.content.lower():
                commands = {}
                commands[bot_prefix[0] + 'addstop'] = 'Add a new stop to the map.'
                commands[bot_prefix[0] + 'addtask'] = 'Define a new task and reward set.'
                commands[bot_prefix[0] + 'listtasks'] = 'Lists all tasks the bot currently knows along with their rewards.'
                commands[bot_prefix[0] + 'resetstop'] = 'Removes any task associated with a given stop. Use if a stop was misreported'
                commands[bot_prefix[0] + 'settask'] = 'Assign a task to a stop.'

                msg = discord.Embed(colour=discord.Colour(0x186a0))
                for command, description in commands.items():
                    msg.add_field(name=command, value=description, inline=False)
                msg.add_field(name='For more info', value='Use "' + bot_prefix[0] + 'help command" for more info on a command, or use "' + bot_prefix[0] + 'help advanced" to get information on commands for advanced users', inline=False)
                msg.add_field(name='To view the current map', value='Click [here](' + map_url + '/?map=' + str(message.server.id) + ')', inline=False)
                await bot_embed_respond(message, msg)
            elif 'trade' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                intro_text = """This bot allows you to create trade offers.\n
- You can offer pokemon A,B,C.. for pokemon X,Y,Z... (no limits!)\n
- You can have multiple offers (for shinies, regionals, pvp wishlists, unowns, etc)\n
- You can search and view other people offers!\n
- You will receive notifications when you and another person match!"""
                instruction_text = """All messages must be sent in the form of a (?) command. To begin, add your pogo-username using:\n
?setname <pogo_name>\n
 - Replace <pogo_name> with your in-game username\n
\n
Now you can create trade offers using:\n
?addoffer <offer_name>\n
- Replace <offer_name> with any word. This will be the title of your trade offer.\n
\n
Add pokemon to your offer using:\n
?addwant <offer_name> <pokemon>\n
?addhave <offer_name> <pokemon>\n
- Replace <offer_name> with the offer you want to edit\n
- Replace <pokemon> with the pokemon you want/have\n
- Both commands can take multiple pokemon seperated by spaces\n
\n
- Modifiers can be added to the pokemon names if needed\n
    - Shiny can be added before the pokemon name (ex. Shiny Pikachu)\n
    - Forms can be added before the pokemon name (ex. Altered Giratina or Shedinja Costume Bulbasaur)\n
    - Unown letters and Spinda numbers can be added after the pokemon name (ex. Unown A or Spinda 1)\n
.\n"""
                instruction_text2 = """Remove pokemon from your offer using:\n
?deletewant <offer_name> <pokemon>\n
?deletehave <offer_name> <pokemon>\n
- Delete all pokemon by not listing any after the offer name\n
\n
To add or remove multiple shinies at once use:\n
?addshinywant, ?addshinyhave, ?deleteshinywant or ?deleteshinyhave
- These are the same as the normal commands will assume all pokemon listed are shiny\n
\n
Remove an offer completely using:\n
?deleteoffer <offer_name>\n
\n
To view a list of all your offers, use:\n
?listoffers\n
\n
To view the contents of one of your offers use:\n
?viewoffer <offer_name>\n
\n
To search everyone else's offers for a specific pokemon use:\n
?searchwant <pokemon>\n
?searchhave <pokemon>\n
- These will return a list of each person that has the pokemon and the name of their offer\n
\n
To view someone else's offer(s) use:\n
?listoffers <pogo_name>\n
?viewoffer <pogo_name> <offer_name>\n
\n
When you and someone else match you will be notified automatically. You can view all your matches using ?check"""
                msg.add_field(name='Introduction', value=intro_text, inline=False)
                msg.add_field(name='Instructions', value=instruction_text, inline=False)
                msg.add_field(name='Instructions', value=instruction_text2, inline=False)
                await bot_embed_respond(message, msg)
            else:
                await bot_respond(message, 'Use either "help trade" or "help research" to specify topic.')
        elif msg.startswith('setup'):
            msg = discord.Embed(colour=discord.Colour(0x186a0))
            command_name = 'Initial Setup Commands'
            command_help = '- First setup the location of your map by using "' + bot_prefix[0] + 'setlocation lat long", with lat and long being the latitude and longitude near the center of your map area.\n'
            command_help += '- Then define the bounds of your map using "' + bot_prefix[0] + 'setbounds lat1 long1 lat2 long2" where the latitudes and longitudes are from opposite corners of your map boundary (SW and NE recommended). '
            command_help += 'The extent of your boundary should be less than one degree of latitude and longitude.\n'
            command_help += '- Lastly set the timezone your map is in (so it resets at midnight correctly) using "' + bot_prefix[0] + 'settimezone timezone_str" where timezone_str is from the list https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones.'
            msg.add_field(name=command_name, value=command_help, inline=False)
            await client.send_message(message.channel, embed=msg)
        else:
            await client.process_commands(message)
    elif prev_message_was_stop[message.server.id] and prev_message[message.server.id].author == message.author:
        prev_message_was_stop[message.server.id] = False
        if 'shadow' in message.content.lower():
            pokemon = message.content.split()[-1]
            try:
                if 'shadow' not in pokemon.lower():
                    if 'gone' in message.content.lower():
                        prev_message_stop[message.server.id].reset_shadow()
                    else:
                        prev_message_stop[message.server.id].set_shadow(pokemon)
                else:
                    prev_message_stop[message.server.id].set_shadow()
                taskmap.save()
                await client.add_reaction(prev_message[message.server.id], '👍')
                await client.add_reaction(message, '👍')
            except pokemap.PokemapException as e:
                await client.send_message(message.channel, e.message)
        else:
            try:
                task_name = message.content
                task = tasklist.find_task(task_name)
                prev_message_stop[message.server.id].set_task(task)
                if task_name.title() in task.rewards:
                    prev_message_stop[message.server.id].properties['Icon'] = task_name.title()
                taskmap.save()
                await client.add_reaction(prev_message[message.server.id], '👍')
                await client.add_reaction(message, '👍')
            except pokemap.TaskAlreadyAssigned:
                if prev_message_stop[message.server.id].properties['Reward'] == task.reward:
                    await client.add_reaction(prev_message[message.server.id], '👍')
                    await client.add_reaction(message, '👍')
            except pokemap.PokemapException as e:
                await client.send_message(message.channel, e.message)
    else:
        try:
            stop_name = message.content
            prev_message_stop[message.server.id] = taskmap.find_stop(stop_name)
            prev_message_was_stop[message.server.id] = True
            prev_message[message.server.id] = message
        except pokemap.StopNotFound:
            prev_message_was_stop[message.server.id] = False
            if '\n' in message.content:
                try:
                    args = message.content.split('\n', 1)
                    stop_name = args[0]
                    task_name = args[1]
                    stop = taskmap.find_stop(stop_name)
                    if 'shadow' in task_name.lower():
                        pokemon = task_name.split()[-1]
                        if 'shadow' not in pokemon:
                            if 'gone' in message.content.lower():
                                stop.reset_shadow()
                            else:
                                stop.set_shadow(pokemon)
                        else:
                            stop.set_shadow()
                    else:
                        task = tasklist.find_task(task_name)
                        stop.set_task(task)
                        if task_name.title() in task.rewards:
                            stop.properties['Icon'] = task_name.title()
                    taskmap.save()
                    await client.add_reaction(message, '👍')
                except pokemap.TaskAlreadyAssigned:
                    if stop.properties['Reward'] == task.reward:
                        await client.add_reaction(message, '👍')
                    else:
                        pass
                except pokemap.PokemapException:
                    pass


async def list_servers():
    """List all servers that the bot is in."""
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(1800)


async def check_maps():
    """Map checks every few minutes."""
    await client.wait_until_ready()
    while not client.is_closed:
        print('Checking maps at: ' + datetime.now().strftime("%Y.%m.%d.%H%M%S"))
        for key in maps:
            taskmap = maps[key]
            reset_bool = taskmap.reset_old()
            if reset_bool:
                taskmap.save()
                print('Reset map at: ' + datetime.now().strftime("%Y.%m.%d.%H%M%S"))
        now = datetime.strftime(datetime.now(), '%M')
        diff = (datetime.strptime('01', '%M') - datetime.strptime(now, '%M')).total_seconds() % 300  # want to reset every 5 min
        if diff < 60:
            diff += 300
        await asyncio.sleep(diff)

client.loop.create_task(list_servers())
client.loop.create_task(check_maps())
client.run(discord_token)
