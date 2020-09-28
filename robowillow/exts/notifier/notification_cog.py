"""Commands to deal with the setting sighting roles."""
from discord.ext.commands import Cog, command
from robowillow.utils import pokemap
from . import notification_checks
import discord


class Notifier(Cog):
    """Commands to deal with notification of sightings."""

    def __init__(self, bot):
        """Initialize Cog variables from bot."""
        self.bot = bot
        print("Notifier Loaded.")

    @command()
    @notification_checks.notification_channel()
    async def want(self, ctx, *roles):
        """Set a given pokemon sighting role to a user."""
        all_pokemon = True
        bad = ''
        for role in roles:
            match = pokemap.match_pokemon(role)
            if match is not None:
                user = ctx.message.author
                role_obj = discord.utils.get(ctx.message.guild.roles, name=match.lower())
                if role_obj is None:
                    await ctx.message.guild.create_role(name=match.lower(), mentionable=True)
                    role_obj = discord.utils.get(ctx.message.guild.roles, name=match.lower())
                await user.add_roles(role_obj)
            else:
                bad += ' ' + role
                all_pokemon = False
        if all_pokemon:
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Not all requests matched known pokemon. Unable to match:' + bad)

    @command()
    @notification_checks.notification_channel()
    async def unwant(self, ctx, *roles):
        """Remove sighting role(s) from a user."""
        bad = ''
        for role in roles:
            role = role.strip(',')
            if role.lower() == 'all':
                user = ctx.message.author
                roles = ctx.message.author.roles
                for role in roles:
                    match = pokemap.match_pokemon(role)
                    if match is not None:
                        await user.remove_roles(role)
                await ctx.message.add_reaction('👍')
                return
            else:
                match = pokemap.match_pokemon(role)
                if match is not None:
                    user = ctx.message.author
                    role_obj = discord.utils.get(user.guild.roles, name=match.lower())
                    await user.remove_roles(role_obj)
                else:
                    bad += ' ' + role
        if bad == '':
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Not all requests matched known pokemon. Unable to match:' + bad)

    @command()
    @notification_checks.notification_channel()
    async def listwants(self, ctx):
        """List all pokemon sighting roles a user has."""
        roles = ctx.message.author.roles
        pokemon = []
        embed_str = []
        str_num = 0
        embed_str.append('')

        with open('pokemon.txt') as file:
            line = file.readline()
            while line:
                for role in roles:
                    if role.name.title() in line:
                        pokemon.append(role.name.title())
                line = file.readline()
        if pokemon == []:
            await ctx.send('No want roles found.')
        else:
            for mon in pokemon:
                to_add = mon + '\n'
                if (len(embed_str[str_num]) + len(to_add) > 1000):
                    str_num += 1
                    embed_str.append('')
                embed_str[str_num] += to_add
            for i in range(len(embed_str)):
                msg = discord.Embed(colour=discord.Colour(0x186a0))
                msg.add_field(name='You are looking for:', value=embed_str[i], inline=False)
                await ctx.send(embed=msg)
