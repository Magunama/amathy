from discord.ext import commands
from utils.embed import Embed
import datetime
import random


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.mc_emoji = bot.get_emoji(bot.consts["mc_emoji_id"])

    @commands.guild_only()
    @commands.command(aliases=["dailymc"])
    async def daily(self, ctx):
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


def setup(bot):
    bot.add_cog(Economy(bot))
