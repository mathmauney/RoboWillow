"""Discord bot for mapping out pokemon go research and other misc functions."""

import asyncio
import pokemap
import pickle
import discord
import inspect
from datetime import datetime
from discord import Game
from discord.ext.commands import Bot, has_permissions
import urllib.parse as urlparse
import trade_functions as tf
from test_config import discord_token

bot_prefix = ("!")   # Tells bot which prefix(or prefixes) to look for. Multiple prefixes can be specified in a tuple, however all help messages will use the first item for examples
map_dir = '/var/www/html/maps/'  # Path the saved map, in geojson format. http://geojson.io/ can be used to create basic maps, or the bot can do it interactively
task_path = 'tasklist.pkl'   # Location to save the tasklist to and load it from if the bot is restarted
map_url = 'http://robowillow.ddns.net'
bot_game = "with maps at robowillow.net"
maintainer_handle = 'mathmauney#2643'
maintainer_id = 200038656021364736

client = Bot(command_prefix=bot_prefix)

prev_matches = {}
prev_views = {}
prev_search = {}
# ------------------------------------------------------------------------------------------------------------------------------- #


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
async def view(ctx, offer_name):
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
async def listoffers(ctx):
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


@client.command(pass_context=True)
async def setname(ctx, pogo_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
    try:
        tf.set_name(user, pogo_name)
        await bot_thumbsup(ctx.message)
    except ValueError:
        await bot_respond(ctx.message, 'Name already in use, please contact <@%s> if you think this is in error.' % maintainer_id)


@client.command(pass_context=True)
async def viewuseroffers(ctx, pogo_name, *search_terms):
    user = tf.find_user(pogo_name)
    if user is None:
        await bot_respond(ctx.message, 'User not found')
    else:
        if len(search_terms) == 0:
            offer_names = tf.find_offers(user)
            if offer_names == []:
                await bot_respond(ctx.message, 'No offers found')
            else:
                offer_str = '\n'.join(offer_names)
                embed = discord.Embed(colour=discord.Colour(0x186a0))
                embed.add_field(name='Offer Names', value=offer_str, inline=False)
                await bot_embed_respond(ctx.message, embed)
        elif len(search_terms) == 1:
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
async def viewhave(ctx, *search_terms):
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
    embed_strs = ['']
    embed_num = 0
    for result in results:
        to_add = "%s (<@%s>)'s offer: %s.\n" % (result[1], str(result[0]), result[2])
        if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
            embed_num += 1
            embed_strs.append('')
        embed_strs[embed_num] += to_add
    prev_matches[message.author.id] = embed_strs
    embed = discord.Embed(colour=discord.Colour(0x186a0))
    embed.add_field(name='Search Results', value=embed_strs[0], inline=False)
    embed.set_footer(text='Page 1 of %s. Use %smoreresults n to see page n.' % (len(embed_strs), bot_prefix[0]))
    await bot_embed_respond(ctx.message, embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(bot_prefix):
        await client.process_commands(message)


# ------------------------------------------------------------------------------------------------------------------------------- #
client.run(discord_token)
