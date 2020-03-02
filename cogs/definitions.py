from discord.ext import commands
import datetime
import asyncpg


class Definitions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.date_format = bot.consts["date_format"]

    async def get_short_local_def(self, def_name, guild_id):
        script = f"select def_body from amathy.local_def where def_name='{def_name}' and guild_id='{guild_id}'"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        data = data["def_body"]
        return f"`[L]` {data}"

    async def get_long_local_def(self, def_name, guild_id):
        script = f"select def_body, def_time, author_id from amathy.local_def where def_name='{def_name}' and guild_id='{guild_id}'"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        def_body, def_time, author_id = data
        author_obj = self.bot.get_user(int(author_id))
        if not author_obj:
            author_obj = author_id
        return f"**[Local DEF]**: `{def_name}` was defined as `{def_body}` by {author_obj} on {def_time}. :smile:"

    async def save_local_def(self, def_name, def_body, author_id, guild_id):
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        time_now = time_now.strftime(self.date_format)
        script = f"insert into amathy.local_def values ('{def_name}', '{def_body}', '{time_now}', {author_id}, {guild_id})"
        try:
            await self.bot.funx.execute(script)
        except asyncpg.exceptions.UniqueViolationError:
            return f"Sorry, local definition `{def_name}` already exists!"
        return f"Saved local definition `{def_name}`."

    async def get_short_global_def(self, def_name):
        script = f"select def_body from amathy.global_def where def_name='{def_name}'"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        data = data["def_body"]
        return f"`[G]` {data}"

    async def get_long_global_def(self, def_name):
        script = f"select def_body, def_time, author_id from amathy.global_def where def_name='{def_name}'"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        def_body, def_time, author_id = data
        author_obj = self.bot.get_user(int(author_id))
        if not author_obj:
            author_obj = author_id
        return f"**[Global DEF]**: `{def_name}` was defined as `{def_body}` by {author_obj} on {def_time}. :smile:"

    async def save_global_def(self, def_name, def_body, author_id):
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        time_now = time_now.strftime(self.date_format)
        script = f"insert into amathy.global_def values ('{def_name}', '{def_body}', '{time_now}', {author_id})"
        try:
            await self.bot.funx.execute(script)
        except asyncpg.exceptions.UniqueViolationError:
            return f"Sorry, global definition `{def_name}` already exists!"
        return f"Saved global definition `{def_name}`."

    @commands.Cog.listener()
    async def on_message(self, message):
        # todo: add cooldown?
        mesc = message.content.lower()
        if 0 < len(mesc) <= 20:
            chan = message.channel
            global_def = await self.get_short_global_def(mesc)
            if global_def:
                await chan.send(global_def)
                local_def = await self.get_short_local_def(mesc, message.guild.id)
                if local_def:
                    await chan.send(local_def)
            else:
                local_def = await self.get_short_local_def(mesc, message.guild.id)
                if local_def:
                    await chan.send(local_def)

    @commands.command(aliases=["def"])
    async def define(self, ctx, def_name=None):
        """Fun|Get information about a definition.|"""
        if not def_name:
            text = "You must enter the name of a definition!"
            return await ctx.send(text)
        global_def = await self.get_long_global_def(def_name)
        if global_def:
            await ctx.send(global_def)
            local_def = await self.get_long_local_def(def_name, ctx.guild.id)
            if local_def:
                await ctx.send(local_def)
        else:
            local_def = await self.get_long_local_def(def_name, ctx.guild.id)
            if local_def:
                await ctx.send(local_def)
            else:
                text = f"No definition found for `{def_name}`. :slight_frown:"
                await ctx.send(text)

    @commands.command(aliases=["dset"])
    async def defset(self, ctx, def_string=None):
        """Fun|Add a local/global definition, depending on your VIP status.|"""
        # todo: limit def creation by level
        text = "You need to use `::` to separate the definition name from the definition body.\nExample: `a defset gn::Good night!`"
        if not def_string:
            return await ctx.send(text)
        if not "::" in def_string:
            return await ctx.send(text)
        def_name, def_body = def_string.split("::")
        if not 0 < len(def_name) <= 20:
            text = "The definition name must have between 1 and 20 characters!"
            return await ctx.send(text)
        if not 0 < len(def_body):
            text = "The definition body must not be empty!"
            return await ctx.send(text)
        vip_days = await self.bot.funx.get_vip_days(ctx.author.id)
        if vip_days:
            ret = await self.save_global_def(def_name, def_body, ctx.author.id)
        else:
            ret = await self.save_local_def(def_name, def_body, ctx.author.id, ctx.guild.id)
        await ctx.send(ret)


def setup(bot):
    bot.add_cog(Definitions(bot))
