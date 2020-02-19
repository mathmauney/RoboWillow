"""Commands for raid organization and information."""
from discord.ext.commands import Cog, command, has_permissions
from robowillow.utils import pokemap
from robowillow.utils import database as db
from . import raid_checks


class Raids(Cog):
    """Cog for raid help commands."""

    def __init__(self, bot):
        """Start the raid cog."""
        self.bot = bot

    @command()
    @raid_checks.raid_channel()
    def infographic(self, ctx, pokemon=None):
        """Return the pokebattler infographic for a pokemon if it exists."""
        if pokemon is None:
            pokemon = db.raid_pokemon()
        match = pokemap.match_pokemon(pokemon)
        if match is None:
            await ctx.send("Pokemon not found.")
            return
        url = "https://static.pokebattler.com/graphics/Infographics/0/" + match.upper() + "_2160.png"
        ctx.send(url)   # TODO: try to grab the imgage and put it in
        # TODO: have it fallback to the pokebattler page for the pokemon if there ins't an infographic

    @command()
    @has_permissions(administrator=True)
    @raid_checks.raid_channel()
    def set_current(self, ctx, pokemon):
        """Set the default 5* boss."""
        match = pokemap.match_pokemon(pokemon)
        db.raid_pokemon(match)
        await ctx.message.add_reaction('👍')
