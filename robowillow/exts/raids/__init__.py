from .raid_cog import Raids


def setup(bot):
    bot.add_cog(Raids(bot))
