from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from utils.converters import MemberConverter
from asyncio import TimeoutError


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(3, 45, BucketType.user)
    @commands.command()
    async def purge(self, ctx, amount: int = None):
        """Utility|Deletes a number of messages.|Manage messages permission"""
        if not amount:
            text = "You have to enter the number of messages you want to delete."
            return await ctx.send(text)
        if amount >= 100:
            amount = 100
        await ctx.message.channel.purge(limit=amount)
        text = "I made {} messages to disappear. Am I magic or not? :eyes:"
        await ctx.send(text.format(amount), delete_after=3.0)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.command()
    async def kick(self, ctx, target: MemberConverter = None, *, reason=None):
        """Utility|Kicks a member.|Kick permission"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        if not target:
            text = "I don't know who you want me to kick!"
            return await ctx.send(text)
        if target == ctx.author:
            text = "You shouldn't kick yourself."
            return await ctx.send(text)
        if target.top_role > ctx.author.top_role:
            return await ctx.send("You shouldn't kick your superiors!")
        if target.top_role >= ctx.me.top_role:
            return await ctx.send(f"I can't kick {target} as their role is greater than/equal to my role.")

        if not reason:
            reason = "Unknown"
        text = f"Are you sure you want to kick **{target}**, for reason *{reason}*?\nIf yes, type `confirm`."
        await ctx.send(text)
        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=20)
        except TimeoutError:
            await ctx.send("I'll take this as a no...")
        else:
            if cf_mes.content.lower() != "confirm":
                text = "{} got away from the kick, *for now*."
                return await ctx.send(text.format(target))
            try:
                text = "You got kicked from {} by {} for reason **{}**."
                await target.send(text.format(ctx.guild, ctx.author, reason))
            except Exception as e:
                print(f"[ERROR][Moderation-Kick] {e}")
            try:
                await target.kick(reason=reason)
            except Exception as e:
                print(f"[ERROR][Moderation-Kick] {e}")
                text = "I didn't manage to kick {}, something went wrong!"
                return await ctx.send(text.format(target))
            text = "I kicked {}."
            await ctx.send(text.format(target))

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.command()
    async def ban(self, ctx, target: MemberConverter = None, *, reason=None):
        """Utility|Bans a member.|Ban permission"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        if not target:
            text = "I don't know who you want me to ban!"
            return await ctx.send(text)
        if target == ctx.author:
            text = "You shouldn't ban yourself."
            return await ctx.send(text)
        if target.top_role > ctx.author.top_role:
            return await ctx.send("You shouldn't ban your superiors!")
        if target.top_role >= ctx.me.top_role:
            return await ctx.send(f"I can't ban {target} as their role is greater than/equal to my role.")

        if not reason:
            reason = "Unknown"
        text = f"Are you sure you want to ban **{target}**, for reason *{reason}*?\nIf yes, type `confirm`."
        await ctx.send(text)
        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=20)
        except TimeoutError:
            await ctx.send("I'll take this as a no...")
        else:
            if cf_mes.content.lower() != "confirm":
                text = "{} got away from the ban, *for now*."
                return await ctx.send(text.format(target))
            try:
                text = "You got banned from {} by {} for reason **{}**."
                await target.send(text.format(ctx.guild, ctx.message.author, reason))
            except Exception as e:
                print(f"[ERROR][Moderation-Ban] {e}")
            try:
                await target.ban(reason=reason, delete_message_days=3)
            except Exception as e:
                print(f"[ERROR][Moderation-Ban] {e}")
                text = "I didn't manage to ban {}, something went wrong!"
                return await ctx.send(text.format(target))
            text = "I banned {}."
            await ctx.send(text.format(target))


def setup(bot):
    bot.add_cog(Moderation(bot))
