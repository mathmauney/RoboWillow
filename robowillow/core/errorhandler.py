import discord
from discord.exts.commands import Cog


class ErrorHandler(Cog):

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.errors.Forbidden):
            await self.bot.send_message(ctx.message.author, "You seem to have tried to send a command in a channel I can't talk in. Try again in the appropriate channel")


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
