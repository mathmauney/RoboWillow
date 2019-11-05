import pickle
from robowillow.utils import pokemap
import discord
from discord.ext import commands
from discord.utils import cached_property
import logging

from robowillow import config
# from robowillow.utils import pagination
# from meowth.core.context import Context
# from meowth.core.data_manager import DatabaseInterface, DataManager
# from meowth.utils import ExitCodes, fuzzymatch, make_embed, pagination


class Bot(commands.Bot):
    """Core logic of the Discord Bot."""

    def __init__(self, **kwargs):
        self.default_prefix = config.bot_prefix
        self.owner = config.bot_owner
        self.config = config
        self.token = config.bot_token
        self.maps = {}
        self.prev_message_was_stop = {}
        self.prev_message_stop = {}
        self.prev_message = {}
        self.req_perms = discord.Permissions(config.bot_permissions)
        # Import the tasklist object or create new one
        try:
            self.task_path = self.config.file_paths['tasklist']
            with open(self.task_path, 'rb') as file_input:
                self.tasklist = pickle.load(file_input)
        except FileNotFoundError:
            self.tasklist = pokemap.Tasklist()
        self.req_perms = discord.Permissions(config.bot_permissions)
        kwargs = dict(owner_id=self.owner,
                      command_prefix=self.default_prefix,
                      status=discord.Status.online,
                      case_insensitive=True,
                      **kwargs)
        super().__init__(**kwargs)
        self.logger = logging.getLogger('willow.Bot')

    # async def send_cmd_help(self, ctx, **kwargs):
    # async def send_cmd_help(self, ctx, **kwargs):
    #     """Invoke help output for a command.

    #     Parameters
    #     -----------
    #     ctx: :class:`discord.ext.commands.Context`
    #         Context object from the originally invoked command.
    #     per_page: :class:`int`
    #         Number of entries in the help embed page. 12 is default.
    #     title: :class:`str`
    #         Title of the embed message.
    #     """
    #     try:
    #         if ctx.invoked_subcommand:
    #             kwargs['title'] = kwargs.get('title', 'Sub-Command Help')
    #             p = await pagination.Pagination.from_command(
    #                 ctx, ctx.invoked_subcommand, **kwargs)
    #         else:
    #             kwargs['title'] = kwargs.get('title', 'Command Help')
    #             p = await pagination.Pagination.from_command(
    #                 ctx, ctx.command, **kwargs)
    #         await p.paginate()
    #     except discord.DiscordException as exc:
    #         await ctx.send(exc)

    @cached_property
    def invite_url(self):
        invite_url = discord.utils.oauth_url(self.user.id,
                                             permissions=self.req_perms)
        return invite_url

    # ====================Events==========================
    async def on_guild_join(self, guild):
        """Take actions on server join."""
        map_dir = self.config.file_paths['map_directory']
        map_path = map_dir + str(guild.id) + '.json'
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
        self.maps[guild.id] = taskmap

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_connect(self):
        print('Connected')
        await self.change_presence(status=discord.Status.idle)

    async def on_ready(self):
        await self.change_presence(game=discord.Game(name=self.config.bot_status))  # Sets the game presence
        print("Logged in as " + self.user.name)  # Logs sucessful login
        map_dir = self.config.file_paths['map_directory']
        for server in self.guilds:
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
            self.maps[server.id] = taskmap
            self.prev_message_was_stop[server.id] = False
