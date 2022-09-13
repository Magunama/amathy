import asyncio
import datetime
import random

import aiohttp
from discord import Activity, ActivityType
from discord.ext import tasks, commands


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utc_diff = bot.consts["utc_diff"]
        self.bot.updates_webhook = self.bot.consts["updates_webhook"]
        self.bot.api_url = self.bot.consts["api_url"]
        self.bot.api_key = self.bot.consts["api_key"]
        self.post_gcount.start()
        self.reward_votes.start()
        self.bot_activity.start()
        self.vip_days.start()
        self.refill_bet.start()
        self.reset_votes.start()

    def cog_unload(self):
        self.post_gcount.cancel()
        self.reward_votes.cancel()
        self.bot_activity.cancel()
        self.vip_days.cancel()
        self.refill_bet.cancel()
        self.reset_votes.cancel()

    def get_vip_interval(self):
        time_utc = datetime.datetime.utcnow()
        time_now = time_utc + datetime.timedelta(hours=self.utc_diff)
        time_next = time_now + datetime.timedelta(days=1)  # interval
        time_next = time_next.replace(hour=0, minute=0, second=0)
        return time_next - time_now

    @tasks.loop(hours=24)
    async def vip_days(self):
        """Vip_days must go down, right?"""
        script = "update amathy.stats set vip_days=stats.vip_days - 1 where vip_days > 0"
        await self.bot.funx.execute(script)
        print("[INFO][Task] VIP days just went down!")

    @vip_days.before_loop
    async def before_vip_days(self):
        interval = self.get_vip_interval()
        await asyncio.sleep(interval.total_seconds())

    @tasks.loop(minutes=5)
    async def refill_bet(self):
        """Refill bets for gamblers."""
        script = "update amathy.timers set bet_left = timers.bet_left + 1 where bet_left < 20"
        await self.bot.funx.execute(script)

    @tasks.loop(minutes=5)
    async def bot_activity(self):
        """Changes bot's activity."""
        activities = (
            (("quality music", "with Magu and Hrozvitnir"), ActivityType.playing),
            (("/help", "/bot vote", "/daily"), ActivityType.listening),
            (("Pokemon Go with Andrew", "the best bot contest"), ActivityType.competing),
            # (("votes on Top.gg", "https://amathy.moe"), ActivityType.watching),
            (("votes on Top.gg", "SOME COMMANDS THAT ARE CURRENTLY UNAVAILABLE"), ActivityType.watching),
        )

        new_activity_category = random.choice(activities)
        new_activity = random.choice(new_activity_category[0])
        new_activity_type = new_activity_category[1]

        await self.bot.change_presence(activity=Activity(type=new_activity_type, name=new_activity))

    @bot_activity.before_loop
    async def before_bot_activity(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def reward_votes(self):
        """Reward users who voted the bot!"""
        # todo: connect queries
        # params = {"api_key": self.bot.api_key}
        url = f"{self.bot.api_url}/vote/{self.bot.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:  # params
                data = await response.json()
        for elem in data:
            user_id = elem["user"]
            last_vote = elem["dateTime"]
            rewards = 1
            if elem["is_Weekend"]:
                rewards = 2
            script = (
                "insert into amathy.votes (user_id, monthly_votes, last_vote, total_votes) values "
                "({0}, {1}, '{2}', {1}) on conflict (user_id) do update set monthly_votes=votes.monthly_votes+{1}, "
                "last_vote='{2}', total_votes=votes.total_votes+{1};"
            )
            script = script.format(user_id, rewards, last_vote)
            await self.bot.funx.execute(script)
            coins = self.bot.base_vote_coins * rewards
            xp = self.bot.base_vote_xp * rewards
            script = "insert into amathy.coins (user_id, bank) values ({0}, {1}) on conflict (user_id) do update set bank=coins.bank+{1};"
            await self.bot.funx.execute(script.format(user_id, coins))
            script = "insert into amathy.stats(user_id, xp) values ({0}, {1}) on conflict (user_id) do update set xp=stats.xp+{1};"
            await self.bot.funx.execute(script.format(user_id, xp))
            user = self.bot.get_user(int(user_id))
            if not user:
                user = user_id
            else:
                last_vote_str = last_vote.split(".")[0]
                last_vote_str = last_vote_str.replace("T", " ")
                reward_text = (
                    "Thank you for your vote received on {} (UTC+{})! "
                    "You have been rewarded **{}** coins and **{}** xp. "
                    "Don't forget that you can vote me every 12 hours!"
                )
                await user.send(reward_text.format(last_vote_str, self.utc_diff, coins, xp))
            await self.bot.cogs["WebHook"].send_on_vote_received(user, rewards)
            print("[INFO][Task] Rewarded", user, "for", rewards, "votes!")

    @reward_votes.before_loop
    async def before_reward_votes(self):
        print("[INFO][Task] Vote reward task is now active!")
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=25)
    async def post_gcount(self):
        """Post guildcount to Top.gg!"""
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
        print("[INFO][Task] Waiting to send guildcount to Top.gg...")
        await asyncio.sleep(300)

    @tasks.loop(hours=24)
    async def reset_votes(self):
        """Reset monthly votes."""
        today = datetime.datetime.today().date()
        first_day = today.replace(day=1)
        script = f"update amathy.votes set monthly_votes = 0 where last_vote < '{first_day}';"
        await self.bot.funx.execute(script)
        print("[INFO][Task] Any votes from last month were just removed!")


async def setup(bot):
    await bot.add_cog(Tasks(bot))
