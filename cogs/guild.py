import discord
from discord.ext import commands
from discord.ext import menus
from discord.ext.commands.cooldowns import BucketType
from utils.checks import FileCheck
from utils.embed import Embed
from utils.funx import BaseRequest
import random
import json


class RolePaginator(menus.ListPageSource):
    def __init__(self, entries, *, per_page=10):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, entries):
        curr_page = menu.current_page
        page_count = self.get_max_pages()
        rows = list()
        for index, role in enumerate(entries, 10 * curr_page + 1):
            rows.append(f"`{index}`. {role.mention} • {role.id}")
        embed = discord.Embed(title="Guild roles", description="\n".join(rows))
        embed.set_footer(text=f"Page {curr_page + 1}/{page_count}")
        return embed

    def is_paginating(self):
        return True


class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wrole_path = "data/welcome/roles.json"
        self.wmessage_path = "data/welcome/messages.json"
        self.welcome_roles, self.welcome_messages = self.load_welcome_files()

    def load_welcome_files(self):
        fchk = FileCheck()
        fchk.check_create_folder("data/welcome/")
        fchk.check_create_file(self.wrole_path, "{}")
        fchk.check_create_file(self.wmessage_path, "{}")

        # Welcome roles
        with open(self.wrole_path, 'r') as fp:
            welcome_roles = json.load(fp)
        # Welcome messages
        with open(self.wmessage_path, 'r') as fp:
            welcome_messages = json.load(fp)
        #############
        return welcome_roles, welcome_messages

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # await bot.wait_until_ready()
        if member.bot:
            return
        serv_obj = member.guild
        serv_str = str(serv_obj.id)
        if serv_str in self.welcome_messages:
            msg = self.welcome_messages[serv_str]
            basictext = "A welcome message has been set for you from the guild *{}*: \n{}".format(serv_obj, msg)
            await member.send(basictext)
        if serv_str in self.welcome_roles:
            roleobj = serv_obj.get_role(int(self.welcome_roles[serv_str]))
            basictext = "Welcome to **{0}**! You were given the following role: `{1}`".format(serv_obj.name, roleobj.name)
            await member.add_roles(roleobj)
            await member.send(basictext)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # await bot.wait_until_ready()
        if after.bot:
            return
        serv_obj = after.guild
        serv_str = str(serv_obj.id)
        if serv_str in self.welcome_roles:
            roleobj = serv_obj.get_role(int(self.welcome_roles[serv_str]))
            if roleobj is None or roleobj in before.roles:
                return
            try:
                await after.add_roles(roleobj)
            except discord.errors.Forbidden:
                pass

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.group(aliases=["guild"])
    async def server(self, ctx):
        """Utility|Shows server info/settings.|"""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @server.command(name="info")
    async def s_info(self, ctx):
        """Info|Returns some server information.|"""
        if not ctx.guild.chunked:
            await ctx.guild.chunk()

        embed = Embed().make_emb(title="Guild details:", desc="")
        embed.set_author(name="{} ({})".format(ctx.guild.name, ctx.guild.id))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Owner", value=ctx.guild.owner, inline=True)
        embed.add_field(name="Region", value=ctx.guild.region, inline=True)
        embed.add_field(name="Created at", value=str(ctx.guild.created_at).split('.', 1)[0], inline=True)

        members = ctx.guild.member_count
        bots = sum(m.bot for m in ctx.guild.members)
        widget_url = f"https://discordapp.com/api/guilds/{ctx.guild.id}/widget.json"
        widget_data = await BaseRequest().get_json(widget_url)
        online_members = widget_data.get("presence_count", "Unavailable")

        embed.add_field(name="Members", value=members, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        embed.add_field(name="Online members", value=online_members, inline=True)
        embed.add_field(name="Text channels", value=len(ctx.guild.text_channels), inline=True)
        embed.add_field(name="Voice channels", value=len(ctx.guild.voice_channels), inline=True)
        embed.add_field(name="Nitro boost level", value=ctx.guild.premium_tier, inline=True)
        embed.add_field(name="Members boosting this guild", value=ctx.guild.premium_subscription_count, inline=True)
        g_boost_stats = "```Emoji limit: {} emojis\nBitrate limit: {} kbps\nFilesize limit: {} MB```"
        g_boost_stats = g_boost_stats.format(
            ctx.guild.emoji_limit, int(ctx.guild.bitrate_limit / 1000), int(ctx.guild.filesize_limit / 1048576)
        )
        embed.add_field(name="Guild boost stats", value=g_boost_stats, inline=True)
        emoji_list = await ctx.guild.fetch_emojis()
        random.shuffle(emoji_list)
        emoji_string = ""
        for i in range(len(emoji_list)):
            emoji = emoji_list[i]
            if emoji.available:
                emoji = str(emoji)
                if len(emoji_string) + len(emoji) < 1024:
                    emoji_string += emoji
        if emoji_string:
            embed.add_field(name="Some emojis", value=emoji_string, inline=True)
        await ctx.send(embed=embed)

    @server.command(aliases=["roles"])
    async def roleids(self, ctx):
        """Utility|Returns a list of roles in the guild.|"""
        guild_roles = ctx.guild.roles
        guild_roles.reverse()
        source = RolePaginator(entries=guild_roles)
        menu = menus.MenuPages(source=source, timeout=None, delete_message_after=True)
        await menu.start(ctx)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group()
    async def welcome(self, ctx):
        """Utility|Welcome Role/Message|Administrator permission."""
        if ctx.invoked_subcommand is None:
            text = "Available actions:\n`a welcome role` to change the welcome role;\n`a welcome msg` to change the welcome message."
            await ctx.send(text)

    @welcome.command()
    async def role(self, ctx, roleid=None):
        """Utility|Set a welcome role (autorole).|"""
        # todo: search for role, check for position/perms
        serv_str = str(ctx.guild.id)
        autorole = "N/A"
        if serv_str in self.welcome_roles:
            autorole = ctx.guild.get_role(int(self.welcome_roles[serv_str]))
        if not roleid:
            rettext = "The current active welcome role: `{}` \nTo change the role, use `a welcome role [id]`. To disable the welcome role event, use `a welcome role disable`.\nTo find easier the role id, use `a server roles`."
            return await ctx.send(rettext.format(autorole))
        if roleid == "disable":
            if not serv_str in self.welcome_roles:
                return await ctx.send("There isn't any active welcome role.")
            del self.welcome_roles[serv_str]
            with open(self.wrole_path, 'w') as fp:
                json.dump(self.welcome_roles, fp, indent=4)
            return await ctx.send("I won't give a role to new members anymore.")
        elif len(roleid) == 18 and roleid.isdigit():
            role = ctx.guild.get_role(int(roleid))
            if role is None or str(role) == "@everyone":
                return await ctx.send("Something went wrong! Are you sure you gave me a valid id?")
            if role.managed:
                return await ctx.send("Sorry, I can't give that role to members since it's managed by an integration!")
            self.welcome_roles[serv_str] = roleid
            with open(self.wrole_path, 'w') as fp:
                json.dump(self.welcome_roles, fp, indent=4)
            return await ctx.send("I will now give the role `{}` to new members, {}!".format(role, ctx.author.name))

        else:
            await ctx.send("Something went wrong! Are you sure you gave me a valid id?")

    @welcome.command(aliases=["msg"])
    async def message(self, ctx, *, msg=None):
        """Utility|Set a welcome message.|"""
        serv_str = str(ctx.guild.id)
        joinmsg = "N/A"
        if serv_str in self.welcome_messages:
            joinmsg = self.welcome_messages[serv_str]
        if not msg:
            rettext = "The active welcome message: `{}` \nTo change it, use `a welcome msg [text]`. To disable the sending of the message, use `a welcome msg disable`."
            return await ctx.send(rettext.format(joinmsg))
        if msg == "disable":
            if not serv_str in self.welcome_messages:
                return await ctx.send("There isn't any active welcome message!")
            del self.welcome_messages[serv_str]
            with open(self.wmessage_path, 'w') as fp:
                json.dump(self.welcome_messages, fp, indent=4)
            return await ctx.send("I won't send a welcome message to new members anymore.")
        if len(msg) > 800:
            return await ctx.send("Your chosen message is too long! (800 characters)")
        self.welcome_messages[serv_str] = msg
        with open(self.wmessage_path, 'w') as fp:
            json.dump(self.welcome_messages, fp, indent=4)
        await ctx.send("I will now send the welcome message to new members, {}!".format(ctx.author.name))

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command()
    @commands.cooldown(1, 10, BucketType.guild)
    async def prefix(self, ctx, prefix=None):
        """Utility|Shows the prefix of the server or sets a new one|Administrator permission"""
        if not prefix:
            prefix = await self.bot.funx.get_prefix(ctx.guild.id)
            if not prefix:
                prefix = "/ ".join(self.bot.prefixes)
            return await ctx.send("The prefix of this server is `{}`".format(prefix))
        if len(prefix) > 3:
            return await ctx.send("The prefix cannot be longer than 3 characters!")
        await self.bot.funx.set_prefix(ctx.guild.id, prefix)
        await ctx.send("The prefix on this server is now `{}`".format(prefix))


def setup(bot):
    bot.add_cog(Server(bot))
