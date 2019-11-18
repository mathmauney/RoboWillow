from discord.ext.commands import check


def check_is_owner():
    async def _check(ctx):
        return await ctx.bot.is_owner(ctx.author)
    return check(_check)
