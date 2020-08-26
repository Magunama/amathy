from discord.ext import commands
from utils.checks import AuthorCheck


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


def setup(bot):
    bot.add_cog(Creator(bot))
