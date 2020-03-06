from discord.ext import commands
import datetime
import asyncpg
import random
import asyncio
import json


class Definitions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.date_format = bot.consts["date_format"]

    @staticmethod
    def can_delete_def(definition, user):
        author_id = definition["def_author_id"]
        if user.id == author_id:
            return True, "can be deleted by you because you are the author."
        if user.guild_permissions.administrator:
            return True, "can be deleted by you because you are an Administrator."
        return False, "cannot be deleted by you."

    async def get_short_def(self, def_name, guild_id):
        script = f"select def_body from amathy.definitions where def_name='{def_name}' and (def_global=true or def_guild_id={guild_id})"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        data = data["def_body"]
        return f":bookmark: | {data}"

    async def get_long_def(self, def_name):
        script = f"select def_body, def_guild_id, def_author_id, def_time, def_global from amathy.definitions where def_name='{def_name}'"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        return data

    async def get_formatted_def(self, def_name, definition):
        # todo global check
        def_body = definition["def_body"]
        def_guild_id = definition["def_guild_id"]
        def_author_id = definition["def_author_id"]
        def_time = definition["def_time"]
        def_global = definition["def_global"]
        author_obj = self.bot.get_user(def_author_id)
        if not author_obj:
            author_obj = def_author_id
        return f"**[DEF]**: `{def_name}` was defined as `{def_body}` by {author_obj} on {def_time}. :smile:"

    async def save_def(self, def_name, def_body, def_guild_id, def_author_id, def_global):
        # todo: parse
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        def_time = time_now.strftime(self.date_format)
        # def_name = json.dumps(def_name)
        # def_body = json.dumps(def_body)
        script = f"insert into amathy.definitions values (default, '{def_name}', '{def_body}', {def_guild_id}, {def_author_id}, '{def_time}', {def_global})"
        try:
            await self.bot.funx.execute(script)
        except asyncpg.exceptions.UniqueViolationError:
            return f"Sorry, definition `{def_name}` already exists!"
        return f"Saved definition `{def_name}`."

    async def delete_def(self, def_name):
        script = f"delete from amathy.definitions where def_name='{def_name}'"
        try:
            await self.bot.funx.execute(script)
        except Exception as e:
            print(e)
        return f"Deleted `{def_name}`."

    async def get_random_def(self):
        script = "select * from amathy.definitions"
        data = await self.bot.funx.fetch_many(script)
        if not data:
            return f"Couldn't find a definition. Try again, maybe?"
        data = random.choice(data)
        def_name = data["def_name"]
        return await self.get_formatted_def(def_name, data)

    @commands.Cog.listener()
    async def on_message(self, message):
        # todo: add cooldown?
        mesc = message.content.lower()
        if 0 < len(mesc) <= 20:
            chan = message.channel
            def_found = await self.get_short_def(mesc, message.guild.id)
            if def_found:
                await chan.send(def_found)

    @commands.command(aliases=["def"])
    async def define(self, ctx, def_name=None):
        """Fun|Get information about a definition.|"""
        if not def_name:
            text = "You must enter the name of a definition!"
            return await ctx.send(text)
        def_found = await self.get_long_def(def_name)
        if def_found:
            def_text = await self.get_formatted_def(def_name, def_found)
            await ctx.send(def_text)
        else:
            text = f"No definition found for `{def_name}`. :slight_frown:"
            await ctx.send(text)

    @commands.command(aliases=["dset"])
    async def defset(self, ctx, def_string=None):
        """Fun|Add a local/global definition, depending on your VIP status.|"""
        # todo: limit def creation by level
        text = "Use `::` to separate the definition name from the definition body.\nExample: `a defset gn::Good night!`"
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

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        text = f"Your choice for a definition is `{def_name}`: `{def_body}`.\nPick:\n• `1` or `local` for a local definition;\n• `2` or `global` for a global definition."
        await ctx.send(text)
        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("No response. Try again?")
        else:
            if cf_mes:
                cf_mes = cf_mes.content.lower()
                if cf_mes in ["1", "local"]:
                    ret = await self.save_def(def_name, def_body, ctx.guild.id, ctx.author.id, "false")
                elif cf_mes in ["2", "global"]:
                    vip_days = await self.bot.funx.get_vip_days(ctx.author.id)
                    if vip_days:
                        ret = await self.save_def(def_name, def_body, ctx.guild.id, ctx.author.id, "true")
                    else:
                        ret = "You don't have any VIP days left! Aquire some or try a local definition?"
                else:
                    ret = "Unknown definition type! Try again?"
                await ctx.send(ret)

    @commands.command(aliases=["ddel"])
    async def defdel(self, ctx, def_name=None):
        """Fun|Remove a definition.|"""
        if not def_name:
            text = "Enter the name of the definition you want to delete."
            return await ctx.send(text)
        if not 0 < len(def_name) <= 20:
            text = "The definition name must have between 1 and 20 characters!"
            return await ctx.send(text)

        def_found = await self.get_long_def(def_name)
        if not def_found:
            text = f"No definition found for `{def_name}`."
            return await ctx.send(text)
        def_body = def_found["def_body"]
        can_delete = self.can_delete_def(def_found, ctx.author)
        def_str = f"`{def_body}`, {can_delete[1]}"
        text = f"Found a definition for `{def_name}`:\n• {def_str}"
        if can_delete[0]:
            text += "\nType `delete` to confirm you want to delete it."
        await ctx.send(text)

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.message.channel

        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("No response. Try again?")
        else:
            if cf_mes:
                cf_mes = cf_mes.content.lower()
                if cf_mes == "delete":
                    ret = await self.delete_def(def_name)
                else:
                    ret = "Invalid confirmation! Try again?"
                await ctx.send(ret)

    @commands.command(aliases=["rdef"])
    async def randef(self, ctx):
        """Fun|Get a random definition.|"""
        choice = await self.get_random_def()
        await ctx.send(choice)


def setup(bot):
    bot.add_cog(Definitions(bot))
