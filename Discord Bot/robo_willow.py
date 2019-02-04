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

# Setup Variables
bot_prefix = ("?")   # Tells bot which prefix(or prefixes) to look for. Multiple prefixes can be specified in a tuple, however all help messages will use the first item for examples
map_dir = '/var/www/html/maps/'  # Path the saved map, in geojson format. http://geojson.io/ can be used to create basic maps, or the bot can do it interactively
task_path = 'tasklist.pkl'   # Location to save the tasklist to and load it from if the bot is restarted
map_URL = 'http://robowillow.ddns.net'
bot_game = "with maps at robowillow.net"
maintainer_handle = '@mathmauney'
maintainer_id = 200038656021364736


# Load In Saved Data
# Initialize Map Object
maps = {}
prev_message_was_stop = {}
prev_message_stop = {}
prev_message = {}
# Import the tasklist object or create new one
try:
    with open(task_path, 'rb') as input:
        tasklist = pickle.load(input)
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
    """Take actions on server join"""
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
        await client.send_message(message.channel, response)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")


async def bot_embed_respond(message, msg):
    """Send an embed as a response.

    Command for the bot to send an embed response, checking to see if the channel has the correct permissions.
    If the bot can't say what it wants it sends the user a PM indicating that they tried to use a command in the wrong channel.
    """
    try:
        await client.send_message(message.channel, embed=msg)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")


def pass_errors(func):
    """Decorator to pass library errors into a discord message"""
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


@client.command(pass_context=True)
async def addstop(ctx, *args):
    """Add a stop to the map, contains multiple ways of doing so.

    Expects either:
    !addstop stop name lat long             Stop name can be multiple words or symbols, but doesn't parse " marks correctly
    !addstop stop name ingress_url          ingress_url can be found from the ingress intel map, details in the help description
    """
    taskmap = maps[ctx.message.server.id]
    n_args = len(args)
    if n_args >= 2:  # Checks to see if enough arguements have been given
        if args[-1].startswith('https:'):  # Checks if the lat/long has been given as an ingress intel URL
            name_args = args[0:n_args-1]
            ingress_url = args[-1]
            pll_location = ingress_url.find('pll')  # Finds the part of the url that describes the portal location
            if pll_location != -1:
                comma_location = ingress_url.find(',', pll_location)  # Finds the comma in the portal location and then splits into lat and long
                lat = float(ingress_url[pll_location+4:comma_location])
                long = float(ingress_url[comma_location+1:])
            else:  # If no portal location data was found in the URL
                await client.say('')
                return
        elif n_args > 2:
            lat = float(args[n_args-2])
            long = float(args[n_args-1])
        name = ' '.join(name_args)
        try:
            taskmap.new_stop([long, lat], name)
            taskmap.save()
            await client.say('Creating stop named: ' + name + ' at [' + str(lat) + ', ' + str(long) + '].')
        except pokemap.PokemapException as e:
            await client.say(e.message)
    else:
        await client.say('Not enough arguments. Please give the stop a name and the latitude and longitude. Use the "'+bot_prefix[0]+'help addstop" command for detailed instructions')


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
            await client.say('Task set.')
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
    client.say('Removed tasks from stop.')


@client.command()
@pass_errors
async def addtask(reward, quest, shiny=False):
    """Add a task to a stop."""
    tasklist.add_task(pokemap.Task(reward, quest, shiny))
    tasklist.save(task_path)
    client.say('Task Added')


@client.command()
@pass_errors
async def resettasklist():
    """Backup and reset the tasklist."""
    backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
    tasklist.save(backup_name)
    tasklist.clear()


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
            if (len(value_str[str_num])+len(to_add) > 1000):
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


@client.command()
@pass_errors
async def deletetask(task_str):
    """Delete a task."""
    task = tasklist.find_task(task_str)
    tasklist.remove_task(task)
    tasklist.save(task_path)


@client.command(pass_context=True)
@pass_errors
async def nicknamestop(ctx, stop_name, nickname):
    """Add a nickname to a stop."""
    taskmap = maps[ctx.message.server.id]
    stop = taskmap.find_stop(stop_name)
    stop.add_nickname(nickname)
    taskmap.save()


@client.command()
@pass_errors
async def nicknametask(task_name, nickname):
    """Add a nickname to a task."""
    task = tasklist.find_task(task_name)
    task.add_nickname(nickname)
    tasklist.save(task_path)


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def setlocation(ctx, lat, long):
    """Set the location of the map for the web view."""
    taskmap = maps[ctx.message.server.id]
    coordinates = [float(lat), float(long)]
    taskmap.set_location(coordinates)
    taskmap.save()


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def resetall(ctx):
    """Set the location of the map for the web view."""
    taskmap = maps[ctx.message.server.id]
    for stop in taskmap:
        stop._map = taskmap
        stop.reset()
    taskmap.save()


@client.command(pass_context=True)
@pass_errors
async def resetmap(ctx, server_id):
    """Allows bot owner to reset any map remotely"""
    if int(ctx.message.author.id) == int(maintainer_id):
        taskmap = maps[server_id]
        taskmap.reset_all
        taskmap.save()
    else:
        await client.say("Sorry you can't do that" + ctx.message.author.id)


@client.command(pass_context=True)
@pass_errors
async def resetallmaps(ctx):
    """Allows bot owner to reset any map remotely"""
    if int(ctx.message.author.id) == int(maintainer_id):
        for server_id in maps:
            taskmap = maps[server_id]
            taskmap.reset_all
            taskmap.save()
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
    taskmap.save()


@client.command(pass_context=True)
@has_permissions(administrator=True)
@pass_errors
async def settimezone(ctx, tz_str):
    """Set the timezone of the map so it resets itself correctly."""
    taskmap = maps[ctx.message.server.id]
    taskmap.set_time_zone(tz_str)
    taskmap.save()


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
                The first is to specify the longitude and latitude like so '!addstop test 42.46 -76.51'
                The second is to give an ingress intel url like so '!addstop test https://intel.ingress.com/intel?ll=42.447358,-76.48151&z=18&pll=42.46,-76.51'

                A site like [this](geojson.io) can be used to find the latitude and longitude manually
                While the [Ingress Intel Map](https://intel.ingress.com/intel) can be used to generate the url by clicking on a portal then clicking the Link button at the top right of the page."""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await bot_embed_respond(message, msg)
            elif 'addtask' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'addtask'
                command_help = """This command lets you add a new task to the tasklist after research changes. If you do so please notify """ + maintainer_handle + """ so they can make sure new tasks show up correctly on the map.

                The correct syntax for the command is !addtask reward quest shiny*
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

                The correct syntax for the command is !resetstop stop_name"""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'settask' in message.content.lower():
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'settask'
                command_help = """This command assigns a task to a stop.

                The correct syntax for the command is !settask reward stop_name
                If the reward is more than 1 word it should be enclosed with quotations marks

                Tasks can also be assigned by saying the name of a stop then the name of a task (in different messages). If this is successful the bot should give a thumbs up to both messages."""
                msg.add_field(name=command_name, value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'advanced' in message.content.lower():
                commands = {}
                commands[bot_prefix[0]+'deletetask'] = 'Remove a task from the list.'
                commands[bot_prefix[0]+'deletestop'] = 'Remove a stop from the local map.'
                commands[bot_prefix[0]+'resettasklist'] = 'Completely clear the tasklist. Use only if the tasklist has become corrupted,' +\
                    ' otherwise use the deletetask command to remove unwanted tasks one by one.'
                commands[bot_prefix[0]+'resetall'] = 'Reset all the stops in the map. Use when an event causes research changes (Requires admin).'
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                for command, description in commands.items():
                    msg.add_field(name=command, value=description, inline=False)
                await bot_embed_respond(message, msg)
            else:
                commands = {}
                commands[bot_prefix[0]+'addstop'] = 'Add a new stop to the map.'
                commands[bot_prefix[0]+'addtask'] = 'Define a new task and reward set.'
                commands[bot_prefix[0]+'listtasks'] = 'Lists all tasks the bot currently knows along with their rewards.'
                commands[bot_prefix[0]+'resetstop'] = 'Removes any task associated with a given stop. Use if a stop was misreported'
                commands[bot_prefix[0]+'settask'] = 'Assign a task to a stop.'

                msg = discord.Embed(colour=discord.Colour(0x186a0))
                for command, description in commands.items():
                    msg.add_field(name=command, value=description, inline=False)
                msg.add_field(name='For more info', value='Use "' + bot_prefix[0] + 'help command" for more info on a command, or use "' + bot_prefix[0] +
                              'help advanced" to get information on commands for advanced users', inline=False)
                msg.add_field(name='To view the current map', value='Click [here](' + map_URL + '/?map=' + str(message.server.id) + ')', inline=False)
                await bot_embed_respond(message, msg)
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
    elif prev_message_was_stop[message.server.id]:
        prev_message_was_stop[message.server.id] = False
        try:
            task_name = message.content
            task = tasklist.find_task(task_name)
            prev_message_stop[message.server.id].set_task(task)
            if task_name.title() in task.rewards:
                prev_message_stop[message.server.id].properties['Icon'] = task_name.title()
            taskmap.save()
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
        except pokemap.PokemapException:
            prev_message_was_stop[message.server.id] = False
            if '\n' in message.content:
                try:
                    args = message.content.split('\n', 1)
                    stop_name = args[0]
                    task_name = args[1]
                    stop = taskmap.find_stop(stop_name)
                    task = tasklist.find_task(task_name)
                    stop.set_task(task)
                    if task_name.title() in task.rewards:
                        stop.properties['Icon'] = task_name.title()
                    taskmap.save()
                    await client.add_reaction(message, '👍')
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
    """Map resets every hour."""
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
        diff = (datetime.strptime('01', '%M') - datetime.strptime(now, '%M')).total_seconds()
        if diff < 60:
            diff += 3600
        await asyncio.sleep(diff)

client.loop.create_task(list_servers())
client.loop.create_task(check_maps())
client.run(discord_token)
