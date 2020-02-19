from discord.ext.commands import Cog, command, has_permissions
from robowillow.utils import database as db


class Admin(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot
        print("Admin loaded")

    @command()
    @has_permissions(administrator=True)
    async def tradehere(self, ctx, arg=True):
        """Turn on/off trading commands in this channel."""
        if isinstance(arg, str):
            if arg.lower in ['t', 'yes', 'on', 'true']:
                arg = True
            elif arg.lower in ['n', 'no', 'off', 'false']:
                arg = False
        if arg is True or arg == 1:
            db.set_permission(ctx.channel.id, 'trade', True)
        elif arg is False or arg == 0:
            db.set_permission(ctx.channel.id, 'trade', False)
        else:
            ctx.send("Unable to understand. Use on or off as arguement for clarity.")

    @command()
    @has_permissions(administrator=True)
    async def researchhere(self, ctx, arg=True):
        """Turn on/off research commands and reporting in this channel."""
        if isinstance(arg, str):
            if arg.lower in ['t', 'yes', 'on', 'true']:
                arg = True
            elif arg.lower in ['n', 'no', 'off', 'false']:
                arg = False
        if arg is True or arg == 1:
            db.set_permission(ctx.channel.id, 'research', True)
        elif arg is False or arg == 0:
            db.set_permission(ctx.channel.id, 'research', False)
        else:
            ctx.send("Unable to understand. Use on or off as arguement for clarity.")

    @command()
    @has_permissions(administrator=True)
    async def roleshere(self, ctx, arg=True):
        """Turn on/off the ability to control roles in a channel."""
        if isinstance(arg, str):
            if arg.lower in ['t', 'yes', 'on', 'true']:
                arg = True
            elif arg.lower in ['n', 'no', 'off', 'false']:
                arg = False
        if arg is True or arg == 1:
            db.set_permission(ctx.channel.id, 'notifier', True)
        elif arg is False or arg == 0:
            db.set_permission(ctx.channel.id, 'notifier', False)
        else:
            ctx.send("Unable to understand. Use on or off as arguement for clarity.")
