"""Core of the raid cog."""
from .raid_cog import Raids


def setup(bot):
    """Add the raid cog to a bot."""
    bot.add_cog(Raids(bot))
