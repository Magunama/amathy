from discord.ext import tasks, commands
import aiohttp
from discord import Game
import random
import datetime
import asyncio


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.bot.webhook_url = self.bot.consts["dbl_webhook"]
        self.post_gcount.start()
        self.reward_votes.start()
        self.bot_activity.start()
        self.vip_days.start()

    def cog_unload(self):
        self.post_gcount.cancel()
        self.reward_votes.cancel()
        self.bot_activity.cancel()
        self.vip_days.cancel()

    async def send_whook(self, u_name, multi):
        url = self.bot.webhook_url
        pic = "https://i.imgur.com/enep9dS.png"
        votestr = "\nTo vote, click [here](https://top.gg/bot/410488336344547338/vote)."
        if multi > 1:
            pic = "https://i.imgur.com/LjRefpO.png"
        desc = "This vote gave them {} coins and {} xp.{}".format(300*multi, 100*multi, votestr)
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
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=obj)

    def get_vip_interval(self):
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        time_next = time_now + datetime.timedelta(days=1) #interval
        time_next = time_next.replace(hour=0, minute=0, second=0)
        return time_next - time_now

    @tasks.loop(hours=24)
    async def vip_days(self):
        """Vip_days must go down, right?"""
        script = "update amathy.stats set vip_days=stats.vip_days-1 where vip_days > 0"
        await self.bot.funx.execute(script)
        print("[INFO][Task] VIP days just went down!")

    @vip_days.before_loop
    async def before_vip_days(self):
        interval = self.get_vip_interval()
        await asyncio.sleep(interval.total_seconds())

    @tasks.loop(minutes=5)
    async def bot_activity(self):
        # todo dynamic approach
        """Changes bot's activity."""
        games = ["ama help", "getting votes on DBL", "https://amathy.moe", "with Magu and Hrozvitnir", "quality music", "catching pokemon with Andrew"]
        old_game = self.bot.guilds[0].get_member(self.bot.user.id).activity
        old_game_name = ""
        if old_game:
            old_game_name = old_game.name
        new_game_name = random.choice(games)
        while new_game_name == old_game_name:
            new_game_name = random.choice(games)
        game = Game(name=new_game_name)
        await self.bot.change_presence(activity=game)

    @bot_activity.before_loop
    async def before_reward_votes(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def reward_votes(self):
        """Reward users who voted the bot!"""
        script = "select user_id, last_vote, rewards from amathy.votes where rewards>0;"
        data = await self.bot.funx.fetch_many(script)
        for elem in data:
            user_id, last_vote, rewards = elem
            coins = 300 * rewards
            xp = 100 * rewards
            script = "update amathy.votes set rewards=0 where user_id='{0}';".format(user_id)
            await self.bot.funx.execute(script)
            script = "insert into amathy.coins (user_id, bank) values ({0}, {1}) on conflict (user_id) do update set bank=coins.bank+{1};"
            await self.bot.funx.execute(script.format(user_id, coins))
            script = "insert into amathy.stats(user_id, xp) values ({0}, {1}) on conflict (user_id) do update set xp=stats.xp+{1};"
            await self.bot.funx.execute(script.format(user_id, xp))
            user = self.bot.get_user(int(user_id))
            if not user:
                user = user_id
            else:
                text = "Thank you for your vote! You have received {} coins and {} xp. Don't forget that you can vote me every 12 hours!"
                await user.send(text.format(coins, xp))
            await self.send_whook(user, rewards)
            print("[INFO][Task] Rewarded", user, "for", rewards, "votes!")

    @reward_votes.before_loop
    async def before_reward_votes(self):
        print('[INFO][Task] Vote reward task is active...')
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=25)
    async def post_gcount(self):
        """Post guildcount to discordbots.org!"""
        botid = self.bot.user.id
        dbl_token = self.bot.consts["dbl_token"]
        url = f'https://discordbots.org/api/bots/{botid}/stats'
        headers = {'Authorization': dbl_token}

        if not self.bot.is_closed():
            gcount = len(self.bot.guilds)
            payload = {'server_count': gcount}
            try:
                async with aiohttp.ClientSession() as session:
                    data = await session.request('POST', url, json=payload, headers=headers)
                    data = await data.json()
                    if "error" in data:
                        print("[INFO][Task] Request to DBL failed: {}".format(data["error"]))
                    else:
                        print("[INFO][Task] Guildcount sent to DBL! - {} servers -".format(gcount))
            except Exception as e:
                print("[INFO][Task] Request to DBL failed: {}".format(e))

    @post_gcount.before_loop
    async def before_post_gcount(self):
        print('[INFO][Task] Waiting to send guildcount to DBL...')
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))