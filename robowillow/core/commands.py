import discord
from discord.ext import commands

from robowillow import checks, command
from robowillow.utils import make_embed
from .cog_base import Cog

class Core(Cog):
    """General bot functions."""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @command(name="shutdown", aliases=["exit"], category='Owner')
    @checks.is_owner()
    async def _shutdown(self, ctx):
        """Shuts down the bot"""
        embed = make_embed(
            title='Shutting down.',
            msg_colour='red',
            icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown()

    @command(name="restart", category='Owner')
    @checks.is_owner()
    async def _restart(self, ctx):
        """Restarts the bot"""
        embed = make_embed(
            title='Restarting...',
            msg_colour='red',
            icon="https://i.imgur.com/uBYS8DR.png")
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            pass
        await ctx.bot.shutdown(restart=True)

    @command(name="botinvite", category='Bot Info')
    async def _bot_invite(self, ctx, plain_url: bool = False):
        """Shows bot's invite url"""
        invite_url = ctx.bot.invite_url
        if plain_url:
            await ctx.send("Invite URL: <{}>".format(invite_url))
            return
        else:
            embed = make_embed(
                title='Click to invite me to your server!',
                title_url=invite_url,
                msg_colour='blue',
                icon="https://i.imgur.com/DtPWJPG.png")
        try:
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            await ctx.send("Invite URL: <{}>".format(invite_url))
