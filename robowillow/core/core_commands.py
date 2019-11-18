from discord.ext.commands import Cog, command
from .checks import check_is_owner

class Core(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot
        print("Core loaded")

    @command()
    @check_is_owner()
    async def load(self, ctx, extension):
        """Load or reload one of the extensions."""
        loaded = extension in ctx.bot.extensions
        if loaded:
            ctx.bot.reload_extension(extension)
        else:
            ctx.bot.load_extension(extension)
        await ctx.message.add_reaction('👍')

def setup(bot):
    bot.add_cog(Core(bot))
