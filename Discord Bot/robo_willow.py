# Work with Python 3.6
import sys
import random
import asyncio
import aiohttp
import json
import pokemap
import pygeoj
import pickle
import discord
import datetime
from discord import Game
from discord.ext.commands import Bot

###Setup Variables
bot_prefix = ("?") # Tells bot which prefix(or prefixes) to look for. Multiple prefixes can be specified in a tuple, however all help messages will use the first item for examples
discord_token = 'NTEwNDY5NjI3NDc4ODAyNDM1.DsczsA.lv7-Pkok6Id07DlF2yuzdfohZNQ' # Discord API token from https://discordapp.com/developers/applications
map_path = '/var/www/html/map.json' # Path the saved map, in geojson format. http://geojson.io/ can be used to create basic maps, or the bot can do it interactively
task_path = 'tasklist.pkl' # Location to save the tasklist to and load it from if the bot is restarted
latitude_range = [42, 43] # These ranges will give the use an error if they try to create stops outside of them, and will correct flipped latitude and longitude if the ranges are distinct
longitude_range = [-77, -76]
map_URL = 'https://mathmauney.no-ip.org'
bot_game = "with maps at mathmauney.no-ip.org"
maintainer_handle = '@mathmauney'


###Load In Saved Data
#Initialize Map Object
try:
    taskmap = pygeoj.load(map_path)
    reset_bool = pokemap.reset_old_tasks(taskmap)
    if reset_bool:
        taskmap.save(map_path)
    print('Map successfully loaded')
except FileNotFoundError:
    taskmap = pygeoj.new()
    print('No map found at: ' + map_path +'. Creating new map now')

#Import the tasklist object or create new one 
try:
    with open(task_path, 'rb') as input:
        tasklist = pickle.load(input)
except:
    tasklist = []

###Startup Bot Instance
client = Bot(command_prefix=bot_prefix)
prev_message_was_stop = False # This is used to for passive detection of reports without commands

#Sets the bots playing status
@client.event
async def on_ready():
    """Bot actions on login"""
    await client.change_presence(game=Game(name=bot_game)) #Sets the game presence
    print("Logged in as " + client.user.name) #Logs sucessful login

###Bot Command Definitions
async def bot_respond(message, response):
    """Command for the bot to send a simple response, checking to see if the channel has the correct permissions. If the bot can't say what it wants it sends the user a PM indicating that they tried to use a command in the wrong channel."""
    try:
        await client.send_message(message.channel, response)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")

async def bot_embed_respond(message, msg):
    """Command for the bot to send an embed response, checking to see if the channel has the correct permissions. If the bot can't say what it wants it sends the user a PM indicating that they tried to use a command in the wrong channel."""
    try:
        await client.send_message(message.channel, embed=msg)
    except discord.errors.Forbidden:
        await client.send_message(message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")

@client.command()
async def addstop(*args):
    """Adds a stop to the map, contains multiple ways of doing so. Expects either:
!addstop stop name lat long             Stop name can be multiple words or symbols, but doesn't parse " marks correctly
!addstop stop name ingress_url          ingress_url can be found from the ingress intel map, details in the help description"""
    n_args = len(args)
    if n_args >= 2: # Checks to see if enough arguements have been given
        if args[-1].startswith('https:'): # Checks if the lat/long has been given as an ingress intel URL
            name_args = args[0:n_args-1]
            ingress_url = args[-1]
            pll_location = ingress_url.find('pll') # Finds the part of the url that describes the portal location
            if pll_location != -1: 
                comma_location = ingress_url.find(',',pll_location) # Finds the comma in the portal location and then splits into lat and long
                lat = float(ingress_url[pll_location+4:comma_location])
                long = float(ingress_url[comma_location+1:])
            else: # If no portal location data was found in the URL
                await client.say('')
                return
        elif n_args > 2:
            lat = float(args[n_args-2])
            long = float(args[n_args-1])
            if (long > 0) and (lat < 0):
                temp = lat
                lat = long
                long = temp
            name_args = args[0:n_args-2]
        name = ' '.join(name_args)
        try:
            pokemap.add_stop(taskmap,[long, lat],name)
            taskmap.save(map_path)
            await client.say('Creating stop named: ' + name + ' at [' + str(lat) + ', ' + str(long) + '].')
        except Exception as e:
            print(e)
            await client.say('Error in stop creation. Double check formating of command.')
    else:
        await client.say('Not enough arguments. Please give the stop a name and the latitude and longitude. Use the "'+bot_prefix[0]+'help addstop" command for detailed instructions')

@client.command()
async def settask(*args):
    n_args = len(args)
    if n_args > 1:
        try:
            task_str = args[0]
            stop_args = args[1:]
            stop_name = ' '.join(stop_args)
            stop_name = stop_name.title()
            stop = pokemap.find_stop(taskmap,stop_name)
            task = pokemap.find_task(tasklist,task_str)
            pokemap.set_task(stop,task)
            await client.say('Task set.')
            taskmap.save(map_path)
        except pokemap.PokemapException as e:
            await client.say(e.message)
        except Exception as e:
            await client.say('Error in task assignment. Task was probably not found. Tried to find task: ' + task_str +' for stop: ' + stop_name)
    else:
        await client.say('Not enough arguments.')
		
@client.command()
async def resetstop(*args):
    stop_name = ' '.join(args)
    stop_name = stop_name
    stop = pokemap.find_stop(taskmap,stop_name)
    try:
        pokemap.reset_task(stop)
        taskmap.save(map_path)
        client.say('Removed tasks from stop.')
    except:
        client.say('Unable to remove task from stop. Double check stop name')
        
@client.command()
async def addtask(reward, quest, shiny = 'False', reward_type = 'Encounter'):
    try:
        tasklist.append(pokemap.Task(reward, quest, reward_type, shiny))
        pokemap.save_object(tasklist,task_path)
        client.say('Task Added')
    except:
        client.say('Unable to add task. Double check command syntax')
        
@client.command()
async def resettasklist():
    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
    pokemap.save_object(tasklist,backup_name)
    tasklist.clear()
    
@client.command()
async def listtasks():
    value_str = []
    str_num = 0
    value_str.append('')
    for tasks in tasklist:
        to_add = tasks.quest + ' for a ' + tasks.reward
        if tasks.shiny == 'True':
            to_add += ' ✨'
        if tasks.reward_type == 'Rare Candy':
            to_add += ' 🍬'
        to_add += '\n'
        if (len(value_str[str_num])+len(to_add) > 1000):
            str_num += 1
            value_str.append('')
        value_str[str_num] += to_add
    for i in range(len(value_str)):
        msg=discord.Embed(colour=discord.Colour(0x186a0))
        msg.add_field(name='Currently Known Tasks',value=value_str[i], inline=False)
        await client.say(embed=msg)
        
@client.command()
async def deletestop(*args):
    stop_name = ' '.join(args)
    stop_name = stop_name
    for i in range(len(taskmap)):
        if taskmap[i].properties['Stop Name'].title() == stop_name.title():
            del taskmap[i]
            await client.say('Deleted Stop')
    taskmap.save(map_path)        
        
@client.command()
async def deletetask(task_str):
    for i in range(len(tasklist)):
        if tasklist[i].reward == task_str:
            del tasklist[i]
            await client.say('Deleted Task')

@client.command()
async def nicknamestop(stop_name,nickname):
    stop_name = stop_name
    stop = pokemap.find_stop(taskmap,stop_name)
    pokemap.add_stop_nickname(stop,nickname)
    taskmap.save(map_path)
            
@client.command()
async def nicknametask(task_name,nickname):
    task_name = task_name
    stop = pokemap.find_task(tasklist,task_name)
    pokemap.add_task_nickname(task,nickname)  
    pokemap.save_object(tasklist,task_path)    
    
@client.event
async def on_message(message):
    global prev_message_was_stop
    global prev_message_stop
    global prev_message
    if message.author == client.user:
        return
    elif message.content.startswith(bot_prefix):
        prev_message_was_stop = False
        msg = message.content.strip("".join(list(bot_prefix)))
        if msg.startswith('help'):
            if 'addstop' in message.content.lower():
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'addstop'
                command_help = """This command is used to add a new stop to the map, and can be used in two different ways.\n
                The first is to specify the longitude and latitude like so '!addstop test 42.46 -76.51'
                The second is to give an ingress intel url like so '!addstop test https://intel.ingress.com/intel?ll=42.447358,-76.48151&z=18&pll=42.46,-76.51'
                
                A site like [this](geojson.io) can be used to find the latitude and longitude manually
                While the [Ingress Intel Map](https://intel.ingress.com/intel) can be used to generate the url by clicking on a portal then clicking the Link button at the top right of the page."""
                msg.add_field(name=command_name,value=command_help, inline=False)
                await bot_embed_respond(message, msg)
            elif 'addtask' in message.content.lower():
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'addtask'
                command_help = """This command lets you add a new task to the tasklist after research changes. If you do so please notify """ + maintainer_handle + """ so they can make sure new tasks show up correctly on the map.
                
                The correct syntax for the command is !addtask reward quest shiny* reward_type*
                Values should be put in quotations if they are more than single words (shiny and reward_type are optional).
                shiny should be either 'True' or 'False'
                reward_type should be either 'Encounter', 'Stardust', 'Item', or 'Rare Candy'"""
                msg.add_field(name=command_name,value=command_help, inline=False)
                await bot_embed_respond(message.channel, msg)
            elif 'listtasks' in message.content.lower():
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'listtasks'
                command_help = 'This command instructs the bot to list all the tasks it currently knows.'
                msg.add_field(name=command_name,value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)
            elif 'resetstop' in message.content.lower():
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'resetstop'
                command_help = """This command removes any tasks associated with a stop. Use if a stop was misreported
                
                The correct syntax for the command is !resetstop stop_name"""
                msg.add_field(name=command_name,value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)  
            elif 'settask' in message.content.lower():
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                command_name = 'settask'
                command_help = """This command assigns a task to a stop.
                
                The correct syntax for the command is !settask reward stop_name
                If the reward is more than 1 word it should be enclosed with quotations marks
                
                Tasks can also be assigned by saying the name of a stop then the name of a task (in different messages). If this is successful the bot should give a thumbs up to both messages."""
                msg.add_field(name=command_name,value=command_help, inline=False)
                await client.send_message(message.channel, embed=msg)  
            elif 'advanced' in message.content.lower():
                commands={}
                commands[bot_prefix[0]+'deletetask']='Remove a task from the list.'
                commands[bot_prefix[0]+'deletestop']='Remove a stop from the local map.'
                commands[bot_prefix[0]+'resettasklist']='Completely clear the tasklist. Use only if the tasklist has become corrupted, otherwise use the deletetask command to remove unwanted tasks one by one.'
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                for command,description in commands.items():
                    msg.add_field(name=command,value=description, inline=False)
                await bot_embed_respond(message, msg)
            else:
                commands={}
                commands[bot_prefix[0]+'addstop']='Add a new stop to the map.'
                commands[bot_prefix[0]+'addtask']='Define a new task and reward set.'
                commands[bot_prefix[0]+'listtasks']='Lists all tasks the bot currently knows along with their rewards.'
                commands[bot_prefix[0]+'resetstop']='Removes any task associated with a given stop. Use if a stop was misreported'
                commands[bot_prefix[0]+'settask']='Assign a task to a stop.'
                
                msg=discord.Embed(colour=discord.Colour(0x186a0))
                for command,description in commands.items():
                    msg.add_field(name=command,value=description, inline=False)
                msg.add_field(name='For more info',value='Use "'+bot_prefix[0]+'help command" for more info on a command, or use "'+bot_prefix[0]+'help advanced" to get information on commands for advanced users', inline=False)
                msg.add_field(name='To view the current map',value='Click [here](' + map_URL + ')', inline=False)
                await bot_embed_respond(message, msg)    
        else:
            await client.process_commands(message)
    elif prev_message_was_stop:
        prev_message_was_stop = False
        try:
            task_name = message.content
            task = pokemap.find_task(tasklist,task_name)
            pokemap.set_task(prev_message_stop,task)
            taskmap.save(map_path)
            await client.add_reaction(prev_message, '👍')
            await client.add_reaction(message, '👍')
        except:
            await client.send_message(message.channel, sys.exc_info()[0]) 
    else:
        try:
            stop_name = message.content
            prev_message_stop = pokemap.find_stop(taskmap,stop_name)
            prev_message_was_stop = True
            prev_message = message
        except:
            prev_message_was_stop = False
            
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        reset_bool = pokemap.reset_old_tasks(taskmap)
        if reset_bool:
            taskmap.save(map_path)
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        print(datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S"))
        await asyncio.sleep(1800)


client.loop.create_task(list_servers())
client.run(discord_token)