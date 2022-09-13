import platform
import time
from typing import Optional, Literal, List

import discord
import psutil
import wavelink
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Greedy

from cogs.slash.music import MPlayer
from utils.embed import Embed
from utils.funx import BaseRequest


class Bot(app_commands.Group):
    """Bot."""

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

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

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        """Info|Marco! Polo!|"""
        ws = round(self.bot.latency * 1000, 3)
        first = time.perf_counter()
        await interaction.response.send_message(content='__*`Pinging...`*__')
        second = time.perf_counter()
        resp = round((second - first) * 1000, 3)
        text = f":ping_pong: **Pong!**\nWebsocket latency: `{ws} ms`\nResponse time: `{resp} ms`"
        await interaction.edit_original_response(content=text)

    @app_commands.command()
    async def vote(self, interaction: discord.Interaction):
        """Utility|Vote for me, darling!~|"""
        vote_link = "https://tiny.cc/voteama"
        emb_links_perm = interaction.channel.permissions_for(interaction.guild.me).embed_links
        coins, xp = self.bot.base_vote_coins, self.bot.base_vote_xp

        rewards = "Today's rewards: Unknown :confused:"
        data = await BaseRequest.get_json("https://top.gg/api/weekend")
        if data:
            if data["is_weekend"]:
                coins, xp = coins * 2, xp * 2
            rewards = f"Today's rewards: {coins} coins & {xp} XP :money_mouth:"

        if not emb_links_perm:
            text = f"Vote for me here: {vote_link}\n{rewards}"
            return await interaction.response.send_message(text)
        emb = Embed().make_emb("Vote link", f"Vote for me and get rewards by clicking [here]({vote_link})!\n{rewards}")
        await interaction.response.send_message(embed=emb)

    @app_commands.command()
    async def invite(self, interaction: discord.Interaction):
        """Utility|Invite me to your guild!|"""
        emb_links_perm = interaction.channel.permissions_for(interaction.guild.me).embed_links
        if not emb_links_perm:
            return await interaction.response.send_message(self.bot.invite_link)
        emb = Embed().make_emb("Invite link", f"Invite me to your guild by clicking [here]({self.bot.invite_link})!")
        await interaction.response.send_message(embed=emb)

    @app_commands.command()
    async def info(self, interaction: discord.Interaction):
        """Info|Returns some information about the bot.|"""
        embed = discord.Embed(title="About Amathy")
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

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

        # music stats
        node = wavelink.NodePool.get_node()
        players: List[MPlayer] = node.players
        active_players = 0
        paused_players = 0
        waiting_players = 0
        for player in players:
            if player.is_playing():
                if player.is_paused():
                    paused_players += 1
                else:
                    active_players += 1
            if player.waiting:
                waiting_players += 1

        music_stats = f"""
                ```Active players: {active_players}\nPaused players: {paused_players}\nWaiting players: {waiting_players}```
            """
        embed.add_field(name="Music stats", value=music_stats, inline=True)

        website = "https://amathy.moe"
        supp_server = "https://discord.gg/D87ykxd"
        vote = "https://discordbots.org/bot/410488336344547338/vote"
        invite = self.bot.invite_link
        links = f"\n[Website!]({website}) ✤ [Support server!]({supp_server}) ✤ [Vote for me & get rewards!]({vote}) ✤ [Invite me!]({invite})\n"
        embed.add_field(name="Links", value=links, inline=False)
        embed.set_footer(text="© 2018-2020 - Copyright: AnimeVibe - Project Amathy")
        await interaction.response.send_message(embed=embed)

    # @commands.bot_has_permissions(embed_links=True)
    # @commands.cooldown(1, 8, BucketType.user)
    @app_commands.command()
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

    @commands.command()
    @commands.guild_only()
    async def sync(ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """Utility|Umbra's sync command
        !sync -> global sync
        !sync ~ -> sync current guild
        !sync * -> copies all global app commands to current guild and syncs
        !sync ^ -> clears all commands from the current guild target and syncs (removes guild commands)
        !sync id_1 id_2 -> syncs guilds with id 1 and 2|"""
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot):
    bot.tree.add_command(Bot(bot))
