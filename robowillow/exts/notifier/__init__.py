"""Core of the notification cog."""
from .notification_cog import Notifier


def setup(bot):
    """Add the notification cog to a bot."""
    bot.add_cog(Notifier(bot))
