import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# 3 commands per 8 seconds
shared_cooldown = app_commands.checks.cooldown(rate=3, per=8)


# todo: maybe use GroupCog
class Media(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.funx = bot.funx
        self.wolke = bot.consts["weeb_token"]

    async def weeb_fetch_random(self, r_type, ret):
        params = {"type": r_type, "hidden": "false"}
        headers = {"User-Agent": "Amathy/1.8", "Authorization": "Wolke {}".format(self.wolke)}
        url = "https://api.weeb.sh/images/random"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
        status = data["status"]
        if status == 404:
            return discord.Embed(description="**\"Cat\"** {} not found!".format(r_type))
        if status == 401:
            return discord.Embed(description="Sorry, the provided Wolke token for Weeb.sh is invalid!")
        image = data["url"]
        embed = discord.Embed(description=ret, colour=discord.Colour.purple())
        embed.set_image(url=image)
        embed.set_footer(text="Powered by Weeb.sh API v2.")
        return embed

    async def weeb_fetch_categories(self):
        headers = {"User-Agent": "Amathy/1.8", "Authorization": "Wolke {}".format(self.wolke)}
        url = "https://api.weeb.sh/images/types"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                data = await response.json()
        status = data["status"]
        if not status == 200:
            print("The wolke token is invalid!")
        cats = data["types"]
        return ", ".join(cats)

    async def cog_before_invoke(self, ctx):
        """Since most commands in this cog require certain perms, we might as well check it only once"""
        perms = ctx.channel.permissions_for(ctx.me)
        if not perms.embed_links:
            raise commands.MissingPermissions(["embed_links"])
        if not perms.attach_files:
            raise commands.MissingPermissions(["attach_files"])

    @app_commands.command()
    @shared_cooldown
    async def punch(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Punch your friends/enemies!|"""
        ret = "Here's a punch for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets punched by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("punch", ret)))

    # todo: find fix/replacement for Giphy
    # @app_commands.command()
    # @shared_cooldown
    # async def grope(self, interaction: discord.Interaction, target: discord.Member = None):
    #     """Media|Grope your senpai/waifu!|"""
    #     ret = f"Get groped, {interaction.user.mention}!"
    #     if target:
    #         ret = f"{interaction.user.mention} gropes {target}!"
    #     url = "http://api.giphy.com/v1/gifs/search?q=anime+grope&api_key=dc6zaTOxFJmzC&limit=20"
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url) as response:
    #             data = await response.json()
    #     data = data["data"]
    #     image = random.choice(data)["images"]["original"]["url"]
    #     embed = discord.Embed(description=ret, colour=discord.Colour.purple())
    #     embed.set_image(url=image)
    #     embed.set_footer(text="Powered by Giphy API V1.")
    #     await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @shared_cooldown
    async def think(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Look great while thinking!|"""
        ret = "Here's some thinking for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} think!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("thinking", ret)))

    @app_commands.command()
    @shared_cooldown
    async def greet(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Greet in style!|"""
        ret = "Here's a greet for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets greeted by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("greet", ret)))

    @app_commands.command()
    @shared_cooldown
    async def insult(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Get rekt!|"""
        ret = "Here's an insult for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets insulted by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("insult", ret)))

    @app_commands.command()
    @shared_cooldown
    async def lick(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Delicious lick!|"""
        ret = "Here's a lick for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets licked by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("lick", ret)))

    @app_commands.command()
    @shared_cooldown
    async def smug(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Smug like a boss!|"""
        ret = "Here's a smug for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} makes a smug face to {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("smug", ret)))

    @app_commands.command()
    @shared_cooldown
    async def wag(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Show people how happy you are!|"""
        ret = "Here's a wag for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets wagged by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("wag", ret)))

    @app_commands.command()
    @shared_cooldown
    async def bite(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Bite strong like a dog!|"""
        ret = "Here's a bite for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets bit by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("bite", ret)))

    @app_commands.command()
    @shared_cooldown
    async def slap(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Slap the shit out of people!|"""
        ret = "Here's a slap for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets slapped by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("slap", ret)))

    @app_commands.command()
    @shared_cooldown
    async def tickle(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Tickle them toes!|"""
        ret = "Here's a tickle for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets tickled by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("tickle", ret)))

    @app_commands.command()
    @shared_cooldown
    async def stare(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Stare...|"""
        ret = "Here's a stare for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets stared at by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("stare", ret)))

    @app_commands.command()
    @shared_cooldown
    async def owo(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Notices....owo|"""
        ret = "Here's some owo for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets some owo from {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("owo", ret)))

    @app_commands.command()
    @shared_cooldown
    async def smile(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Be happy!|"""
        ret = "Here's a smile for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} smile!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("smile", ret)))

    @app_commands.command()
    @shared_cooldown
    async def pout(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|A cute pout never hurt anybody.|"""
        ret = "Here's a pout for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} pout!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("pout", ret)))

    @app_commands.command()
    @shared_cooldown
    async def nom(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Monch the haters!|"""
        ret = "Feel free to nom, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} nom something!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("nom", ret)))

    @app_commands.command()
    @shared_cooldown
    async def megumin(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|The only loli you need!|"""
        ret = "Here's some Megumin for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets some Megumin from {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("megumin", ret)))

    @app_commands.command()
    @shared_cooldown
    async def dance(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Dance 'till you break your legs!|"""
        ret = "Here's a dance for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} dance!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("dance", ret)))

    @app_commands.command()
    @shared_cooldown
    async def cuddle(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Cuddle with your senpai/waifu!|"""
        ret = "Here's a cuddle for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets cuddled by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("cuddle", ret)))

    @app_commands.command()
    @shared_cooldown
    async def cry(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Cry in a corner like you always do!|"""
        ret = "I'm crying with you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} cry!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("cry", ret)))

    @app_commands.command()
    @shared_cooldown
    async def blush(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|*blushes in japanese*|"""
        ret = "Here's a blush for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} blush!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("blush", ret)))

    @app_commands.command()
    @shared_cooldown
    async def awoo(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Awoo at the glowing moon!|"""
        ret = "Here's an awoo for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets an awoo from {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("awoo", ret)))

    # @commands.command(aliases=["nya"])
    @app_commands.command()
    @shared_cooldown
    async def neko(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Nekos! My only weakness!|"""
        ret = "Here's a neko for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} and {1} play with a neko!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("neko", ret)))

    # @commands.command(aliases=["nya2"])
    @app_commands.command()
    @shared_cooldown
    async def neko2(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Nekos! Warning: Some lewd nekos exist! :eyes:|"""
        url = "https://nekos.life/api/neko"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                nekos = await response.json()
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.set_image(url=nekos['neko'])
        await interaction.response.send_message(embed=embed)

    # @commands.is_nsfw()
    # @commands.cooldown(3, 8, BucketType.user)
    # @commands.command()
    # async def porn(self, context):
    #     """Explicit|Porn - consume it with pleasure!|"""
    #     link = "https://animevibe.ro/api/porn/pornvibe({}).gif"
    #     author = context.message.author.mention
    #     hentai = "**{0} onii-chan, here!**"
    #     choice = random.randint(1, 197)
    #     embed = discord.Embed(description=hentai.format(author), colour=discord.Colour.purple())
    #     embed.set_footer(text="Amathy | PornVibe Api V 0.2 | https://patreon.com/amathy/")
    #     embed.set_image(url=link.format(choice))
    #     await context.send(embed=embed)

    # @commands.command(aliases=["bang"])
    @app_commands.command()
    @shared_cooldown
    async def kill(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Kill your foes in a stylish manner!|"""
        ret = "OK, I'm gonna kill you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets killed by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("bang", ret)))

    @app_commands.command()
    @shared_cooldown
    async def pat(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Pat them heads!|"""
        ret = "Here's a pat for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets patted by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("pat", ret)))

    @app_commands.command()
    @shared_cooldown
    async def shrug(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Shrug like a boss!|"""
        ret = "Here's a shrug for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} made {1} shrug!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("shrug", ret)))

    @app_commands.command()
    @shared_cooldown
    async def dab(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Dab on them haters!|"""
        ret = "Here's a dab for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets dabbed on by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("dab", ret)))

    @app_commands.command()
    @shared_cooldown
    async def teehee(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Troll :100:|"""
        ret = "Here's a teehee for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets a teehee from {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("teehee", ret)))

    # @commands.command(aliases=["hi5"])
    @app_commands.command()
    @shared_cooldown
    async def highfive(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Good job, mate!|"""
        ret = "Here's a highfive for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets a highfive from {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("highfive", ret)))

    @app_commands.command()
    @shared_cooldown
    async def baka(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Baka baka baka!|"""
        ret = "Y-You're a baka, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets called a baka by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("baka", ret)))

    @app_commands.command()
    @shared_cooldown
    async def handhold(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Hold hands. That's what you're meant to do.|"""
        ret = "Here's how holding hands looks, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets his/her hand hold by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("handholding", ret)))

    @app_commands.command()
    @shared_cooldown
    async def wasted(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|The cops got you!|"""
        ret = "Here's how you get wasted, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets wasted by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("wasted", ret)))

    @app_commands.command()
    @shared_cooldown
    async def sleepy(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|zzz...|"""
        ret = "Here's a sleepy face for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} makes {1} feel sleepy!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("sleepy", ret)))

    @app_commands.command()
    @shared_cooldown
    async def poke(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Did you just poke your eyeball?|"""
        ret = "Here's a poke for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets poked by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("poke", ret)))

    @app_commands.command()
    @shared_cooldown
    async def love(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|The love you never had...|"""
        ret = "Here's some love for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets loved by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("deredere", ret)))

    @app_commands.command()
    @shared_cooldown
    async def kiss(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Kiss your senpai/waifu!|"""
        ret = "Here's a kiss for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets kissed by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("kiss", ret)))

    @app_commands.command()
    @shared_cooldown
    async def hug(self, interaction: discord.Interaction, target: discord.Member = None):
        """Media|Hug your senpai/waifu!"""
        ret = "Here's a hug for you, {}!".format(interaction.user.mention)
        if target:
            ret = "{0} gets hugged by {1}!**".format(target, interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("hug", ret)))

    @app_commands.command()
    @shared_cooldown
    async def weeb(self, interaction: discord.Interaction, category: str = None):
        """Media|Be the number one Weeb.sh fan!|"""
        if not target:
            cats = await self.weeb_fetch_categories()
            text = f"Pick one of the following **\"cats\"**:\n`{cats}`"
            return await interaction.response.send_message(text)
        ret = "You're the number one Weeb.sh fan now!"
        await interaction.response.send_message(embed=(await self.weeb_fetch_random(category, ret)))

    # @commands.command(aliases=["birb", "tweet"])
    @app_commands.command()
    @shared_cooldown
    async def bird(self, interaction: discord.Interaction):
        """Media|See? A random bird!|"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://random.birb.pw/tweet/") as get:
                assert isinstance(get, aiohttp.ClientResponse)
                _url = (await get.read()).decode("utf-8")
                url = "http://random.birb.pw/img/{}".format(str(_url))
            await session.close()
        await interaction.response.send_message(url)

    # @commands.command(aliases=['foxo', 'foxy'])
    @app_commands.command()
    @shared_cooldown
    async def fox(self, interaction: discord.Interaction):
        """Media|See? A random fox!|"""
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://randomfox.ca/floof') as r:
                res = await r.json()
                await cs.close()
        em = discord.Embed()
        await interaction.response.send_message(content=interaction.user.mention, embed=em.set_image(url=res['image']))

    # @commands.command(aliases=["catto"])
    @app_commands.command()
    @shared_cooldown
    async def cat(self, interaction: discord.Interaction):
        """Media|See? A random cat!|"""
        ret = "Here's a cat for you, {}!".format(interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("animal_cat", ret)))

    # @commands.command(aliases=["doggo"])
    @app_commands.command()
    @shared_cooldown
    async def dog(self, interaction: discord.Interaction):
        """Media|See? A random dog!|"""
        ret = "Here's a dog for you, {}!".format(interaction.user.mention)
        await interaction.response.send_message(embed=(await self.weeb_fetch_random("animal_dog", ret)))

    # @commands.command(aliases=['catto2'])
    @app_commands.command()
    @shared_cooldown
    async def cat2(self, interaction: discord.Interaction):
        """Media|See? A random cat!|"""
        headers = {"x-api-key": "527d4d23-baa3-42f5-918d-ed86920dc31e"}
        url = "https://api.thecatapi.com/v1/images/search"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, ) as response:
                data = await response.json()
        em = discord.Embed()
        await interaction.response.send_message(content=interaction.user.mention,
                                                embed=em.set_image(url=data[0]['url']))

    # @commands.command(aliases=['doggo2'])
    @app_commands.command()
    @shared_cooldown
    async def dog2(self, interaction: discord.Interaction):
        """Media|See? A random dog!|"""
        while True:
            async with aiohttp.ClientSession() as cs:
                async with cs.get('https://random.dog/woof.json') as r:
                    res = await r.json()
                    res = res['url']
                    await cs.close()
            if not res.endswith('.mp4'):
                break
        em = discord.Embed()
        await interaction.response.send_message(content=interaction.user.mention, embed=em.set_image(url=res))

    # @commands.is_nsfw()
    # todo: add nsfw check
    @app_commands.command()
    @shared_cooldown
    async def hentai(self, interaction: discord.Interaction):
        """Explicit|Hentai and chill with your senpai/waifu!|"""
        author = interaction.user.mention
        hentai = "**{0} onii-chan, baka, ecchi!**"
        script = "SELECT * FROM amathy.hentai"
        data = await self.funx.fetch_many(script)
        index, image = random.choice(data)
        embed = discord.Embed(title=f"HentaiVibe Api V 0.3 | Hentai link [{index}]", description=hentai.format(author),
                              colour=discord.Colour.purple(), url=image)
        embed.set_footer(text="Image won't load? Report broken link!")
        embed.set_image(url=image)
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @shared_cooldown
    async def anime(self, interaction: discord.Interaction):
        """Media|Surf for some anime images!|"""
        author = interaction.user.mention
        anime = "**{0}, here, onii-chan, animeee~!**"
        choice = random.randint(1, 922)
        link = f"https://animevibe.ro/api/anime/anime({choice}).gif"
        embed = discord.Embed(description=anime.format(author), colour=discord.Colour.purple())
        embed.set_footer(text="Amathy | AnimeVibe Api V 0.2 | https://patreon.com/amathy/")
        embed.set_image(url=link)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Media(bot))
