from discord.ext import commands
from utils.checks import AuthorCheck
import random


class Creator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @AuthorCheck.is_creator()
    @commands.group()
    async def reset(self, ctx):
        """Creator|Reset command.|Creator permission"""
        if ctx.invoked_subcommand is None:
            await ctx.send("If you don't know how to use this, then you should not be using this!")

    @reset.command()
    async def votes(self, ctx):
        """Creator|Resets monthly top.gg vote count.|Creator permission"""
        script = "update amathy.votes set monthly_votes = 0;"
        await self.bot.funx.execute(script)
        await ctx.send("Monthly vote count has been reset.")

    @AuthorCheck.is_creator()
    @commands.group(aliases=["module"])
    async def cog(self, ctx):
        """Creator|Operate on modules.|Creator permission"""
        pass

    @cog.command()
    async def load(self, ctx, cog_name):
        """Creator|Load a module.|Creator permission"""
        self.bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"Loaded {cog_name}.")

    @cog.command()
    async def unload(self, ctx, cog_name):
        """Creator|Unload a module.|Creator permission"""
        self.bot.unload_extension(f"cogs.{cog_name}")
        await ctx.send(f"Unloaded {cog_name}.")

    @cog.command()
    async def reload(self, ctx, cog_name):
        """Creator|Reload a module.|Creator permission"""
        self.bot.unload_extension(f"cogs.{cog_name}")
        self.bot.load_extension(f"cogs.{cog_name}")
        await ctx.send(f"Reloaded {cog_name}.")

    @AuthorCheck.is_creator()
    @commands.command()
    async def rinv(self, ctx):
        """Creator|Return a random invite link.|Creator permission"""
        k = 0
        while True:
            r_guild = random.choice(ctx.bot.guilds)
            try:
                r_guild_inv_list = await r_guild.invites()
            except Exception as e:
                print(e)
                k += 1
                if k == 5:
                    return await ctx.send("Missing permission in 5 consecutive guilds.")
            else:
                if len(r_guild_inv_list) > 0:
                    inv = random.choice(r_guild_inv_list)
                    return await ctx.send(inv.url, delete_after=8.0)


def setup(bot):
    bot.add_cog(Creator(bot))
