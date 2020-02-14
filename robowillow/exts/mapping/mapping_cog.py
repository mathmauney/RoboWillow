"""Commands to deal with the mapping of research tasks."""
from discord.ext.commands import Cog, command, has_permissions
import urllib.parse as urlparse
from robowillow.utils import pokemap
from robowillow.utils import database as db
from robowillow.core.checks import check_is_owner
from . import map_checks
from datetime import datetime
import discord
import requests
import json


class Mapper(Cog):
    """Commands to deal with the mapping of research tasks."""

    def __init__(self, bot):
        """Initialize Cog variables from bot."""
        self.bot = bot
        self.maps = bot.maps
        self.map_url = bot.config.map_url
        self.maintainer_id = bot.config.bot_owner
        self.tasklist = bot.tasklist
        self.task_path = bot.config.file_paths['tasklist']
        self.prev_message_was_stop = {}
        self.prev_message_stop = {}
        self.prev_message = {}
        print("Mapper loaded")
        for guild in self.bot.guilds:
            print(f"Mapper init: {str(guild.id)}")
            self.prev_message_was_stop[guild.id] = False
            self.prev_message[guild.id] = None
            self.prev_message_stop[guild.id] = None

    @command()
    @map_checks.map_ready()
    async def map(self, ctx):
        """View the map url for this server."""
        msg = discord.Embed(colour=discord.Colour(0x186a0))
        msg.add_field(name='To view the current map', value='Click [here](' + self.map_url + '/?map=' + str(ctx.message.guild.id) + ')', inline=False)
        await ctx.send(embed=msg)

    @command()
    @map_checks.map_ready()
    async def addstop(self, ctx, *args):
        """Add a stop to the map, contains multiple ways of doing so.

        Expects either:
        !addstop stop name lat long             Stop name can be multiple words or symbols, but doesn't parse " marks correctly
        !addstop stop name ingress_url          ingress_url can be found from the ingress intel map, details in the help description
        """
        taskmap = self.maps[ctx.message.guild.id]
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
                    await ctx.send('No portal location data in URL.')
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
            await ctx.send('Not enough arguments. Please give the stop a name and the latitude and longitude. Use the "' + self.bot.default_prefix + 'help addstop" command for detailed instructions')
        try:
            taskmap.new_stop([long, lat], name)
            taskmap.save()
            await ctx.send('Creating stop named: ' + name + ' at [' + str(lat) + ', ' + str(long) + '].')
        except pokemap.PokemapException as e:
            await ctx.send(e.message)

    @command()
    @map_checks.map_ready()
    async def settask(self, ctx, task, *stop):
        """Set a task to a stop.

        Can also be done by simple typing the stop name and task in a message seperated by a return."""
        taskmap = self.maps[ctx.message.guild.id]
        n_args = len(stop)
        if n_args > 0:
            try:
                task_str = task
                stop_args = stop
                stop_name = ' '.join(stop_args)
                stop_name = stop_name.title()
                stop = taskmap.find_stop(stop_name)
                task = self.tasklist.find_task(task_str)
                stop.set_task(task)
                if task_str.title() in task.rewards:
                    stop.properties['Icon'] = task_str.title()
                await ctx.message.add_reaction('👍')
                taskmap.save()
            except pokemap.PokemapException as e:
                await ctx.send(e.message)
        else:
            await ctx.send('Not enough arguments.')

    @command()
    @map_checks.map_ready()
    async def resetstop(self, ctx, *args):
        """Reset the task associated with a stop."""
        taskmap = self.maps[ctx.message.guild.id]
        stop_name = ' '.join(args)
        stop_name = stop_name
        stop = taskmap.find_stop(stop_name)
        stop.reset()
        taskmap.save()
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def addtask(self, ctx, reward, quest, shiny=False):
        """Add a new task to the tasklist."""
        self.tasklist.add_task(pokemap.Task(reward, quest, shiny))
        self.tasklist.save(self.bot.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def resettasklist(self, ctx):
        """Backup and reset the tasklist."""
        backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
        self.tasklist.save(backup_name)
        self.tasklist.clear()
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    def iitcimport(self, ctx, taskmap, filename):
        """Import an IITC file to get new potential stops and gyms."""
        if '://' in filename:
            file = requests.get(filename)
            json_dict = file.json()
        else:
            with open(filename, 'r') as file:
                json_dict = json.load(file)
        for key in json_dict:
            if 'Ignored' in key.title():
                pass
            else:
                for poi in json_dict[key]:
                    name = json_dict[key][poi]['name']
                    lat = json_dict[key][poi]['lat']
                    long = json_dict[key][poi]['lng']
                    try:
                        stop = taskmap.find_stop(name, [long, lat], acc=95, force=True)
                    except pokemap.StopNotFound:
                        taskmap.new_stop([long, lat], name)
                        stop = taskmap.find_stop(name)
                        if key == 'pokestops':
                            stop.properties['Type'] = 'Stop'
                        else:
                            stop.properties['Type'] = 'POI'
                    except pokemap.MultipleStopsFound:
                        stop = None
                    if key == 'gyms' and stop is not None:
                        stop.properties['Type'] = 'Gym'
        taskmap.save()
        print("Loaded IITC data")
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def pulltasklist(self, ctx):
        """Pull tasks from TheSilphRoad."""
        new_tasklist = pokemap.fetch_tasklist()
        if new_tasklist.tasks == []:
            await ctx.message.add_reaction('❌')
        else:
            backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
            self.tasklist.save(backup_name)
            self.tasklist = new_tasklist
            self.tasklist.save(self.task_path)
            await ctx.message.add_reaction('👍')

    @command(aliases=['tasklist'])
    @map_checks.map_channel()
    async def listtasks(self, ctx):
        """List the known tasks."""
        value_str = []
        str_num = 0
        value_str.append('')
        if self.tasklist.tasks == []:
            await ctx.send("No tasks known")
        else:
            for tasks in self.tasklist.tasks:
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
                await ctx.send(embed=msg)

    @command()
    @map_checks.map_ready()
    async def deletestop(self, ctx, *stop_name):
        """Delete a stop."""
        taskmap = self.maps[ctx.message.guild.id]
        stop_str = ' '.join(stop_name)
        stop = taskmap.find_stop(stop_str)
        taskmap.remove_stop(stop)
        taskmap.save()
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def deletetask(self, ctx, task_name):
        """Delete a task."""
        task = self.tasklist.find_task(task_name)
        self.tasklist.remove_task(task)
        self.tasklist.save(self.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_ready()
    async def nicknamestop(self, ctx, stop_name, nickname):
        """Add a nickname to a stop.

        If the stop or nickname contain spaces they should be wrapped in quotes."""
        taskmap = self.maps[ctx.message.guild.id]
        stop = taskmap.find_stop(stop_name)
        stop.add_nickname(nickname)
        taskmap.save()
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_ready()
    @check_is_owner()
    async def nicknametask(self, ctx, task_name, nickname):
        """Add a nickname to a task.

        If the task or nickname contain spaces they should be wrapped in quotes."""
        task = self.tasklist.find_task(task_name)
        task.add_nickname(nickname)
        self.tasklist.save(self.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def setlocation(self, ctx, lat, long):
        """Set the location of the map for the web view.

        This will set the center of the default map view."""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.set_location(float(lat), float(long))
        try:
            taskmap.save()
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def resetall(self, ctx):
        """Reset all stops on the map."""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.reset_all()
        taskmap.save()

    @command()
    @map_checks.map_channel()
    @check_is_owner()
    async def resetmap(self, ctx, guild_id):
        """Allow bot owner to reset any map remotely."""
        if int(self, ctx.message.author.id) == int(self.maintainer_id):
            taskmap = self.maps[guild_id]
            taskmap.reset_all()
            taskmap.save()
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send("Sorry you can't do that" + ctx.message.author.id)

    @command()
    @map_checks.map_channel()
    @check_is_owner()
    async def resetallmaps(self, ctx):
        """Allow bot owner to reset any map remotely."""
        if int(self, ctx.message.author.id) == int(self.maintainer_id):
            for taskmap in self.maps.values():
                taskmap.reset_all()
                taskmap.save()
                await ctx.send("Reset map: " + taskmap._data['path'])
        else:
            await ctx.send("Sorry you can't do that" + ctx.message.author.id)

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def setbounds(self, ctx, lat1, long1, lat2, long2):
        """Set the boundaries of the maps for checking when pokestops are added.

        The latitutes and longitudes will form a bounding rectangle, all stops added must fall within these coordinates."""
        taskmap = self.maps[ctx.message.guild.id]
        coords1 = [float(lat1), float(long1)]
        coords2 = [float(lat2), float(long2)]
        taskmap.set_bounds(coords1, coords2)
        try:
            taskmap.save()
            db.set_permission(ctx.channel.id, 'map_ready', True)
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass

    @command()
    @map_checks.map_channel()
    @has_permissions(administrator=True)
    async def settimezone(self, ctx, tz_str):
        """Set the timezone of the map so it resets itself correctly.

        The timezone list can be found at: https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones"""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.set_time_zone(tz_str)
        try:
            taskmap.save()
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass

    @Cog.listener()
    async def on_message(self, message):
        """Deal with tasks and stops in plaintext messages."""
        if message.content.startswith(self.bot.default_prefix):
            self.prev_message_was_stop[message.guild.id] = False
            self.prev_message[message.guild.id] = None
            self.prev_message_stop[message.guild.id] = None
        message.content = message.content.replace(u"\u201C", '"')   # Fixes errors with iOS quotes
        message.content = message.content.replace(u"\u201D", '"')
        for role in message.role_mentions:
            role_str = '<@&' + str(role.id) + '>'
            message.content = message.content.replace(role_str, role.name)
        if message.guild is not None:
            taskmap = self.maps[message.guild.id]
        else:
            return
        if await map_checks.is_map_ready(message, taskmap) is False:
            return
        if message.guild.id not in self.prev_message_was_stop:
            self.prev_message_was_stop[message.guild.id] = False
            self.prev_message[message.guild.id] = None
            self.prev_message_stop[message.guild.id] = None
        if message.author == self.bot.user:
            return
        elif self.prev_message_was_stop[message.guild.id] and self.prev_message[message.guild.id].author == message.author:
            self.prev_message_was_stop[message.guild.id] = False
            if 'shadow' in message.content.lower():
                pokemon = message.content.split()[-1]
                try:
                    if 'shadow' not in pokemon.lower():
                        if 'gone' in message.content.lower():
                            self.prev_message_stop[message.guild.id].reset_shadow()
                        else:
                            self.prev_message_stop[message.guild.id].set_shadow(pokemon)
                    else:
                        self.prev_message_stop[message.guild.id].set_shadow()
                    taskmap.save()
                    await self.prev_message[message.guild.id].add_reaction('👍')
                    await message.add_reaction('👍')
                except pokemap.PokemapException as e:
                    await message.channel.send(e.message)
            else:
                try:
                    task_name = message.content
                    task = self.tasklist.find_task(task_name)
                    self.prev_message_stop[message.guild.id].set_task(task)
                    if task_name.title() in task.rewards:
                        self.prev_message_stop[message.guild.id].properties['Icon'] = task_name.title()
                    taskmap.save()
                    await self.prev_message[message.guild.id].add_reaction('👍')
                    await message.add_reaction('👍')
                except pokemap.TaskAlreadyAssigned:
                    if self.prev_message_stop[message.guild.id].properties['Reward'] == task.reward:
                        await self.prev_message[message.guild.id].add_reaction('👍')
                        await message.add_reaction('👍')
                except pokemap.PokemapException as e:
                    await message.channel.send(e.message)
        else:
            try:
                stop_name = message.content
                self.prev_message_stop[message.guild.id] = taskmap.find_stop(stop_name)
                self.prev_message_was_stop[message.guild.id] = True
                self.prev_message[message.guild.id] = message
            except pokemap.StopNotFound:
                self.prev_message_was_stop[message.guild.id] = False
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
                            task = self.tasklist.find_task(task_name)
                            stop.set_task(task)
                            if task_name.title() in task.rewards:
                                stop.properties['Icon'] = task_name.title()
                        taskmap.save()
                        await message.add_reaction('👍')
                    except pokemap.TaskAlreadyAssigned:
                        if stop.properties['Reward'] == task.reward:
                            await message.add_reaction('👍')
                        else:
                            pass
                    except pokemap.PokemapException:
                        pass
