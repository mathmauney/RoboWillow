from discord.ext.commands import Cog


class Core(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Core(bot))
