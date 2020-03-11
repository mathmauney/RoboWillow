"""Commands for raid organization and information."""
from discord.ext.commands import Cog, command, has_permissions
from robowillow.utils import pokemap
from . import raid_checks
import requests
from datetime import datetime


class Raids(Cog):
    """Cog for raid help commands."""

    def __init__(self, bot):
        """Start the raid cog."""
        self.bot = bot
        response = requests.get("https://fight.pokebattler.com/raids")
        self.raids = response.json()['tiers']
        self.check_time = datetime.utcnow()
        self.refresh_interval = 15  # How many minutes must elapse before requerying pokebattler

    def check(self):
        """Check for new raids if it has been long enough."""
        delta = datetime.utcnow() - self.check_time()
        if delta > 60*self.refresh_interval:
            response = requests.get("https://fight.pokebattler.com/raids")
            self.raids = response.json()['tiers']
            self.check_time = datetime.utcnow()

    @command()
    @raid_checks.raid_channel()
    async def infographic(self, ctx, pokemon=None):
        """Return the pokebattler infographic for a pokemon if it exists."""
        self.check()
        if pokemon is None:
            for tier in self.raids:
                if tier['tier'] == "RAID_LEVEL_5":
                    for item in tier['raids']:
                        if item['article'] is None:
                            pass
                        else:
                            url = item['article']['infographicShareURL']
                            await ctx.send(url)
                            return
        else:
            match = pokemap.match_pokemon(pokemon)
            if match is None:
                await ctx.send("Pokemon not found.")
                return
            for tier in self.raids:
                for item in tier['raids']:
                    if match.upper() in item['pokemon']:
                        if item['article'] is None:
                            pass
                        else:
                            url = item['article']['infographicShareURL']
                            await ctx.send(url)
                            return
            await ctx.send(f"Pokebattler infographic not found for {match}.")
