from discord.ext import commands
import aiohttp


class WebHook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.main_webhook = self.bot.consts["updates_webhook"]
        self.bot.base_vote_coins, self.bot.base_vote_xp = 150, 50

    async def send(self, url, obj):
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=obj)

    async def make_guild_payload(self, guild, title):
        pic = str(guild.icon.url)
        invite = self.bot.invite_link
        desc = f"To invite me to a guild, click [here]({invite})."
        guild_owner = guild.owner
        if not guild_owner:
            guild_owner = await commands.MemberConverter().query_member_by_id(self.bot, guild, guild.owner_id)
        return {
            "embeds": [
                {
                    "title": title,
                    "description": desc,
                    "thumbnail": {
                        "url": pic
                    },
                    "fields": [
                        {
                            "name": "Name",
                            "value": guild.name,
                            "inline": True
                        },
                        {
                            "name": "Owner",
                            "value": str(guild_owner),
                            "inline": True
                        },
                        {
                            "name": "Membercount",
                            "value": guild.member_count,
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "If you enjoy our projects, spread the word about us!"
                    }
                }
            ]
        }

    async def send_on_guild_join(self, guild):
        title = "Just joined a new guild! [#{}]".format(len(self.bot.guilds))
        obj = await self.make_guild_payload(guild, title)
        await self.send(self.main_webhook, obj)

    async def send_on_guild_remove(self, guild):
        title = "Just left a guild! [#{}]".format(len(self.bot.guilds))
        obj = await self.make_guild_payload(guild, title)
        await self.send(self.main_webhook, obj)

    async def send_on_vote_received(self, u_name, multi):
        votestr = "\nTo vote, click [here](https://top.gg/bot/410488336344547338/vote)."
        pic = "https://i.imgur.com/enep9dS.png"
        if multi > 1:
            pic = "https://i.imgur.com/LjRefpO.png"
        coins = self.bot.base_vote_coins
        xp = self.bot.base_vote_xp
        desc = "This vote gave them {} coins and {} xp.{}".format(coins*multi, xp*multi, votestr)
        title = "{} just voted!".format(u_name)
        obj = {
            "embeds": [
                {
                    "title": title,
                    "description": desc,
                    "thumbnail": {
                        "url": pic
                    },
                    "footer": {
                        "text": "If you can't donate, at least vote to support us!"
                    }
                }
            ]
        }
        await self.send(self.main_webhook, obj)


async def setup(bot):
    await bot.add_cog(WebHook(bot))
