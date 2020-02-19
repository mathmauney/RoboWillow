"""Core of the raid cog."""
from .trade_cog import Trader


def setup(bot):
    """Add the trade cog to a bot."""
    bot.add_cog(Trader(bot))
