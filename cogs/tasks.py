from discord.ext import tasks, commands
import aiohttp


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_gcount.start()

    def cog_unload(self):
        self.post_gcount.cancel()

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
    async def before_printer(self):
        print('[INFO][Task] Waiting to send guildcount to DBL...')
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))