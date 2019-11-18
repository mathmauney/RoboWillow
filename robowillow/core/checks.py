from discord.ext.commands import check


async def check_is_owner(ctx):
    async def _check(ctx):
        return await ctx.bot.is_owner(ctx.author)
    return check(_check(ctx))
