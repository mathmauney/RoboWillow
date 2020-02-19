"""Core of the mapping cog."""
from .mapping_cog import Mapper


def setup(bot):
    """Add the mapping cog to a bot."""
    bot.add_cog(Mapper(bot))
