from discord.ext import commands
from utils.embed import Embed
from utils.checks import is_creator
import datetime
import random
import asyncio
import discord


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.mc_emoji = bot.get_emoji(bot.consts["mc_emoji_id"])
        self.shop = [{"name": ["chest", "chests"], "price": 1200, "currency": "coins"},
                     {"name": ["die", "dice"], "price": 80, "currency": "coins"}]

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
        name = item["name"][0]
        price = item["price"] * quantity
        curr = item["currency"]
        if curr == "coins":
            bal = (await self.bot.funx.get_coins(user_id))[0]
        else:
            bal = (await self.bot.funx.get_gems(user_id)[0])
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

    @commands.guild_only()
    @commands.command(aliases=["dailymc"])
    async def daily(self, ctx):
        """Fun|Get your daily coins!|"""
        prev_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
        prev_time = await self.bot.funx.get_timer(ctx.author.id, "daily")
        expected_time = prev_time + datetime.timedelta(days=1)  # cooldown
        expected_time = expected_time.replace(hour=0, minute=0, second=0)  # because cooldown should not be constant
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        if time_now >= expected_time:
            # todo: add xp multiplier
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

    @commands.guild_only()
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

        # script = "SELECT xp, imgsite, bio FROM stats WHERE user_id={}".format(targ.id)
        # datasite = await funx.run_q(script)
        # if datasite:
        #     xpu, imgsite, bio = datasite
        # else:
        #     xpu, imgsite, bio = [0, None, None]
        # lv = funx.get_lvl(xpu)
        # if lv == 25:
        #     prog = "  [" + str(xpu) + "/0]"
        # elif lv > -1:
        #     prog = "  [" + str(xpu) + "/" + str(funx.xpatrib[lv + 1]) + "]"
        # else:
        #     prog = "  [0/0]"
        # embed.add_field(
        #     name="• Level",
        #     value=str(lv) + prog + "  (" + funx.get_lvlname(lv) + ")",
        # )
        # usr = await funx.get_rank(targ.id)
        # if 3 <= usr <= 6:
        #     climit, blimit = 80 * (10 ** 6), 120 * (10 ** 6)
        # elif usr > 6:
        #     climit, blimit = 80 * (10 ** 6), 170 * (10 ** 6)
        # else:
        #     climit, blimit = 20 * (10 ** 6), 100 * (10 **
        xp, gems, vip_days = await self.bot.funx.get_stats(targ.id)
        pocket_coins, bank_coins = await self.bot.funx.get_coins(targ.id)
        total_coins = pocket_coins + bank_coins
        pocket_coins = self.bot.funx.group_digit(pocket_coins)
        bank_coins = self.bot.funx.group_digit(bank_coins)
        total_coins = self.bot.funx.group_digit(total_coins)

        # if bio:
        #     embed.add_field(
        #         name="• Bio",
        #         value=bio,
        #     )
        # if imgsite:
        #     embed.set_image(url=imgsite)
        #     embed.add_field(
        #         name=" ឵឵ ឵឵",
        #         value="**• Avatar site**",
        #         inline=False,
        #     )
        fields = [["• Created:", created_at, False],
                  ["• Joined:", joined_at, False],
                  ["• XP:", str(xp), False],
                  ["• Gems:", str(gems), False],
                  ["• VIP days:", str(vip_days), False],
                  ["• Pocket:", f"{pocket_coins} {self.mc_emoji}", False],
                  ["• Bank: ", f"{bank_coins} {self.mc_emoji}", False],
                  ["• Total: ", f"{total_coins} {self.mc_emoji}", False]]
        embed = Embed().make_emb(title, desc, author, fields)
        embed.set_thumbnail(url=targ.avatar_url)
        await ctx.send(embed=embed)

    @commands.guild_only()
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

    @commands.guild_only()
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

    @commands.guild_only()
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

    @commands.guild_only()
    @commands.group(aliases=["ac"])
    @is_creator()
    async def addcoins(self, ctx):
        """Utility|Adds coin to user.|Creator permission."""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @addcoins.command(name="pocket")
    async def add_pocket(self, ctx, targ=None, val=None):
        """Utility|Adds coins to user's pocket.|"""
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
        await self.bot.funx.save_pocket(ctx.author.id, new_coins)
        await ctx.send(f"I've added {val} coins to {targ}'s pocket.")

    @addcoins.command(name="bank")
    async def add_bank(self, ctx, targ=None, val=None):
        """Utility|Add coins to user's bank.|"""
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
        await self.bot.funx.save_bank(ctx.author.id, new_coins)
        await ctx.send(f"I've added {val} coins to {targ}'s bank.")

    @commands.guild_only()
    @commands.group(aliases=["ec"])
    @is_creator()
    async def editcoins(self, ctx):
        """Utility|Edits user's coins.|Creator permission."""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @editcoins.command(name="pocket")
    async def edit_pocket(self, ctx, targ=None, val=None):
        """Utility|Edits user's pocket coins.|"""
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
        await self.bot.funx.save_pocket(ctx.author.id, val)
        await ctx.send(f"I've edited {targ}'s pocket coins to {val}.")

    @editcoins.command(name="bank")
    async def edit_bank(self, ctx, targ=None, val=None):
        """Utility|Edits user's bank coins.|"""
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
        await self.bot.funx.save_bank(ctx.author.id, val)
        await ctx.send(f"I've edited {targ}'s bank coins to {val}.")

    @commands.guild_only()
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

    @top.command()
    async def xp(self, ctx):
        """Info|Shows the top 10 people with the most XP.|"""
        script = "select user_id, xp from amathy.stats"
        data = await self.bot.funx.fetch_many(script)
        top = dict()
        for elem in data:
            user_id, xp = elem
            top[user_id] = xp
        sorted_top = sorted(top, key=top.get, reverse=True)
        emb = Embed().make_emb("Global top - XP", "To get xp, use commands or vote for me ([here](https://tiny.cc/voteama)).")
        max_range = 10
        if len(sorted_top) < max_range:
            max_range = len(sorted_top)
        for index in range(0, max_range):
            user_id = sorted_top[index]
            xp = self.bot.funx.group_digit(top[user_id])
            if user_id == ctx.author.id:
                text = "Author position >>> No. {}: {} - {} XP <<<"
                emb.set_footer(text=text.format(index + 1, ctx.author.name, xp))
            user = self.bot.get_user(user_id)
            if user:
                emb.add_field(name="No. {}: {}".format(index + 1, user.name), value="{} XP".format(xp))
        await ctx.send(embed=emb)

    @top.command()
    async def votes(self, ctx):
        """Info|Shows the top 10 people with the most votes.|"""
        script = "select user_id, vote_num from amathy.votes"
        data = await self.bot.funx.fetch_many(script)
        top = dict()
        for elem in data:
            user_id, votes = elem
            top[user_id] = votes
        sorted_top = sorted(top, key=top.get, reverse=True)
        emb = Embed().make_emb("Global top - Votes", "To get listed, vote for me ([here](https://tiny.cc/voteama)).")
        max_range = 10
        if len(sorted_top) < max_range:
            max_range = len(sorted_top)
        for index in range(0, max_range):
            user_id = sorted_top[index]
            votes = self.bot.funx.group_digit(top[user_id])
            if user_id == ctx.author.id:
                text = "Author position >>> No. {}: {} - {} votes <<<"
                emb.set_footer(text=text.format(index + 1, ctx.author.name, votes))
            user = self.bot.get_user(user_id)
            if user:
                emb.add_field(name="No. {}: {}".format(index + 1, user.name), value="{} votes".format(votes))
        await ctx.send(embed=emb)

    @commands.command()
    @commands.guild_only()
    async def buy(self, ctx, item, quantity="1"):
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

    @commands.command(aliases=["bag"])
    async def inventory(self, ctx, targ=None):
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


def setup(bot):
    bot.add_cog(Economy(bot))
