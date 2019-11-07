from .trade_cog import Trader

def setup(bot):
    bot.add_cog(Trader(bot))
