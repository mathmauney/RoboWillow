"""Core of the administration cog."""
from .admin_cog import Admin


def setup(bot):
    """Add the administration cog to a bot."""
    bot.add_cog(Admin(bot))
