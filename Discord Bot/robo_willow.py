# Work with Python 3.6
import random
import asyncio
import aiohttp
import json
import pokemap
import pygeoj
import pickle
import discord
from discord import Game
from discord.ext.commands import Bot

#Initialize Map Object
taskmap = pygeoj.load('map.json')
pokemap.reset_old_tasks(taskmap)

#Initialize the tasklist object
try:
    with open('tasklist.pkl', 'rb') as input:
        tasklist = pickle.load(input)
except:
    tasklist = []


BOT_PREFIX = ("?", "!")
TOKEN = 'NTEwNDY5NjI3NDc4ODAyNDM1.DsczsA.lv7-Pkok6Id07DlF2yuzdfohZNQ'

client = Bot(command_prefix=BOT_PREFIX)

@client.event
async def on_ready():
    await client.change_presence(game=Game(name="with humans"))
    print("Logged in as " + client.user.name)

@client.command()
async def addstop(*args):
    n_args = len(args)
    if n_args > 2:
        lat = float(args[n_args-2])
        long = float(args[n_args-1])
        name_args = args[0:n_args-2]
        name = ' '.join(name_args)
        name = name.title()
        try:
            await client.say('Creating stop named: ' + name + ' at [' + str(lat) + ', ' + str(long) + '].')
            pokemap.add_stop(taskmap,[lat, long],name)
            taskmap.save('map.json')
            await client.say('Stop created!')
        except:
            await client.say('Error in stop creation. Double check formating of command.')
        
    else:
        await client.say('Not enough arguments. Please give the stop a name and the latitude and longitude. Use the "'+BOT_PREFIX[0]+'help addstop" command for detailed instructions')

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
            await client.say('Found stop')
            task = pokemap.find_task(tasklist,task_str)
            await client.say('Found task')
            pokemap.set_task(stop,task)
            await client.say('Success!')
            taskmap.save('map.json')
        except:
            await client.say('Error in task assignment. Task was probably not found. Tried to find task: ' + task_str +' for stop: ' + stop_name)
    else:
        await client.say('Not enough arguments.')
        
@client.command()
async def addtask(reward, quest, reward_type, shiny):
    tasklist.append(pokemap.Task(reward, quest, reward_type, shiny))
    pokemap.save_object(tasklist,'tasklist.pkl')
    
@client.command()
async def resettasklist():
    backup_name = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
    save_object(tasklist,backup_name)
    tasklist = []
    
@client.command()
async def listtasks():
    for tasks in tasklist:
        await client.say(tasks.quest + ' for a ' + tasks.reward)
        
        

        
        
@client.event
async def on_message(message):
    
    if message.content.lower().startswith(BOT_PREFIX[0]+'help'):
        if 'addstop' in message.content.lower():
            await client.send_message(message.channel, 'Roger')
        elif 'addtask' in message.content.lower():
            pass
        elif 'addtask' in message.content.lower():
            pass
        elif 'addtask' in message.content.lower():
            pass
        else:
            commands={}
            commands[BOT_PREFIX[0]+'addstop']='Add a new stop to the map.'
            commands[BOT_PREFIX[0]+'addtask']='Define a new task and reward set.'
            commands[BOT_PREFIX[0]+'listtasks']='Lists all tasks the bot currently knows along with their rewards.'
            commands[BOT_PREFIX[0]+'settask']='Assign a task to a stop.'


            msg=discord.Embed(colour=discord.Colour(0x186a0))
            for command,description in commands.items():
                msg.add_field(name=command,value=description, inline=False)
            msg.add_field(name='For more info',value='Use "'+BOT_PREFIX[0]+'help command" for more info on a command.', inline=False)
            msg.add_field(name='To view the current map',value='Click [here](http://geojson.io/#data=data:text/x-url,https%3A%2F%2Fdl.dropboxusercontent.com%2Fs%2Fr19l5yv9b49izkm%2Fmap.json)', inline=False)
            await client.send_message(message.channel, embed=msg)    
    
async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)


client.loop.create_task(list_servers())
client.run(TOKEN)

