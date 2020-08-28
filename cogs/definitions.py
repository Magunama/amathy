from discord.ext import commands
from utils.embed import Embed
from utils.converters import MemberConverter
import datetime
import asyncpg
import random
import asyncio


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
        script = f"select def_body from amathy.definitions where def_name=($1) and (def_global=true or def_guild_id={guild_id})"
        data = await self.bot.funx.fetch_one(script, def_name)
        if not data:
            return None
        data = data["def_body"]
        return f":bookmark: | {data}"

    async def get_long_def(self, def_name):
        script = f"select def_body, def_guild_id, def_author_id, def_time, def_global from amathy.definitions where def_name=($1)"
        data = await self.bot.funx.fetch_one(script, def_name)
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

    async def get_defs_by_author(self, def_author):
        def_author_id = def_author.id
        script = f"select def_name, def_global from amathy.definitions where def_author_id={def_author_id}"
        data = await self.bot.funx.fetch_many(script)
        if not data:
            return None
        showlen = len(data)
        if showlen % 10 == 0:
            lastpage = int(showlen / 10)
        else:
            lastpage = int(showlen / 10) + 1
        embeds = list()
        title = f"{def_author.name}'s list of definitions [{showlen}]"
        desc = f"Here are {def_author.name}'s definitions:"
        for i in range(1, lastpage + 1):
            fields = []
            for j in range((i - 1) * 10, (i * 10) - 1):
                if not j < showlen:
                    break
                def_status = "• local"
                if data[j]["def_global"]:
                    def_status = "• global"
                fields.append([data[j]["def_name"], def_status, True])
            footer = "{}/{} - To see a definition, use ama define [definition].".format(i, lastpage)
            embed = Embed().make_emb(title, desc, None, fields, footer)
            embeds.append(embed)
        return embeds

    async def save_def(self, def_name, def_body, def_guild_id, def_author_id, def_global):
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        def_time = time_now.strftime(self.date_format)
        script = f"insert into amathy.definitions values (default, ($1), ($2), {def_guild_id}, {def_author_id}, '{def_time}', {def_global})"
        try:
            await self.bot.funx.execute(script, def_name, def_body)
        except asyncpg.exceptions.UniqueViolationError:
            return f"Sorry, definition `{def_name}` already exists!"
        except Exception as e:
            print(e)
            return "Sorry, something went wrong!"
        return f"Saved definition `{def_name}`."

    async def delete_def(self, def_name):
        script = f"delete from amathy.definitions where def_name=($1)"
        try:
            await self.bot.funx.execute(script, def_name)
        except Exception as e:
            print(e)
            return "Sorry, something went wrong!"
        return f"Deleted `{def_name}`."

    async def get_random_def(self):
        script = "select * from amathy.definitions"
        data = await self.bot.funx.fetch_many(script)
        if not data:
            return f"Couldn't find a definition. Try again, maybe?"
        data = random.choice(data)
        def_name = data["def_name"]
        return await self.get_formatted_def(def_name, data)

    @commands.Cog.listener("on_message")
    async def send_def(self, message):
        # todo: add cooldown?
        mesc = message.content.lower()
        if 0 < len(mesc) <= 25:
            chan = message.channel
            if hasattr(chan, "guild"):
                def_found = await self.get_short_def(mesc, chan.guild.id)
                if def_found:
                    await chan.send(def_found)

    @commands.command(aliases=["def"])
    async def define(self, ctx, def_name=None):
        """Fun|Get information about a definition.|"""
        if not def_name:
            text = "You must enter the name of a definition!"
            return await ctx.send(text)
        def_name = def_name.lower()
        def_found = await self.get_long_def(def_name)
        if def_found:
            def_text = await self.get_formatted_def(def_name, def_found)
            await ctx.send(def_text)
        else:
            text = f"No definition found for `{def_name}`. :slight_frown:"
            await ctx.send(text)

    @commands.guild_only()
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
        def_name = def_name.lower()
        if not 0 < len(def_name) <= 25:
            text = "The definition name must have between 1 and 25 characters!"
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

    @commands.guild_only()
    @commands.command(aliases=["ddel"])
    async def defdel(self, ctx, def_name=None):
        """Fun|Remove a definition.|"""
        if not def_name:
            text = "Enter the name of the definition you want to delete."
            return await ctx.send(text)
        if not 0 < len(def_name) <= 25:
            text = "The definition name must have between 1 and 20 characters!"
            return await ctx.send(text)

        def_name = def_name.lower()
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

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    @commands.command(aliases=["dlist"])
    async def deflist(self, ctx, target: MemberConverter = None):
        """Fun|Read someone's definitions.|"""
        if not target:
            text = "**You need to give me a member.**"
            return await ctx.send(text)
        embeds = await self.get_defs_by_author(target)
        if not embeds:
            return await ctx.send(f"No definitions found for user {target.name}.")
        await self.bot.funx.embed_menu(ctx, embeds)

    @commands.command(aliases=["rdef"])
    async def randef(self, ctx):
        """Fun|Get a random definition.|"""
        choice = await self.get_random_def()
        await ctx.send(choice)


def setup(bot):
    bot.add_cog(Definitions(bot))
