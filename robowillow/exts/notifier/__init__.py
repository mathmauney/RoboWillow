from .notification_cog import Notifier

def setup(bot):
    bot.add_cog(Notifier(bot))
