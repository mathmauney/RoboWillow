from discord.ext.commands import Cog, command


class Core(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot

    @command()
    async def echo(self, ctx, *args):
        return_str = (' ').join(args).strip(':')
        await ctx.send(return_str)

def setup(bot):
    bot.add_cog(Core(bot))
