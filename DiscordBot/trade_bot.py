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
maintainer_handle = '@mathmauney'
maintainer_id = 200038656021364736

client = Bot(command_prefix=bot_prefix)

prev_matches = {}
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


async def process_matches(message, offer):
    """Check for matches on an offer and notify both parties if there are matches."""
    matches = tf.parse_matches(offer)
    sender = message.author
    matches = [(['Squirtle', 'Charmander'], ['Bulbasaur', 'Pikachu', 'Raichu'], 200038656021364736)]
    embed_componenets = []
    for match in matches:
        if len(match[0]) == 1:
            want_str = match[0]
        elif len(match[0]) == 2:
            want_str = ' or '.join(match[0])
        else:
            want_str = ', '.join(match[0][:-1]) + ', or ' + match[0][-1]
        if len(match[1]) == 1:
            have_str = match[0]
        elif len(match[1]) == 2:
            have_str = ' or '.join(match[1])
        else:
            have_str = ', '.join(match[1][:-1]) + ', or ' + match[1][-1]
        notification = "Trade matched! Your %s for <@%s>'s %s" % (want_str, str(sender.id), have_str)
        match_user = await client.get_user_info(match[2])
        await client.send_message(match_user, notification)
        embed_componenets.append((want_str, have_str, match_user.id))
    if embed_componenets != []:
        embed_strs = ['']
        embed_num = 0
        for component in embed_componenets:
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
        user = tf.add_new_user(ctx.message.author.id)
    if ctx.message.server is not None:
        tf.add_community(user, ctx.message.server.id)
        await client.send_message(ctx.message.author, "Adding you to community: " + str(ctx.message.server.id))


@client.command(pass_context=True)
async def addoffer(ctx, offer_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    if tf.find_offer(user, offer_name) is None:
        tf.add_offer(user, offer_name)
        await client.add_reaction(ctx.message, '👍')
    else:
        await bot_respond(ctx.message, "Offer group already exists.")


@client.command(pass_context=True, aliases=['deletewants'])
async def deletewant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_delete = []
    costume = None
    shiny = False
    for (i, poke) in enumerate(pokemon):
        poke = poke.strip(',')
        if poke.title() == 'Shiny':
            shiny = True
        else:
            matched_poke = pokemap.match_pokemon(poke)
            if costume is not None and matched_poke is not None:
                matched_costume = pokemap.match_costume(matched_poke, costume)
                if matched_costume is not None:
                    matched_poke = matched_costume
            if matched_poke is not None:
                if shiny is True:
                    cleaned_delete.append('Shiny ' + matched_poke)
                    shiny = False
                else:
                    cleaned_delete.append(matched_poke)
            else:
                if costume is None:
                    costume = poke
                else:
                    costume = costume + ' ' + poke
    tf.remove_wants(offer, cleaned_delete)
    await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_delete))


@client.command(pass_context=True, aliases=['deletehaves'])
async def deletehave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_delete = []
    costume = None
    shiny = False
    for (i, poke) in enumerate(pokemon):
        poke = poke.strip(',')
        if poke.title() == 'Shiny':
            shiny = True
        else:
            matched_poke = pokemap.match_pokemon(poke)
            if costume is not None and matched_poke is not None:
                matched_costume = pokemap.match_costume(matched_poke, costume)
                if matched_costume is not None:
                    matched_poke = matched_costume
            if matched_poke is not None:
                if shiny is True:
                    cleaned_delete.append('Shiny ' + matched_poke)
                    shiny = False
                else:
                    cleaned_delete.append(matched_poke)
            else:
                if costume is None:
                    costume = poke
                else:
                    costume = costume + ' ' + poke
    tf.remove_haves(offer, cleaned_delete)
    await bot_respond(ctx.message, 'Removed: ' + ', '.join(cleaned_delete))


@client.command(pass_context=True, aliases=['addwants'])
async def addwant(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_wants = []
    costume = None
    shiny = False
    for (i, poke) in enumerate(pokemon):
        poke = poke.strip(',')
        if poke.title() == 'Shiny':
            shiny = True
        else:
            matched_poke = pokemap.match_pokemon(poke)
            if costume is not None and matched_poke is not None:
                matched_costume = pokemap.match_costume(matched_poke, costume)
                if matched_costume is not None:
                    matched_poke = matched_costume
            if matched_poke is not None:
                if shiny is True:
                    cleaned_wants.append('Shiny ' + matched_poke)
                    shiny = False
                else:
                    cleaned_wants.append(matched_poke)
            else:
                if costume is None:
                    costume = poke
                else:
                    costume = costume + ' ' + poke
    tf.add_wants(offer, cleaned_wants)
    await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_wants))
    await process_matches(offer)


@client.command(pass_context=True, aliases=['addhaves'])
async def addhave(ctx, offer_name, *pokemon):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    if offer is None:
        await bot_respond(ctx.message, "Offer group not found.")
        return
    cleaned_haves = []
    costume = None
    shiny = False
    for (i, poke) in enumerate(pokemon):
        poke = poke.strip(',')
        if poke.title() == 'Shiny':
            shiny = True
        else:
            matched_poke = pokemap.match_pokemon(poke)
            if costume is not None and matched_poke is not None:
                matched_costume = pokemap.match_costume(matched_poke, costume)
                if matched_costume is not None:
                    matched_poke = matched_costume
            if matched_poke is not None:
                if shiny is True:
                    cleaned_haves.append('Shiny ' + matched_poke)
                    shiny = False
                else:
                    cleaned_haves.append(matched_poke)
            else:
                if costume is None:
                    costume = poke
                else:
                    costume = costume + ' ' + poke
    tf.add_wants(offer, cleaned_haves)
    await bot_respond(ctx.message, 'Added: ' + ', '.join(cleaned_haves))
    await process_matches(offer)


@client.command(pass_context=True)
async def view(ctx, offer_name):
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    (wants, haves) = tf.get_offer_contents(tf.find_offer(user, offer_name))
    have_str = ', '.join(haves)
    want_str = ', '.join(wants)
    embed = discord.Embed(colour=discord.Colour(0x186a0))
    embed.add_field(name='You Have', value=have_str, inline=False)
    print(have_str)
    embed.add_field(name='You Want', value=want_str, inline=False)
    print(want_str)
    await bot_embed_respond(ctx.message, embed)


@client.command(pass_context=True)
async def test(ctx):
    offer_name = '  test2'
    user = tf.get_user(ctx.message.author.id)
    if user is None:
        user = tf.add_new_user(ctx.message.author.id)
    offer = tf.find_offer(user, offer_name)
    await process_matches(ctx.message, offer)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith(bot_prefix):
        await client.process_commands(message)


# ------------------------------------------------------------------------------------------------------------------------------- #
client.run(discord_token)
