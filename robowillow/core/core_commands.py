from discord.ext.commands import Cog, command, errors
import subprocess
from .checks import check_is_owner


class Core(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot
        print("Core loaded")

    @command()
    @check_is_owner()
    async def load(self, ctx, extension_name):
        """Load or reload one of the extensions."""
        subprocess.run("git pull", shell=True, check=True)
        extension = 'robowillow.exts.' + extension_name
        loaded = extension in ctx.bot.extensions
        if loaded:
            ctx.bot.reload_extension(extension)
        else:
            try:
                ctx.bot.load_extension(extension)
            except errors.ExtensionNotFound:
                await ctx.send(f"Extension not found. Currently loaded: {str(ctx.bot.extensions)}")
                return
        await ctx.message.add_reaction('👍')


def setup(bot):
    bot.add_cog(Core(bot))
