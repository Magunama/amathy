from discord.ext import commands
from utils.embed import Embed
import datetime
import random
import asyncio
import discord


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.mc_emoji = bot.get_emoji(bot.consts["mc_emoji_id"])

    @commands.guild_only()
    @commands.command(aliases=["dailymc"])
    async def daily(self, ctx):
        """Fun|Get your daily coins!|"""
        prev_coins = (await self.bot.funx.get_coins(ctx.author.id))[0]
        prev_time = (await self.bot.funx.get_timer(ctx.author.id, "daily"))[0]
        expected_time = prev_time + datetime.timedelta(days=1)  # cooldown
        expected_time = expected_time.replace(hour=0, minute=0, second=0)  # because cooldown should not be constant
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        if time_now >= expected_time:
            # todo: add xp multiplier
            pick = random.randint(50, 200)
            after_coins = prev_coins + pick
            await self.bot.funx.save_pocket(ctx.author.id, after_coins)
            await self.bot.funx.save_timer(ctx.author.id, "daily", time_now)
            text = ["**:moneybag: | You have received {0} {3}, {1}. I see you're kinda lucky. :) You now have {2} {3}.**",
                    "**:moneybag: | You have received {0} {3}, {1}. How'd you do that? :) You now have {2} {3}.**",
                    "**:moneybag: | You have received {0} {3}, {1}. Have you eaten something special today? :) You now have {2} {3}.**"]
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
            return await ctx.send(text.format(self.mc_emoji))
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
            return await ctx.send(text.format(self.mc_emoji))
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
            return await ctx.send(text.format(self.mc_emoji))
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


def setup(bot):
    bot.add_cog(Economy(bot))
