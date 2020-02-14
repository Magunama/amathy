from discord.ext import commands


class HakunaMatata(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["h"])
    async def hakuna(self, ctx):
        """Hakuna Matata command."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Hakuna!")

    @hakuna.command(aliases=["m"])
    async def matata(self, ctx):
        """Hakuna Matata subcommand."""
        await ctx.send("Hakuna Matata!")


def setup(bot):
    bot.add_cog(HakunaMatata(bot))
