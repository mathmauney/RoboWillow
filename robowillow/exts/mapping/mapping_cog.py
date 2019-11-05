"""Commands to deal with the mapping of research tasks."""
from discord.ext.commands import Cog, command, has_permissions
import urllib.parse as urlparse
from robowillow.utils import pokemap
from datetime import datetime
import discord


class Mapper(Cog):
    """Commands to deal with the mapping of research tasks."""

    def __init__(self, bot):
        """Initialize Cog variables from bot."""
        self.bot = bot
        self.maps = bot.maps
        self.maintainer_id = bot.config.bot_owner
        self.tasklist = bot.tasklist
        self.task_path = bot.config.file_paths['tasklist']
        print("Mapper loaded")

    @command()
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
    async def settask(self, ctx, *args):
        """Set a task to a stop."""
        taskmap = self.maps[ctx.message.guild.id]
        n_args = len(args)
        if n_args > 1:
            try:
                task_str = args[0]
                stop_args = args[1:]
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
    async def addtask(self, ctx, reward, quest, shiny=False):
        """Add a task to a stop."""
        self.tasklist.add_task(pokemap.Task(reward, quest, shiny))
        self.tasklist.save(self.bot.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    async def resettasklist(self, ctx):
        """Backup and reset the self.tasklist."""
        backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
        self.tasklist.save(backup_name)
        self.tasklist.clear()
        await ctx.message.add_reaction('👍')

    @command()
    async def pulltasklist(self, ctx):
        """Pull tasks from TheSilphRoad."""
        backup_name = datetime.now().strftime("%Y.%m.%d.%H%M%S") + '_tasklist_backup.pkl'
        self.tasklist.save(backup_name)
        self.tasklist = pokemap.fetch_tasklist()
        self.tasklist.save(self.task_path)
        await ctx.message.add_reaction('👍')

    @command(aliases=['tasklist'])
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
    async def deletestop(self, ctx, *args):
        """Delete a stop."""
        taskmap = self.maps[ctx.message.guild.id]
        stop_str = ' '.join(args)
        stop = taskmap.find_stop(stop_str)
        taskmap.remove_stop(stop)
        taskmap.save()
        await ctx.message.add_reaction('👍')

    @command()
    async def deletetask(self, ctx, task_str):
        """Delete a task."""
        task = self.tasklist.find_task(task_str)
        self.tasklist.remove_task(task)
        self.tasklist.save(self.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    async def nicknamestop(self, ctx, stop_name, nickname):
        """Add a nickname to a stop."""
        taskmap = self.maps[ctx.message.guild.id]
        stop = taskmap.find_stop(stop_name)
        stop.add_nickname(nickname)
        taskmap.save()
        await ctx.message.add_reaction('👍')

    @command()
    async def nicknametask(self, ctx, task_name, nickname):
        """Add a nickname to a task."""
        task = self.tasklist.find_task(task_name)
        task.add_nickname(nickname)
        self.tasklist.save(self.task_path)
        await ctx.message.add_reaction('👍')

    @command()
    @has_permissions(administrator=True)
    async def setlocation(self, ctx, lat, long):
        """Set the location of the map for the web view."""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.set_location(float(lat), float(long))
        try:
            taskmap.save()
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass

    @command()
    @has_permissions(administrator=True)
    async def resetall(self, ctx):
        """Set the location of the map for the web view."""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.reset_all()
        taskmap.save()

    @command()
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
    @has_permissions(administrator=True)
    async def setbounds(self, ctx, lat1, long1, lat2, long2):
        """Set the boundaries of the maps for checking when pokestops are added."""
        taskmap = self.maps[ctx.message.guild.id]
        coords1 = [float(lat1), float(long1)]
        coords2 = [float(lat2), float(long2)]
        taskmap.set_bounds(coords1, coords2)
        try:
            taskmap.save()
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass

    @command()
    @has_permissions(administrator=True)
    async def settimezone(self, ctx, tz_str):
        """Set the timezone of the map so it resets itself correctly."""
        taskmap = self.maps[ctx.message.guild.id]
        taskmap.set_time_zone(tz_str)
        try:
            taskmap.save()
            await ctx.message.add_reaction('👍')
        except ValueError:
            pass
