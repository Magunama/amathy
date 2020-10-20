from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import discord
import psutil
import platform
from utils.embed import Embed
from utils.funx import BaseRequest
from utils.converters import MemberConverter
import random
import aiohttp
import time
import json
from utils.emojis import emojis
from utils.checks import AuthorCheck, FileCheck
import os


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]

    @staticmethod
    def get_size(bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    @commands.command()
    async def say(self, ctx, *, ret):
        """Fun|Repeats your input.|"""
        alm = discord.AllowedMentions(users=True, everyone=False, roles=False)
        await ctx.send(ret, allowed_mentions=alm)
        await ctx.message.delete()  # prone to exceptions

    @commands.command()
    async def ping(self, ctx):
        """Info|Marco! Polo!|"""
        ws = round(self.bot.latency * 1000, 3)
        first = time.perf_counter()
        msg = await ctx.send('__*`Pinging...`*__')
        second = time.perf_counter()
        resp = round((second - first) * 1000, 3)
        text = f":ping_pong: **Pong!**\nWebsocket latency: `{ws} ms`\nResponse time: `{resp} ms`"
        await msg.edit(content=text)

    @commands.command()
    async def vote(self, ctx):
        """Utility|Vote for me, darling!~|"""
        vote_link = "https://tiny.cc/voteama"
        emb_links_perm = ctx.channel.permissions_for(ctx.me).embed_links
        coins, xp = self.bot.base_vote_coins, self.bot.base_vote_xp

        rewards = "Today's rewards: Unknown :confused:"
        data = await BaseRequest.get_json("https://top.gg/api/weekend")
        if data:
            if data["is_weekend"]:
                coins, xp = coins * 2, xp * 2
            rewards = f"Today's rewards: {coins} coins & {xp} XP :money_mouth:"

        if not emb_links_perm:
            text = f"Vote for me here: {vote_link}\n{rewards}"
            return await ctx.send(text)
        emb = Embed().make_emb("Vote link", f"Vote for me and get rewards by clicking [here]({vote_link})!\n{rewards}")
        await ctx.send(embed=emb)

    @commands.command()
    async def invite(self, ctx):
        """Utility|Invite me to your guild!|"""
        emb_links_perm = ctx.channel.permissions_for(ctx.me).embed_links
        if not emb_links_perm:
            return await ctx.send(self.bot.invite_link)
        emb = Embed().make_emb("Invite link", f"Invite me to your guild by clicking [here]({self.bot.invite_link})!")
        await ctx.send(embed=emb)

    @commands.bot_has_permissions(embed_links=True)
    @commands.group()
    async def bot(self, ctx):
        """Info|Shows info/settings about the bot.|"""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @AuthorCheck.is_creator()
    @bot.command(aliases=["avatar"])
    async def setavatar(self, ctx, link=None):
        """Creator|Modifies Amathy's avatar.|Creator permission"""
        if not link:
            return await ctx.send("You must specify a link.")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as r:
                    img = await r.content.read()
            await self.bot.user.edit(avatar=img)
        except Exception as e:
            await ctx.send("The following went wrong!\n{}".format(e))
        else:
            await ctx.send("I've done everything you asked me to!")

    @bot.command(aliases=["stats"])
    async def info(self, ctx):
        """Info|Returns some information about the bot.|"""
        embed = discord.Embed(title="About Amathy")
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        creator_names = list()
        for uid in self.bot.owner_ids:
            user_obj = self.bot.get_user(uid)
            if not user_obj:
                user_obj = await self.bot.fetch_user(uid)
            creator_names.append(str(user_obj))
        creator_string = "```" + "\n".join(creator_names) + "```"
        embed.add_field(name="Creators", value=creator_string, inline=False)
        embed.add_field(name="Library", value=f"Discord.py {discord.__version__}", inline=True)

        timediff = int(time.time() - self.bot.funx.launch_time)
        uptime_str = self.bot.funx.seconds2string(timediff, "en")
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Guild count", value=str(len(self.bot.guilds)), inline=True)

        all_members = sum(g.member_count for g in self.bot.guilds)
        unique_members = len(self.bot.users)
        embed.add_field(name="Member count", value=f"{all_members} (all)\n{unique_members} (cached)", inline=True)

        if hasattr(self.bot, "wavelink"):
            active_players = 0
            paused_players = 0
            waiting_players = 0
            players = self.bot.wavelink.players
            for gid in players:
                player = players[gid]
                if player.is_playing:
                    if player.is_paused:
                        paused_players += 1
                    else:
                        active_players += 1
                if player.waiting:
                    waiting_players += 1
            music_stats = f"""
                ```Active players: {active_players}\nPaused players: {paused_players}\nWaiting players: {waiting_players}```
            """
            embed.add_field(name="Music stats", value=music_stats, inline=True)
        else:
            embed.add_field(name="Music stats", value="Unavailable", inline=True)

        website = "https://amathy.moe"
        supp_server = "https://discord.gg/D87ykxd"
        vote = "https://discordbots.org/bot/410488336344547338/vote"
        invite = self.bot.invite_link
        links = f"\n[Website!]({website}) ✤ [Support server!]({supp_server}) ✤ [Vote for me & get rewards!]({vote}) ✤ [Invite me!]({invite})\n"
        embed.add_field(name="Links", value=links, inline=False)
        embed.set_footer(text="© 2018-2020 - Copyright: AnimeVibe - Project Amathy")
        await ctx.send(embed=embed)

    @commands.command(aliases=["dadjoke"])
    async def joke(self, ctx):
        """Fun|Sends a Dad Joke!|"""
        headers = {"Accept": "application/json"}
        async with aiohttp.ClientSession()as session:
            async with session.get("https://icanhazdadjoke.com", headers=headers) as get:
                assert isinstance(get, aiohttp.ClientResponse)
                resp = await get.json()
            await session.close()
        await ctx.send(resp["joke"])

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.command(aliases=["av"])
    async def avatar(self, ctx, *, target: MemberConverter = None):
        """Info|Returns a user's avatar.|"""
        if not target:
            target = ctx.author
        avatartext = "**👉 |** ***{} - avatar.***".format(target.name)
        emb = Embed().make_emb("", avatartext)
        emb.set_image(url=target.avatar_url)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.command(aliases=["rr", "reactionrole"])
    async def reactrole(self, ctx, op=None):
        """Utility|Reaction -> Role System.|"""
        # todo: optimization
        if not ctx.message.author.guild_permissions.administrator:
            return await ctx.send("Sorry but only someone with the Administration permission may use this command.")
        if not op:
            return await ctx.send("Here are the available operations:\n`rr add`, `rr list`, `rr del`, `rr log`.")
        if not op in ["add", "list", "del"]:
            return await ctx.send("Here are the availalbe operations:\n`rr add`, `rr list`, `rr del`, `rr log`.")
        await ctx.message.delete()
        if op == "add":
            global mid
            mid = "<?> (Not known yet)"

            def make_emb(desc, options):
                embed = discord.Embed(title="[Amathy v1.8] - ReactRole entry with id `{}`".format(mid), description=desc)
                for i in range(0, len(options)):
                    emoji, role = options[i]
                    embed.add_field(name="Option {}:".format(i + 1), value="{} -> {}".format(emoji, role), inline=True)
                embed.set_footer(text="ReactRole system v0.9. - https://patreon.com/amathy")
                return embed

            def check(m):
                return m.author.id == ctx.author.id and m.channel == ctx.channel

            desc = "This is a description"
            options = []
            prev = await ctx.send(embed=make_emb(desc, options))
            mid = "<{}>".format(prev.id)
            try:
                first = await ctx.send("Note that this is a preview. Please enter a description for your new ReactRole.")
                cf_mes = await self.bot.wait_for("message", check=check, timeout=45)
                if cf_mes:
                    await first.delete()
                    desc = cf_mes.content
                    await cf_mes.delete()
                    await prev.edit(embed=make_emb(desc, options))
                    await ctx.send(
                        "Now it's time for you to add some options (10 max). Note that Amathy will not be able to give a member a role positioned higher than hers.",
                        delete_after=10)
                    selected = 0
                    sel_text = "Select what you want to do.\n    Press `1` to pick an option.\n    Press `2` to delete an option.\n    Press `3` to finish setting up the reaction role."
                    expected = [emojis["one"], emojis["two"], emojis["three"]]

                    def emoji_check(react, user):
                        return user.id == ctx.author.id and str(react.emoji) in expected

                    while True:
                        third = await ctx.send(sel_text)
                        for k in expected:
                            await third.add_reaction(k)
                        react, user = await self.bot.wait_for('reaction_add', check=emoji_check, timeout=30)
                        if react is None or user is None:
                            await third.delete()
                            raise Exception
                        await third.delete()
                        if react.emoji == expected[0]:  # :one:
                            if selected == 10:
                                await ctx.send("Sorry, you cannot add more options.", delete_after=5)
                                continue
                            fourth = await ctx.send("To add an option, follow the model: `<emoji> <role_name>/<role_id>/<role_mention>`.")
                            cf_mes = await self.bot.wait_for("message", check=check, timeout=30)
                            if not cf_mes:
                                raise Exception
                            if not " " in cf_mes.content:
                                raise Exception
                            await fourth.delete()
                            emoji, role = cf_mes.content.split(" ", 1)
                            role_obj = None
                            if len(role) == 18 and role.isdigit():
                                role_obj = ctx.guild.get_role(int(role))
                            if not role_obj:
                                if "@" in role:
                                    role = role.replace("<@&", "").replace(">", "")
                                    role_obj = ctx.guild.get_role(int(role))
                                else:
                                    role_obj = discord.utils.get(ctx.guild.roles, name=role)
                                if not role_obj:
                                    raise Exception("No role object found.")
                            await cf_mes.delete()
                            selected += 1
                            options.append([emoji, role_obj.mention])
                            await prev.edit(embed=make_emb(desc, options))
                        elif react.emoji == expected[1]:  # :two:
                            if selected == 0:
                                await ctx.send("Sorry, you cannot delete more options.", delete_after=5)
                                continue
                            fourth = await ctx.send("Type the number of the entry you want to delete. (1-10)")
                            cf_mes = await self.bot.wait_for("message", check=check, timeout=10)
                            if not cf_mes:
                                await cf_mes.delete()
                                raise Exception("No confirm message!")
                            if not cf_mes.content.isdigit():
                                await cf_mes.delete()
                                raise Exception("Confirm message doesn't contain a digit!")
                            index = int(cf_mes.content)
                            await cf_mes.delete()
                            if index > 10 or index < 1:
                                raise Exception("Confirm message doesn't follow the model!")
                            if index > len(options):
                                raise Exception("Options index ouf of range!")
                            del options[index - 1]
                            selected -= 1
                            await fourth.delete()
                            await prev.edit(embed=make_emb(desc, options))
                        else:
                            break

                    cf = await ctx.send("If everything looks alright, press the check mark below.")
                    await cf.add_reaction("\u2705")

                    def emoji_check(react, user):
                        return user.id == ctx.author.id and str(react.emoji) == "\u2705"

                    react, user = await self.bot.wait_for('reaction_add', check=emoji_check, timeout=10)
                    if react is None or user is None:
                        await cf.delete()
                        raise Exception("No reaction!")
                    await cf.delete()
            except Exception as e:
                print(e)
                return await ctx.send("Some error occured because of your input. Please try again!")
            for i in range(0, len(options)):
                react = options[i][0]
                await prev.add_reaction(react)
            folder = "data/reactrole/{}".format(ctx.guild.id)
            path = "{}/reactrole.json".format(folder)
            if not os.path.exists(folder):
                os.makedirs(folder)
            if not os.path.isfile(path):
                with open(path, 'w') as fp:
                    json.dump({}, fp, sort_keys=True, indent=4)
                reactrole = {}
            else:
                with open(path, 'r') as fp:
                    reactrole = json.load(fp)
            reactrole[str(prev.id)] = {"desc": desc, "opt": options}
            with open(path, 'w') as fp:
                json.dump(reactrole, fp, sort_keys=True, indent=4)
            await ctx.send("ReactRole with entry id `{}` was successfully saved! :smile:".format(prev.id))
        elif op == "del":
            def check(m):
                return m.author.id == ctx.author.id and m.channel == ctx.channel

            try:
                fourth = await ctx.send("Type the id of the ReactRole entry you want to delete. To list all entries, use `a rr list`.")
                cf_mes = await self.bot.wait_for("message", check=check, timeout=10)
                if not cf_mes:
                    await cf_mes.delete()
                    raise Exception("No confirm message!")
                if not cf_mes.content.isdigit():
                    await cf_mes.delete()
                    raise Exception("Confirm message doesn't contain a digit!")
                index = cf_mes.content
                await cf_mes.delete()
                await fourth.delete()
                folder = "data/reactrole/{}".format(ctx.guild.id)
                path = "{}/reactrole.json".format(folder)
                if not os.path.exists(folder):
                    os.makedirs(folder)
                if not os.path.isfile(path):
                    with open(path, 'w') as fp:
                        json.dump({}, fp, sort_keys=True, indent=4)
                    reactrole = {}
                else:
                    with open(path, 'r') as fp:
                        reactrole = json.load(fp)
                if index in reactrole:
                    del reactrole[index]
                    await ctx.send("ReactRole with entry id `{}` was successfully deleted! :smile:".format(index))
                else:
                    await ctx.send("Selected index was not found!")
            except Exception as e:
                print(e)
                return await ctx.send("Some error occured because of your input. Please try again!")
        elif op == "list":
            folder = "data/reactrole/{}".format(ctx.guild.id)
            path = "{}/reactrole.json".format(folder)
            if not os.path.isfile(path):
                reactrole = {}
            else:
                with open(path, 'r') as fp:
                    reactrole = json.load(fp)
            embeds = []
            if reactrole:
                def make_emb(desc, options, page, total, mid):
                    embed = discord.Embed(title="[Amathy v1.8] - ReactRole entry with id `{}`".format(mid), description=desc)
                    for i in range(0, len(options)):
                        emoji, role = options[i]
                        embed.add_field(name="Option {}:".format(i + 1), value="{} -> {}".format(emoji, role),
                                        inline=True)
                    embed.set_footer(text="Page {}/{} - ReactRole system v0.9. - https://patreon.com/amathy".format(page, total))
                    return embed

                total = len(reactrole)
                page = 0
                for k in reactrole:
                    mid = k
                    page += 1
                    l = reactrole[k]
                    desc = l["desc"]
                    options = l["opt"]
                    embeds.append(make_emb(desc, options, page, total, mid))
            if embeds:
                await self.bot.funx.embed_menu(ctx, emb_list=embeds)
            else:
                await ctx.send("The list of ReactRoles is empty. Add one with `a rr add`.")

    @commands.guild_only()
    @commands.command()
    async def vip(self, ctx, target: MemberConverter = None):
        """Info|Checks user's VIP status.|"""
        if not target:
            target = ctx.author
        active = "No"
        targ_id = target.id
        vip_days = await self.bot.funx.get_vip_days(targ_id)
        if vip_days > 0:
            active = "Yes"
        embed = discord.Embed(
            title="VIP status check for {}".format(target),
            color=0x992d22,
            description="",
        )
        embed.add_field(
            name="Active",
            value=active)
        embed.add_field(
            name="Days remaining",
            value=vip_days)
        utc_diff_sign = lambda a: f"+{a}" if a > 0 else a
        embed.set_footer(text=f"[Notice] VIP days go down every day after 12 PM (UTC{utc_diff_sign(self.utc_diff)}).")
        await ctx.send(embed=embed)

    @commands.bot_has_permissions(attach_files=True)
    @commands.command()
    async def flip(self, ctx):
        async def dwn_img(source, savepath):
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as resp:
                    if resp.status == 200:
                        resp = await resp.read()
                        with open(savepath, "wb") as fp:
                            fp.write(resp)
        fchk = FileCheck()
        fchk.check_create_folder("data/flip")
        head_file = fchk.check_file("data/flip/heads.png")
        if not head_file:
            await dwn_img("https://i.imgur.com/sq6ZDOx.png", "data/flip/heads.png")
        tail_file = fchk.check_file("data/flip/tails.png")
        if not tail_file:
            await dwn_img("https://i.imgur.com/N5ixRZI.png", "data/flip/tails.png")
        pick = random.choice([("data/flip/heads.png", "Heads!"), ("data/flip/tails.png", "Tails!")])
        link = pick[0]
        text = pick[1]
        files = [discord.File(link, 'coin.png')]
        await ctx.send(text, files=files)

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, BucketType.user)
    @commands.command(aliases=["sys"])
    async def system(self, ctx):
        """Info|Shows system resources.|"""
        fields = []

        # System information
        uname = platform.uname()
        fields.append(["System", uname.system, True])
        fields.append(["Version", uname.version, True])

        # CPU Info
        fields.append(["Physical cores:", psutil.cpu_count(logical=False), True])
        # CPU frequencies
        cpufreq = psutil.cpu_freq()
        fields.append(["Frequency:", f"{cpufreq.current:.2f}Mhz", True])
        # CPU usage
        fields.append(["CPU usage:", f"{psutil.cpu_percent()}%", True])

        # Memory Information
        svmem = psutil.virtual_memory()
        fields.append(["Total memory", self.get_size(svmem.total), True])
        fields.append(["Available memory", self.get_size(svmem.available), True])
        fields.append(["Used memory", self.get_size(svmem.used), True])
        fields.append(["Memory percentage", f"{svmem.percent}%", True])

        # My processes
        ret = 0
        for proc in psutil.process_iter():
            if proc.name() in ["python3", "python3.exe", "java", "java.exe", "postgres"]:
                ret = ret + proc.memory_info().rss
        footer = f"Amathy's memory consumption:  {self.get_size(ret)}"

        title = ctx.command.qualified_name
        author = {"name": ctx.bot.user.name, "icon_url": ctx.bot.user.avatar_url}
        desc = "Here are some details about system resources."
        await ctx.send(embed=Embed().make_emb(title, desc, author, fields, footer))


def setup(bot):
    bot.add_cog(Main(bot))
