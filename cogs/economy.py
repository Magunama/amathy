from discord.ext import commands
from utils.embed import Embed
from discord.ext.commands.cooldowns import BucketType
from utils.checks import AuthorCheck, GuildCheck
from utils.funx import Level
from math import ceil
import datetime
import random
import asyncio
import discord


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.mc_emoji = bot.get_emoji(bot.consts["mc_emoji_id"])
        self.shop = [
            {"name": ["chest", "chests"], "price": 1200, "currency": "coins"},
            {"name": ["die", "dice"], "price": 80, "currency": "coins"}
        ]
        self.max_bet_value = 20000
        # Chest drops
        # {"trap":66, "nametag":66,"rec":88,"ratioreset":33}
        self.chest_drops = {
            "chests": 50, "keys": 30, "xp": 70, "coins": 90, "gems": 10, "empty": 100
        }
        #########################

    @staticmethod
    def can_buy(have, need):
        if need <= have:
            return True
        return False

    async def buy_item(self, ctx, item, quantity):
        # todo: item limit
        if not quantity.isdigit():
            return await ctx.send("Wrong quantity provided! Usage: `a buy [item] [quantity]`.")
        quantity = int(quantity)
        user_id = ctx.author.id
        name = item["name"][1]
        price = item["price"] * quantity
        curr = item["currency"]
        if curr == "coins":
            bal = (await self.bot.funx.get_coins(user_id))[0]
        else:
            bal = (await self.bot.funx.get_gems(user_id))[0]
        if not self.can_buy(bal, price):
            return await ctx.send(f"Not enough {curr}! You need **{price} {curr}** to buy **{quantity} x {name}**!")

        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["✅", "❎"]

        buy_prompt = f"Do you want to buy {quantity} x **{name}**, {ctx.author.mention}? It will cost you **{price}** {curr}!"
        resp = await ctx.send(buy_prompt)
        await resp.add_reaction("✅")
        await resp.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
        except discord.errors.Forbidden:
            await ctx.send("I need permission to add reactions!")
        except asyncio.TimeoutError:
            await ctx.send("You have not replied. I should tax you 1 MC because you made me lose time for nothing.")

        except Exception as e:
            print(e)
        else:
            await resp.delete()
            if str(reaction) == "❎":
                await ctx.send("It seems like you don't want this item. Why though? Is it dirty?")
            elif str(reaction) == "✅":
                bal -= price
                if curr == "coins":
                    await self.bot.funx.save_pocket(user_id, bal)
                else:
                    await self.bot.funx.save_gems(user_id, bal)
                inv = await self.bot.funx.get_inventory(user_id)
                inv = self.bot.funx.inventory_add(inv, name, quantity)
                await self.bot.funx.save_inventory(user_id, inv)
                await ctx.send(f"You have bought **{quantity} x {name}**! Enjoy!")

    async def get_bet_time(self, user_id):
        script = f"select bet, bet_left from amathy.timers where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            data = datetime.datetime(1, 1, 1), 20
        return data

    async def save_bet_time(self, user_id, bet_left):
        script = f"insert into amathy.timers (user_id, bet_left) values ({user_id}, {bet_left}) on conflict (user_id) do update set bet_left={bet_left}"
        if bet_left == 0:
            time_utc = datetime.datetime.utcnow()
            time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
            script = "insert into amathy.timers (user_id, bet, bet_left) values ({0}, '{1}', {2}) on conflict (user_id) do update set bet='{1}', bet_left={2}"
            script = script.format(user_id, time_now, bet_left)
        await self.bot.funx.execute(script)

    @staticmethod
    def inventory_item_count(inventory, item_name):
        if item_name not in inventory:
            return 0
        return inventory[item_name]

    @staticmethod
    def using_chests(chest_count, key_count, quantity):
        """Returns the number of chests that should be opened"""
        if key_count >= chest_count:
            openable = chest_count
        else:
            openable = key_count
        if quantity.isdigit():
            quantity = int(quantity)
            if quantity > 0:
                if quantity > openable:
                    quantity = openable
            else:
                quantity = 1
        else:
            if quantity in ["all", "max"]:
                quantity = openable
            else:
                quantity = 1
        return quantity

    @commands.command(aliases=["dailymc"])
    async def daily(self, ctx):
        """Fun|Get your daily coins!|"""
        prev_time = await self.bot.funx.get_timer(ctx.author.id, "daily")
        expected_time = prev_time + datetime.timedelta(days=1)  # cooldown
        expected_time = expected_time.replace(hour=0, minute=0, second=0)  # because cooldown should not be constant
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        if time_now >= expected_time:
            # todo: add xp multiplier
            prev_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
            pick = random.randint(25, 100)
            after_coins = prev_coins + pick
            await self.bot.funx.save_pocket(ctx.author.id, after_coins)
            await self.bot.funx.save_timer(ctx.author.id, "daily", time_now)
            text = ["**:moneybag: | You have received {0} {3}, {1}. I see you're kinda lucky. :) You now have {2} {3} in your pocket.**",
                    "**:moneybag: | You have received {0} {3}, {1}. How'd you do that? :) You now have {2} {3} in your pocket.**",
                    "**:moneybag: | You have received {0} {3}, {1}. Have you eaten something special today? :) You now have {2} {3} in your pocket.**"]
            text = random.choice(text)
            await ctx.send(text.format(pick, ctx.author.mention, after_coins, self.mc_emoji))
        else:
            # todo: second use for vip users
            left = self.bot.funx.delta2string(expected_time-time_now)
            text = "**:japanese_ogre: | {}, you still need to wait {} to receive {} (MC) again. Don't rush! >.<**"
            await ctx.send(text.format(ctx.author.mention, left, self.mc_emoji))

    @GuildCheck.is_guild()
    @commands.command()
    async def stats(self, ctx, targ=None):
        """Info|Shows information concerning your current stats.|"""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            targ = ctx.message.author
        joined_at = str(targ.joined_at).split('.', 1)[0]
        created_at = str(targ.created_at).split('.', 1)[0]
        nick = targ.name
        if hasattr(targ, "nick"):
            if targ.nick:
                nick = targ.nick

        title = f"• Nickname: {nick}"
        desc = f"Some details about {targ.name}:"
        author = {"name": "{} ({})".format(targ, targ.id), "icon_url": ""}

        xp, gems, vip_days = await self.bot.funx.get_stats(targ.id)
        lvl = Level().from_xp(xp)
        next_xp = Level().to_xp(lvl)
        progress = f"{lvl} [{xp} XP/{next_xp} XP]"
        pocket_coins, bank_coins = await self.bot.funx.get_coins(targ.id)
        total_coins = pocket_coins + bank_coins
        pocket_coins = self.bot.funx.group_digit(pocket_coins)
        bank_coins = self.bot.funx.group_digit(bank_coins)
        total_coins = self.bot.funx.group_digit(total_coins)

        fields = [["• Created:", created_at, False],
                  ["• Joined:", joined_at, False],
                  ["• Level:", progress, False],
                  ["• Gems:", str(gems), False],
                  ["• VIP days:", str(vip_days), False],
                  ["• Pocket:", f"{pocket_coins} {self.mc_emoji}", False],
                  ["• Bank: ", f"{bank_coins} {self.mc_emoji}", False],
                  ["• Total: ", f"{total_coins} {self.mc_emoji}", False]]
        embed = Embed().make_emb(title, desc, author, fields)
        embed.set_thumbnail(url=targ.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["baga"])
    async def deposit(self, ctx, val=None):
        """Fun|Deposit coins in the bank.|"""
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        pocket_coins, bank_coins = await self.bot.funx.get_coins(ctx.author.id)
        if val in ["all", "max"]:
            val = pocket_coins
        else:
            if val.isdigit():
                val = int(val)
            else:
                text = "**What kind of values are you trying to input? :anger:**"
                return await ctx.send(text)
        if val <= 0:
            text = "**You can't do this.**"
            return await ctx.send(text)
        if pocket_coins < val:
            text = "**You don't have this much {} (MC).**"
            return await ctx.send(text.format(self.mc_emoji))
        pocket_coins -= val
        bank_coins += val
        await self.bot.funx.save_pocket(ctx.author.id, pocket_coins)
        await self.bot.funx.save_bank(ctx.author.id, bank_coins)
        text = ":money_with_wings: **| Transfer successful. :) You have deposited {} {} in the bank.**"
        await ctx.send(text.format(val, self.mc_emoji))

    @commands.command(aliases=["scoate"])
    async def withdraw(self, ctx, val=None):
        """Fun|Withdraw coins from the bank.|"""
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        pocket_coins, bank_coins = await self.bot.funx.get_coins(ctx.author.id)
        if val in ["all", "max"]:
            val = bank_coins
        else:
            if val.isdigit():
                val = int(val)
            else:
                text = "**What kind of values are you trying to input? :anger:**"
                return await ctx.send(text)
        if val <= 0:
            text = "**You can't do this.**"
            return await ctx.send(text)
        if bank_coins < val:
            text = "**You don't have this much {} (MC) in the bank.**"
            return await ctx.send(text.format(self.mc_emoji))
        pocket_coins += val
        bank_coins -= val
        await self.bot.funx.save_pocket(ctx.author.id, pocket_coins)
        await self.bot.funx.save_bank(ctx.author.id, bank_coins)
        text = ":money_with_wings: **| Transfer successful. :) You have withdrawn {} {} from the bank.**"
        await ctx.send(text.format(val, self.mc_emoji))

    @GuildCheck.is_guild()
    @commands.command(aliases=["tf"])
    async def transfer(self, ctx, targ=None, val=None):
        """Fun|Transfer coins to somebody.|"""
        # todo: add reason
        if not (targ and val):
            text = "**You need to enter a username and a value.**"
            return await ctx.send(text)
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            text = "**Invalid username.**"
            return await ctx.send(text)
        if targ.id == ctx.author.id:
            text = "Sorry, {} you can't transfer money to yourself!"
            return await ctx.send(text.format(ctx.author.name))
        user_pocket, user_bank = await self.bot.funx.get_coins(ctx.author.id)
        if val in ["all", "max"]:
            val = user_bank
        else:
            if val.isdigit():
                val = int(val)
            else:
                text = "**What kind of values are you trying to input? :anger:**"
                return await ctx.send(text)
        if val <= 0:
            text = "**You can't do this.**"
            return await ctx.send(text)
        if user_bank < val:
            text = "**You don't have this much {} (MC) in the bank.**"
            return await ctx.send(text.format(self.mc_emoji))

        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["✅", "❎"]

        resp = await ctx.send("Transfer {} {} to {}?".format(val, self.mc_emoji, targ))
        await resp.add_reaction("✅")
        await resp.add_reaction("❎")
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
        except discord.errors.Forbidden:
            await ctx.send("I need permission to add reactions!")
        except asyncio.TimeoutError:
            await ctx.send("I'll take this as a no...")
        except Exception as e:
            print(e)
        else:
            await resp.delete()
            if str(reaction) == "❎":
                text = ":money_with_wings: | {}, it seems like you changed your mind..."
                await ctx.send(text.format(ctx.author.name))
            elif str(reaction) == "✅":
                user_bank -= val
                targ_pocket, targ_bank = await self.bot.funx.get_coins(targ.id)
                targ_bank += val
                await self.bot.funx.save_bank(ctx.author.id, user_bank)
                await self.bot.funx.save_bank(targ.id, targ_bank)
                text = ":euro: **| {} {} transferred successfully to {}.**"
                await ctx.send(text.format(val, self.mc_emoji, targ))
                text = ":euro: | **Transfer notice**\nYou have received a transfer of {} {} from {}!"
                await targ.send(text.format(val, self.mc_emoji, ctx.author))

    @GuildCheck.is_guild()
    @AuthorCheck.is_creator()
    @commands.group(aliases=["ac"])
    async def addcoins(self, ctx):
        """Creator|Adds coin to user.|Creator permission."""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @addcoins.command(name="pocket")
    async def add_pocket(self, ctx, targ=None, val=None):
        """Creator|Adds coins to user's pocket.|Creator permission."""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            text = "**Invalid username.**"
            return await ctx.send(text)
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        if val.isdigit():
            val = int(val)
        else:
            text = "**What kind of values are you trying to input? :anger:**"
            return await ctx.send(text)
        old_coins = (await self.bot.funx.get_coins(targ.id))[0]
        new_coins = old_coins + val
        await self.bot.funx.save_pocket(targ.id, new_coins)
        await ctx.send(f"I've added {val} coins to {targ}'s pocket.")

    @addcoins.command(name="bank")
    async def add_bank(self, ctx, targ=None, val=None):
        """Creator|Add coins to user's bank.|Creator permission."""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            text = "**Invalid username.**"
            return await ctx.send(text)
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        if val.isdigit():
            val = int(val)
        else:
            text = "**What kind of values are you trying to input? :anger:**"
            return await ctx.send(text)
        old_coins = (await self.bot.funx.get_coins(targ.id))[1]
        new_coins = old_coins + val
        await self.bot.funx.save_bank(targ.id, new_coins)
        await ctx.send(f"I've added {val} coins to {targ}'s bank.")

    @GuildCheck.is_guild()
    @AuthorCheck.is_creator()
    @commands.group(aliases=["ec"])
    async def editcoins(self, ctx):
        """Creator|Edits user's coins.|Creator permission."""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @editcoins.command(name="pocket")
    async def edit_pocket(self, ctx, targ=None, val=None):
        """Creator|Edits user's pocket coins.|Creator permission."""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            text = "**Invalid username.**"
            return await ctx.send(text)
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        if val.isdigit():
            val = int(val)
        else:
            text = "**What kind of values are you trying to input? :anger:**"
            return await ctx.send(text)
        await self.bot.funx.save_pocket(targ.id, val)
        await ctx.send(f"I've edited {targ}'s pocket coins to {val}.")

    @editcoins.command(name="bank")
    async def edit_bank(self, ctx, targ=None, val=None):
        """Creator|Edits user's bank coins.|Creator permission."""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            text = "**Invalid username.**"
            return await ctx.send(text)
        if not val:
            text = "**You need to input a value.**"
            return await ctx.send(text)
        if val.isdigit():
            val = int(val)
        else:
            text = "**What kind of values are you trying to input? :anger:**"
            return await ctx.send(text)
        await self.bot.funx.save_bank(targ.id, val)
        await ctx.send(f"I've edited {targ}'s bank coins to {val}.")

    @commands.group()
    async def top(self, ctx):
        """Info|Shows the top 10 users in different categories.|"""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @top.command(aliases=["mc"])
    async def coins(self, ctx):
        """Info|Shows the top 10 people with the most MC.|"""
        script = "select user_id, pocket, bank from amathy.coins"
        data = await self.bot.funx.fetch_many(script)
        top = dict()
        for elem in data:
            user_id, pocket, bank = elem
            top[user_id] = pocket + bank
        sorted_top = sorted(top, key=top.get, reverse=True)
        emb = Embed().make_emb("Global top - MC", "To get coins, use `a daily` or vote for me ([here](https://tiny.cc/voteama)).")
        max_range = 10
        if len(sorted_top) < max_range:
            max_range = len(sorted_top)
        for index in range(0, max_range):
            user_id = sorted_top[index]
            coins = self.bot.funx.group_digit(top[user_id])
            if user_id == ctx.author.id:
                text = "Author position >>> No. {}: {} - {} MC <<<"
                emb.set_footer(text=text.format(index+1, ctx.author.name, coins))
            user = self.bot.get_user(user_id)
            if user:
                emb.add_field(name="No. {}: {}".format(index + 1, user.name), value="{} {}".format(coins, self.mc_emoji))
        await ctx.send(embed=emb)

    @top.command(aliases=["lvl", "level", "exp"])
    async def xp(self, ctx):
        """Info|Shows the top 10 people with the highest level & XP.|"""
        script = "select user_id, xp from amathy.stats"
        data = await self.bot.funx.fetch_many(script)
        top = dict()
        for elem in data:
            user_id, xp = elem
            top[user_id] = xp
        sorted_top = sorted(top, key=top.get, reverse=True)
        emb = Embed().make_emb("Global top - Level & XP", "To get xp, use commands or vote for me ([here](https://tiny.cc/voteama)).")
        max_range = 10
        if len(sorted_top) < max_range:
            max_range = len(sorted_top)
        for index in range(0, max_range):
            user_id = sorted_top[index]
            xp = top[user_id]
            lvl = Level().from_xp(xp)
            xp = self.bot.funx.group_digit(xp)
            if user_id == ctx.author.id:
                text = "Author position >>> No. {}: {} - Level {} - {} XP <<<"
                emb.set_footer(text=text.format(index + 1, ctx.author.name, lvl, xp))
            user = self.bot.get_user(user_id)
            if user:
                emb.add_field(name=f"No. {index + 1}: {user.name}", value=f"Level {lvl} - {xp} XP")
        await ctx.send(embed=emb)

    @top.command()
    async def votes(self, ctx):
        """Info|Shows the top 10 people with the most votes.|"""
        script = "select user_id, monthly_votes, total_votes from amathy.votes"
        data = await self.bot.funx.fetch_many(script)
        top = {"monthly": {}, "total": {}}
        for elem in data:
            user_id, monthly_votes, total_votes = elem
            top["monthly"][user_id] = monthly_votes
            top["total"][user_id] = total_votes
        embeds = list()
        for page in ["monthly", "total"]:
            sorted_top = sorted(top[page], key=top[page].get, reverse=True)
            emb = Embed().make_emb(f"Global top - {page.title()} votes", "To get listed, vote for me ([here](https://tiny.cc/voteama)).")
            max_range = 10
            if len(sorted_top) < max_range:
                max_range = len(sorted_top)
            for index in range(0, max_range):
                user_id = sorted_top[index]
                votes = top[page][user_id]
                if votes == 0:
                    continue
                votes = self.bot.funx.group_digit(votes)
                if user_id == ctx.author.id:
                    text = "Author position >>> No. {}: {} - {} votes <<<"
                    emb.set_footer(text=text.format(index + 1, ctx.author.name, votes))
                user = self.bot.get_user(user_id)
                if user:
                    emb.add_field(name="No. {}: {}".format(index + 1, user.name), value="{} votes".format(votes))
            embeds.append(emb)
        await self.bot.funx.embed_menu(ctx, embeds)

    @commands.command()
    async def buy(self, ctx, item, quantity="1"):
        """Fun|Buy an item from the shop.|"""
        if not item:
            pass
        item = item.lower()
        found = None
        for it in self.shop:
            if item in it["name"]:
                found = it
                break
        if not found:
            return await ctx.send(f"The item {item} can't be found in the shop. :confused: Maybe you missed something?")
        await self.buy_item(ctx, found, quantity)

    @GuildCheck.is_guild()
    @commands.command(aliases=["bag"])
    async def inventory(self, ctx, targ=None):
        """Fun|See your items.|"""
        targ = self.bot.funx.search_for_member(ctx, targ)
        if not targ:
            targ = ctx.message.author
        inventory = await self.bot.funx.get_inventory(targ.id)
        if targ == ctx.author:
            embed = Embed().make_emb("[Inventory]", "These are **your** items:")
        else:
            embed = Embed().make_emb("[Inventory]", f"These are **{targ}**'s items:")

        for item in inventory:
            quantity = f"{inventory[item]} units"
            embed.add_field(name=item.capitalize(), value=quantity, inline=True)
        # embed.set_footer("Page 1/1 - To find out more about an item, use ama iteminfo <item_name>.")
        await ctx.send(embed=embed)

    @commands.command()
    async def shop(self, ctx):
        """Fun|See the shop. Buy or leave?|"""
        emb_links_perm = ctx.channel.permissions_for(ctx.me).embed_links
        if not emb_links_perm:
            return await ctx.send("I need the `embed_links` permission to show you the shop.")
        # xpu = await funx.get_xp(u.id)
        # lv = funx.get_lvl(xpu)
        page_1 = Embed().make_emb(title="[Coin Shop] >>> Amathy sells:", desc="The following can be bought with coins.", footer="Page 1/2 - To buy something, type a buy [item]")
        page_2 = Embed().make_emb(title="[Gem Shop] >>> Amathy sells:", desc="The following can be bought with gems.", footer="Page 2/2 - To buy something, type a buy [item]")
        for item in self.shop:
            price = item["price"]
            # if lv > 0:
            #     price = price * lv
            curr = item["currency"]
            field = " | ".join(item["name"])
            field_str = self.bot.funx.group_digit(price)
            if curr == "coins":
                page_1.add_field(name=field, value=f"{field_str} coins", inline=True)
            else:
                page_2.add_field(name=field, value=f"{field_str} gems", inline=True)
        await self.bot.funx.embed_menu(ctx, [page_1, page_2])

    @commands.command(aliases=["bet"])
    @commands.cooldown(3, 5, BucketType.user)
    async def betcoins(self, ctx, bet_sum=None, guess1=None, guess2=None):
        """Fun|Be the gambler you always wanted to be!|"""
        # todo: add megatoken
        max_bet_value = self.max_bet_value
        usage_text = (
            "Get your coins and bet as a true gambler! This is how to play:\n"
            "       **1.**`a bet [bet_sum]` (You win **x1.5** coins if the rolls are equal);\n"
            "       **2.**`a bet [bet_sum] [guess1]` (You win **x1.5** coins if you guess one number);\n"
            "       **3.**`a bet [bet_sum] [guess1] [guess2]` (You win **x3** coins if you guess both numbers).\n"
            "You have **5%** chance to crack one die. Unused bets **stack** up to **20**.\n"
            "You get to bet every 5 minutes if you don't have any bets stacked.\n"
            "To limit spam, you can do ** no more ** than ** 3 bets ** in ** 5 seconds **."
        )
        if not bet_sum:
            return await ctx.send(usage_text)

        prev_time, bet_left = await self.get_bet_time(ctx.author.id)

        if bet_left == 0:
            expected_time = prev_time + datetime.timedelta(minutes=5)  # time until refill
            time_utc = datetime.datetime.utcnow()
            time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
            if time_now >= expected_time:
                await ctx.send("You will be able to bet again in any moment now.")
            left = self.bot.funx.delta2string(expected_time - time_now)
            text = ":game_die: | {}, you have to wait **{}** until you can throw the dice again."
            return await ctx.send(text.format(ctx.author.mention, left))

        count = await self.bot.funx.get_inv_item_count(ctx.author.id, "dice")
        if count < 2:
            return await ctx.send("You can't roll dice without dice! Buy at least two from the shop to use this command.")

        prev_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
        if bet_sum in ["max", "all"]:
            bet_sum = prev_coins
        else:
            if not bet_sum.isdigit():
                return await ctx.send(usage_text)
            bet_sum = int(bet_sum)
            if not bet_sum > 0:
                return await ctx.send(usage_text)
        if bet_sum > prev_coins:
            return await ctx.send("Insufficient coins to bet!")
        if bet_sum > max_bet_value:
            bet_sum = max_bet_value
            await ctx.send(f"You can't bet more than {max_bet_value} {self.mc_emoji} for now.")

        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)

        mode = 0
        if guess1 is not None:
            if not guess1.isdigit():
                return await ctx.send(usage_text)
            guess1 = int(guess1)
            if not 1 <= guess1 <= 6:
                return await ctx.send(usage_text)
            mode = 1
            if guess2 is not None:
                if not guess2.isdigit():
                    return await ctx.send(usage_text)
                guess2 = int(guess2)
                if not 1 <= guess2 <= 6:
                    return await ctx.send(usage_text)
                mode = 2

        main_text = f":game_die: | Your bet: {bet_sum}. The dice rolled: {roll1}, {roll2}."
        mid_text = f"\nI'm sorry, {ctx.author.name},  you have lost."
        after_bet = 0
        if mode == 0:
            # user wins x1.5 if the rolls are equal
            if roll1 == roll2:
                after_bet = ceil(1.5 * bet_sum)
                mid_text = f"\n{ctx.author.mention}, You have won **{after_bet}** {self.mc_emoji} (x1.5)."
        elif mode == 1:
            # user wins x1.5 if one guess is ok
            if guess1 in [roll1, roll2]:
                after_bet = ceil(1.5 * bet_sum)
                mid_text = f"\n{ctx.author.mention}, You have won **{after_bet}** {self.mc_emoji} (x1.5)."
        else:
            # user wins x3 if both guesses are ok
            if (guess1 == roll1 and guess2 == roll2) or (guess1 == roll2 and guess2 == roll1):
                after_bet = ceil(3 * bet_sum)
                mid_text = f"\n{ctx.author.mention}, You have won **{after_bet}** {self.mc_emoji} (x3)."

        bet_left -= 1
        await self.save_bet_time(ctx.author.id, bet_left)

        after_coins = prev_coins - bet_sum + after_bet
        await self.bot.funx.save_pocket(ctx.author.id, after_coins)

        end_text = f"\n[**{bet_left}** bets left]"
        main_text = main_text + mid_text + end_text

        cracked = random.choices([1, 0], [5, 95])[0]
        if cracked:
            cracked_text = f"\nOh, no, {ctx.author.mention}! One of your dice is now cracked! You need to buy another one."
            inv = await self.bot.funx.get_inventory(ctx.author.id)
            inv = self.bot.funx.inventory_rem(inv, "dice")
            await self.bot.funx.save_inventory(ctx.author.id, inv)
            main_text = main_text + cracked_text

        await ctx.send(main_text)

    @commands.command()
    async def wheel(self, ctx, bet_sum=None):
        """Fun|Spin the Wheel of Fate!|"""
        # todo: check embed perms
        bet_sum_text = "You have to type the value of coins you'd like to bet."
        if not bet_sum:
            return await ctx.send(bet_sum_text)
        max_bet_value = self.max_bet_value
        wheel_data = (
            (":arrow_upper_left:", 1.6), (":arrow_up:", 0.0), (":arrow_upper_right:", 2.3),
            (":arrow_left:", 0.5), (":arrow_right:", 1.2),
            (":arrow_lower_left:", 0.2), (":arrow_down:", 2.0), (":arrow_lower_right:", 2.6)
        )
        prev_time = await self.bot.funx.get_timer(ctx.author.id, "wheel")
        expected_time = prev_time + datetime.timedelta(hours=1)  # cooldown
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        if time_now < expected_time:
            left = self.bot.funx.delta2string(expected_time-time_now)
            text = ":ferris_wheel: | {}, you have to wait **{}** until you can spin the wheel again."
            return await ctx.send(text.format(ctx.author.mention, left))
        prev_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
        if bet_sum in ["max", "all"]:
            bet_sum = prev_coins
        else:
            if not bet_sum.isdigit():
                return await ctx.send(bet_sum_text)
            bet_sum = int(bet_sum)
            if not bet_sum > 0:
                return await ctx.send(bet_sum_text)
        if bet_sum > prev_coins:
            return await ctx.send("Insufficient coins to bet!")
        if bet_sum > max_bet_value:
            bet_sum = max_bet_value
            await ctx.send(f"You can't bet more than {max_bet_value} {self.mc_emoji} for now.")
        pick = random.choice(wheel_data)
        mid_emoji, proc = pick
        after_bet = ceil(bet_sum * proc)
        after_coins = prev_coins - bet_sum + after_bet
        await self.bot.funx.save_pocket(ctx.author.id, after_coins)
        await self.bot.funx.save_timer(ctx.author.id, "wheel", time_now)
        space = 10 * "\u00A0"
        mid_space = 8 * "\u00A0"
        wheel_ret = ""
        for i in range(0, len(wheel_data) + 1):
            if i == 4:
                wheel_ret += f"{mid_space}{mid_emoji}{mid_space}{space}"
            else:
                if i > 4:
                    proc = wheel_data[i-1][1]
                else:
                    proc = wheel_data[i][1]
                wheel_ret += f"(x{proc}){space}"
            if i % 3 == 2:
                wheel_ret += "\n\n"
        emb_desc = f"{ctx.author.mention}, you are left with {after_coins} {self.mc_emoji}... :confused:"
        if after_coins > prev_coins:
            emb_desc = f"{ctx.author.mention}, you made a profit of {after_coins - prev_coins} {self.mc_emoji}!!! :smile:"
        fields = [["Thus The Wheel stopped:", f"**{wheel_ret}**", True]]
        embed = Embed().make_emb("The Wheel of Fortune!", emb_desc, fields=fields)
        await ctx.send(embed=embed)

    @commands.group(aliases=["open"])
    async def use(self, ctx):
        """Fun|Use an item from your bag.|"""
        if ctx.invoked_subcommand is None:
            item_name = ctx.subcommand_passed
            if not item_name:
                return await ctx.send("You haven't selected any item! What do you expect me to do?")
            i_found = None
            for i in self.shop:
                if item_name.lower() in i["name"]:
                    i_found = i["name"]
                    break
            if not i_found:
                return await ctx.send("I don't know this item and I don't know what it does! >.<")
            else:
                await ctx.send("You cannot use this item yet!")

    @use.command(aliases=["chests"])
    async def chest(self, ctx, quantity="1"):
        """Fun|Open a chest and get rewards.|"""
        inventory = await self.bot.funx.get_inventory(ctx.author.id)
        chest_count = self.inventory_item_count(inventory, "chests")
        if chest_count == 0:
            return await ctx.send("I don't see any chests in your inventory!")
        key_count = self.inventory_item_count(inventory, "keys")
        if key_count == 0:
            return await ctx.send("I don't see any keys in your inventory!")

        using = self.using_chests(chest_count, key_count, quantity)
        inventory = self.bot.funx.inventory_rem(inventory, "chests", using)
        inventory = self.bot.funx.inventory_rem(inventory, "keys", using)

        population = list()
        weights = list()
        rewards_dict = dict()
        for item in self.chest_drops:
            population.append(item)
            weights.append(self.chest_drops[item])
            rewards_dict[item] = 0
        rewards = random.choices(population, weights=weights, k=using)
        extra_xp = 0
        for rew in rewards:
            if rew == "chests":
                num = random.randint(1, 2)
            elif rew == "keys":
                num = random.randint(1, 4)
            elif rew == "xp":
                num = random.randint(50, 200)
            elif rew == "gems":
                num = random.randint(1, 10)
            elif rew == "coins":
                num = random.randint(900, 1800)
            else:
                num = 1
            rewards_dict[rew] += num
            extra_xp += random.randint(8, 25)

        empty = rewards_dict["empty"]
        if using == empty:
            rew_text = "You didn't win anything, {}. How unfortunate! :confused: You have received {} bonus xp."
            rew_text = rew_text.format(ctx.author.name, extra_xp)
        else:
            del rewards_dict["empty"]
            rew_text = "Congratulations, {}! You have won the following: `{}`. {} chests were empty. You have received {} bonus xp."
            win_text = ""
            for rew in rewards_dict:
                if rewards_dict[rew] > 0:
                    win_text += f"{rewards_dict[rew]} {rew}, "
            rew_text = rew_text.format(ctx.author.name, win_text[:-2], empty, extra_xp)
            if rewards_dict["chests"] > 0:
                inventory = self.bot.funx.inventory_add(inventory, "chests", rewards_dict["chests"])
            if rewards_dict["keys"] > 0:
                inventory = self.bot.funx.inventory_add(inventory, "keys", rewards_dict["keys"])
            if rewards_dict["coins"] > 0:
                pocket_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
                pocket_coins += rewards_dict["coins"]
                await self.bot.funx.save_pocket(ctx.author.id, pocket_coins)
            if rewards_dict["gems"] > 0:
                gems = await self.bot.funx.get_gems(ctx.author.id)
                gems += rewards_dict["gems"]
                await self.bot.funx.save_gems(ctx.author.id, gems)
        rewards_dict["xp"] += extra_xp
        xp = await self.bot.funx.get_xp(ctx.author.id)
        xp += rewards_dict["xp"]
        await self.bot.funx.save_xp(ctx.author.id, xp)
        await self.bot.funx.save_inventory(ctx.author.id, inventory)
        await ctx.send(rew_text)


def setup(bot):
    bot.add_cog(Economy(bot))
