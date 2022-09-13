import random
from typing import Union, Optional, List

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import FileCheck
from utils.embed import Embed
from utils.paginators import Paginator


class Misc(commands.Cog):
    """Miscellaneous."""

    @app_commands.guild_only()
    # @commands.bot_has_permissions(embed_links=True)
    @app_commands.command()
    async def avatar(self, interaction: discord.Interaction, target: Optional[discord.Member] = None):
        """Info|Returns a user's avatar.|"""

        if target is None:
            target = interaction.user

        emb_desc = "👉 | {0} - {1} avatar"
        user_embed = Embed().make_emb(emb_desc.format(target, "User"), "")
        user_embed.set_image(url=target.avatar.url)
        member_embed = Embed().make_emb(emb_desc.format(target, "Guild member"), "")
        member_embed.set_image(url=target.display_avatar.url)
        embeds = [user_embed, member_embed]

        def paginator_callback(page: int) -> List[discord.Embed]:
            return [embeds[page - 1]]

        await interaction.response.send_message(embed=embeds[0], view=Paginator(callback=paginator_callback, pages=2))


class MiscGroup(app_commands.Group, name="misc"):
    """Miscellaneous."""

    @app_commands.command()
    @app_commands.describe(text="Text to repeat")
    async def say(self, interaction: discord.Interaction, text: str):
        """Fun|Repeats your input.|"""
        alm = discord.AllowedMentions(users=True, everyone=False, roles=False)
        await interaction.response.send_message(text, allowed_mentions=alm)
        # todo: delete message if possible

    @app_commands.command()
    async def joke(self, interaction: discord.Interaction):
        """Fun|Sends a Dad Joke!|"""
        headers = {"Accept": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://icanhazdadjoke.com", headers=headers) as get:
                assert isinstance(get, aiohttp.ClientResponse)
                resp = await get.json()
            await session.close()
        await interaction.response.send_message(resp["joke"])

    # @app_commands.bot_has_permissions(attach_files=True)
    @app_commands.command()
    async def flip(self, interaction: discord.Interaction):
        """Fun|Heads or tail?|"""

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
        await interaction.response.send_message(text, files=files)

    @app_commands.command(name='in')
    @app_commands.describe(channel='The channel to get permissions in')
    @app_commands.describe(member='The member to get permissions of')
    async def _in(
            self,
            interaction: discord.Interaction,
            channel: Union[discord.TextChannel, discord.VoiceChannel],
            member: Optional[discord.Member] = None,
    ):
        """Get permissions for you or another member in a specific channel."""
        embed = self.get_permissions_embed(channel.permissions_for(member or interaction.user))
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc())
    bot.tree.add_command(MiscGroup())
