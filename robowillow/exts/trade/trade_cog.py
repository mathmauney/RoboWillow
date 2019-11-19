"""Commands to deal with arranging trades."""
from discord.ext.commands import Cog, command, has_permissions
from robowillow.utils import trade_functions as tf
from . import trade_checks
import discord


class Trader(Cog):
    """Commands to deal with arranging trades."""

    def __init__(self, bot):
        """Initialize Cog variables from bot."""
        self.bot = bot
        self.prev_matches = {}
        self.prev_views = {}
        self.prev_search = {}
        print("Trader loaded")

    async def process_matches(self, ctx, message, offer, reply=False):
        """Check for matches on an offer and notify both parties if there are matches."""
        matches = tf.parse_matches(offer)
        offer_dict = tf.offers.find_one(offer)
        sender = message.author
        # matches = [(['Squirtle', 'Charmander'], ['Bulbasaur', 'Pikachu', 'Raichu'], 200038656021364736)]
        embed_components = []
        for match in matches:
            if len(match[0]) == 1:
                want_str = match[0][0]
            elif len(match[0]) == 2:
                want_str = ' or '.join(match[0])
            else:
                want_str = ', '.join(match[0][:-1]) + ', or ' + match[0][-1]
            if len(match[1]) == 1:
                have_str = match[1][0]
            elif len(match[1]) == 2:
                have_str = ' or '.join(match[1])
            else:
                have_str = ', '.join(match[1][:-1]) + ', or ' + match[1][-1]
            embed_components.append((want_str, have_str, match[2]))
            match_user_id = match[2]
            if match_user_id not in offer_dict['notified']:
                notification = "Trade matched! Your %s for <@%s>'s %s" % (want_str, str(sender.id), have_str)
                match_user = await self.bot.get_user_info(match_user_id)
                await match_user.send_message(notification)
                tf.set_notified(offer, match_user_id)
            other_offer = tf.offers.find_one(match[3])
            tf.set_notified(other_offer, int(sender.id))
        if embed_components != []:
            embed_strs = ['']
            embed_num = 0
            for component in embed_components:
                to_add = "Your %s for <@%s>'s %s.\n" % (component[1], str(component[2]), component[0])
                if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
                    embed_num += 1
                    embed_strs.append('')
                embed_strs[embed_num] += to_add
            self.prev_matches[message.author.id] = embed_strs
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Matches', value=embed_strs[0], inline=False)
            embed.set_footer(text='Page 1 of %s. Use %smorematches n to see page n.' % (len(embed_strs), self.bot.default_prefix))
            await ctx.send(embed=embed)
        elif reply is True:
            await ctx.send('No matches found')

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def morematches(self, ctx, page):
        """Return page n of a previous match result."""
        embed_strs = self.prev_matches.get(ctx.message.author.id, None)
        if int(page) > len(embed_strs):
            await ctx.send('Page out of range')
        if embed_strs is not None:
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Matches', value=embed_strs[int(page)-1], inline=False)
            embed.set_footer(text='Page %s of %s. Use %smorematches n to see page n.' % (page, len(embed_strs), self.bot.default_prefix))
            await ctx.send(embed=embed)

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def moreresults(self, ctx, page):
        """Return page n of a previous search result."""
        embed_strs = self.prev_search.get(ctx.message.author.id, None)
        if int(page) > len(embed_strs):
            await ctx.send('Page out of range')
        if embed_strs is not None:
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Search Results', value=embed_strs[int(page)-1], inline=False)
            embed.set_footer(text='Page %s of %s. Use %smoreresults n to see page n.' % (page, len(embed_strs), self.bot.default_prefix))
            await ctx.send(embed=embed)

    @command(pass_context=True, aliases=['newoffer'])
    @trade_checks.trade_channel()
    async def addoffer(self, ctx, offer_name):
        """Make a new offer."""
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        if ('<:') in offer_name:
            offer_name = offer_name.split(":")[1]
        if tf.find_offer(user, offer_name) is None:
            tf.add_offer(user, offer_name)
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send("Offer group already exists.")

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def deleteoffer(self, ctx, offer_name):
        """Delete an offer or offers."""
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        offer = tf.find_offer(user, offer_name)
        if offer is not None:
            tf.delete_offer(offer)
            await ctx.message.add_reaction('👍')
        else:
            await ctx.send('Unable to find offer')

    @command(pass_context=True, aliases=['deletewants'])
    @trade_checks.trade_channel()
    async def deletewant(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        if len(pokemon) == 0 or pokemon[0] == 'all':
            tf.remove_wants(offer, 'all')
            await ctx.send('Removed all wants')
        else:
            cleaned_list = tf.clean_pokemon_list(pokemon)
            tf.remove_wants(offer, cleaned_list)
            await ctx.send('Removed: ' + ', '.join(cleaned_list))

    @command(pass_context=True, aliases=['deletehaves'])
    @trade_checks.trade_channel()
    async def deletehave(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        if len(pokemon) == 0 or pokemon[0] == 'all':
            tf.remove_haves(offer, 'all')
            await ctx.send('Removed all haves')
        else:
            cleaned_list = tf.clean_pokemon_list(pokemon)
            tf.remove_haves(offer, cleaned_list)
            await ctx.send('Removed: ' + ', '.join(cleaned_list))

    @command(pass_context=True, aliases=['addwants'])
    @trade_checks.trade_channel()
    async def addwant(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon)
        tf.add_wants(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Added: ' + ', '.join(cleaned_list))
            await self.process_matches(ctx, ctx.message, offer)

    @command(pass_context=True, aliases=['addhaves'])
    @trade_checks.trade_channel()
    async def addhave(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon)
        tf.add_haves(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Added: ' + ', '.join(cleaned_list))
            await self.process_matches(ctx, ctx.message, offer)

    @command(pass_context=True, aliases=['deleteshinywants'])
    @trade_checks.trade_channel()
    async def deleteshinywant(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon, True)
        tf.remove_wants(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Removed: ' + ', '.join(cleaned_list))

    @command(pass_context=True, aliases=['deleteshinyhaves'])
    @trade_checks.trade_channel()
    async def deleteshinyhave(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon, True)
        tf.remove_haves(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Removed: ' + ', '.join(cleaned_list))

    @command(pass_context=True, aliases=['addshinywants'])
    @trade_checks.trade_channel()
    async def addshinywant(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon, True)
        tf.add_wants(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Added: ' + ', '.join(cleaned_list))
            await self.process_matches(ctx, ctx.message, offer)

    @command(pass_context=True, aliases=['addshinyhaves'])
    @trade_checks.trade_channel()
    async def addshinyhave(self, ctx, offer_name, *pokemon):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        cleaned_list = tf.clean_pokemon_list(pokemon, True)
        tf.add_haves(offer, cleaned_list)
        if len(cleaned_list) == 0:
            await ctx.message.add_reaction('❌')
        else:
            await ctx.send('Added: ' + ', '.join(cleaned_list))
            await self.process_matches(ctx, ctx.message, offer)

    @command(pass_context=True, aliases=['viewoffer'])
    @trade_checks.trade_channel()
    async def view(self, ctx, offer_name):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send('Offer not found')
            return
        (wants, haves) = tf.get_offer_contents(offer)
        if haves == []:
            have_strs = ['None']
            want_strs = ['']
        else:
            i = 0
            have_strs = ['']
            want_strs = ['']
            for have in haves:
                if len(have_strs[i]) > 500:
                    i = i + 1
                    have_strs.append('')
                    want_strs.append('')
                have_strs[i] = have_strs[i] + have + '\n'
        if wants == []:
            want_strs[0] = 'None'
        else:
            i = 0
            for want in wants:
                if len(want_strs[i]) > 500:
                    i = i + 1
                    if i >= len(have_strs):
                        have_strs.append('')
                        want_strs.append('')
                want_strs[i] = want_strs[i] + want + '\n'
        self.prev_views[ctx.message.author.id] = (have_strs, want_strs)
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.set_footer(text='Page 1 of %s. Use %sviewmore n to see page n.' % (len(want_strs), self.bot.default_prefix))
        embed.add_field(name='Have', value=have_strs[0], inline=False)
        embed.add_field(name='Want', value=want_strs[0], inline=False)
        await ctx.send(embed=embed)

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def viewmore(self, ctx, page):
        (have_strs, want_strs) = self.prev_views.get(ctx.message.author.id, (None, None))
        if int(page) > len(have_strs):
            await ctx.send('Page out of range')
        if have_strs is not None:
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            have_str = have_strs[int(page)-1]
            want_str = want_strs[int(page)-1]
            if have_str != '':
                embed.add_field(name='Haves', value=have_str, inline=False)
            if want_str != '':
                embed.add_field(name='Wants', value=want_str, inline=False)
            embed.set_footer(text='Page %s of %s. Use %sviewmore n to see page n.' % (page, len(want_strs), self.bot.default_prefix))
            await ctx.send(embed=embed)

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def check(self, ctx, offer_name=None):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        if offer_name is None:
            await ctx.send("No offer group supplied")
            return
        offer = tf.find_offer(user, offer_name)
        if ('<:') in offer_name and offer is None:
            offer_name = offer_name.split(":")[1]
            offer = tf.find_offer(user, offer_name)
        if offer is None:
            await ctx.send("Offer group not found.")
            return
        await self.process_matches(ctx, ctx.message, offer, True)

    @command(pass_context=True, aliases=['viewoffers'])
    @trade_checks.trade_channel()
    async def listoffers(self, ctx):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        offer_names = tf.find_offers(user)
        if offer_names == []:
            await ctx.send('No offers found')
        else:
            offer_str = '\n'.join(offer_names)
            embed = discord.Embed(colour=discord.Colour(0x186a0))
            embed.add_field(name='Offer Names', value=offer_str, inline=False)
            await ctx.send(embed=embed)

    @command(pass_context=True)
    @trade_checks.trade_channel()
    async def setname(self, ctx, pogo_name):
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if ctx.message.guild is not None:
            tf.add_community(user, ctx.message.guild.id)
        try:
            tf.set_name(user, pogo_name.title())
            await ctx.message.add_reaction('👍')
        except ValueError:
            await ctx.send('Name already in use, please contact <@%s> if you think this is in error.' % self.bot.owner)

    @command(pass_context=True, aliases=['viewuseroffer'])
    @trade_checks.trade_channel()
    async def viewuseroffers(self, ctx, pogo_name, *search_terms):
        user = tf.find_user(pogo_name.title())
        if user is None:
            await ctx.send('User not found')
        else:
            if len(search_terms) == 0:
                offer_names = tf.find_offers(user)
                if offer_names == []:
                    await ctx.send('No offers found')
                else:
                    offer_str = '\n'.join(offer_names)
                    embed = discord.Embed(colour=discord.Colour(0x186a0))
                    embed.add_field(name='Offer Names', value=offer_str, inline=False)
                    await ctx.send(embed=embed)
            elif len(search_terms) == 1:
                offer_name = search_terms[0]
                offer = tf.find_offer(user, offer_name)
                (wants, haves) = tf.get_offer_contents(offer)
                if haves == []:
                    have_strs = ['None']
                    want_strs = ['']
                else:
                    i = 0
                    have_strs = ['']
                    want_strs = ['']
                    for have in haves:
                        if len(have_strs[i]) > 500:
                            i = i + 1
                            have_strs.append('')
                            want_strs.append('')
                        have_strs[i] = have_strs[i] + have + '\n'
                if wants == []:
                    want_strs[0] = 'None'
                else:
                    i = 0
                    for want in wants:
                        if len(want_strs[i]) > 500:
                            i = i + 1
                            if i >= len(have_strs):
                                have_strs.append('')
                                want_strs.append('')
                        want_strs[i] = want_strs[i] + want + '\n'
                self.prev_views[ctx.message.author.id] = (have_strs, want_strs)
                embed = discord.Embed(colour=discord.Colour(0x186a0))
                embed.set_footer(text='Page 1 of %s. Use %sviewmore n to see page n.' % (len(want_strs), self.bot.default_prefix))
                embed.add_field(name='Haves', value=have_strs[0], inline=False)
                embed.add_field(name='Wants', value=want_strs[0], inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send('Too many arguments')

    @command(pass_context=True, aliases=['searchhaves'])
    @trade_checks.trade_channel()
    async def searchhave(self, ctx, *search_terms):
        cleaned_list = tf.clean_pokemon_list(search_terms)
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if len(cleaned_list) != 1:
            await ctx.send('Too many or too few pokemon matched: ' % ', '.join(cleaned_list))
            return
        results = tf.search_haves(user, cleaned_list[0])
        if len(results) == 0:
            await ctx.send('No public offers matching query found.')
            return
        embed_strs = ['']
        embed_num = 0
        for result in results:
            to_add = "%s (<@%s>)'s offer: %s.\n" % (result[1], str(result[0]), result[2])
            if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
                embed_num += 1
                embed_strs.append('')
            embed_strs[embed_num] += to_add
        self.prev_search[ctx.message.author.id] = embed_strs
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.add_field(name='Search Results', value=embed_strs[0], inline=False)
        embed.set_footer(text='Page 1 of %s. Use %smoreresults n to see page n.' % (len(embed_strs), self.bot.default_prefix))
        await ctx.send(embed=embed)

    @command(pass_context=True, aliases=['searchwants'])
    @trade_checks.trade_channel()
    async def searchwant(self, ctx, *search_terms):
        cleaned_list = tf.clean_pokemon_list(search_terms)
        user = tf.get_user(ctx.message.author.id)
        if user is None:
            user = tf.add_user(ctx.message.author.id)
        if len(cleaned_list) != 1:
            await ctx.send('Too many or too few pokemon matched: ' % ', '.join(cleaned_list))
            return
        results = tf.search_wants(user, cleaned_list[0])
        if len(results) == 0:
            await ctx.send('No public offers matching query found.')
            return
        embed_strs = ['']
        embed_num = 0
        for result in results:
            to_add = "%s (<@%s>)'s offer: %s.\n" % (result[1], str(result[0]), result[2])
            if (len(embed_strs[embed_num]) + len(to_add)) > 1000:
                embed_num += 1
                embed_strs.append('')
            embed_strs[embed_num] += to_add
        self.prev_search[ctx.message.author.id] = embed_strs
        embed = discord.Embed(colour=discord.Colour(0x186a0))
        embed.add_field(name='Search Results', value=embed_strs[0], inline=False)
        embed.set_footer(text='Page 1 of %s. Use %smoreresults n to see page n.' % (len(embed_strs), self.bot.default_prefix))
        await ctx.send(embed=embed)

    @command()
    @trade_checks.trade_channel()
    async def tutorial(self, ctx):
        """Shows a tutorial on how to use the trade functions of the bot."""
        msg = discord.Embed(colour=discord.Colour(0x186a0))
        intro_text = """This bot allows you to create trade offers.
- You can offer pokemon A,B,C.. for pokemon X,Y,Z... (no limits!)
- You can have multiple offers (for shinies, regionals, pvp wishlists, unowns, etc)
- You can search and view other people offers!
- You will receive notifications when you and another person match!"""
        instruction_text = """All messages must be sent in the form of a (?) command. To begin, add your pogo-username using:
?setname <pogo_name>
- Replace <pogo_name> with your in-game username

Now you can create trade offers using:
?addoffer <offer_name>
- Replace <offer_name> with any word. This will be the title of your trade offer.

Add pokemon to your offer using:
?addwant <offer_name> <pokemon>
?addhave <offer_name> <pokemon>
- Replace <offer_name> with the offer you want to edit
- Replace <pokemon> with the pokemon you want/have
- Both commands can take multiple pokemon seperated by spaces

- Modifiers can be added to the pokemon names if needed
- Shiny can be added before the pokemon name (ex. Shiny Pikachu)
- Forms can be added before the pokemon name (ex. Altered Giratina or Shedinja Costume Bulbasaur)
- Unown letters and Spinda numbers can be added after the pokemon name (ex. Unown A or Spinda 1)"""
        instruction_text2 = """Remove pokemon from your offer using:\n
?deletewant <offer_name> <pokemon>
?deletehave <offer_name> <pokemon>
- Delete all pokemon by not listing any after the offer name

To add or remove multiple shinies at once use:
?addshinywant, ?addshinyhave, ?deleteshinywant or ?deleteshinyhave
- These are the same as the normal commands will assume all pokemon listed are shiny

Remove an offer completely using:
?deleteoffer <offer_name>

To view a list of all your offers, use:
?listoffers

To view the contents of one of your offers use:
?viewoffer <offer_name>

To search everyone else's offers for a specific pokemon use:
?searchwant <pokemon>
?searchhave <pokemon>
- These will return a list of each person that has the pokemon and the name of their offer

To view someone else's offer(s) use:
?listoffers <pogo_name>
?viewoffer <pogo_name> <offer_name>

When you and someone else match you will be notified automatically. You can view all your matches using ?check"""
        msg.add_field(name='Tutorial', value=intro_text, inline=False)
        msg.add_field(name='Tutorial', value=instruction_text, inline=False)
        msg.add_field(name='Tutorial cont.', value=instruction_text2, inline=False)
        await ctx.send(embed=msg)
