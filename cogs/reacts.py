import random
import aiohttp
import discord
from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands
from utils.checks import is_nsfw


# ###################### gud ol' giphy
# url = "http://api.giphy.com/v1/gifs/search?q=anime+punch&api_key=dc6zaTOxFJmzC&limit=20"
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 data = await response.json()
#         data = data["data"]
#         image = random.choice(data)["images"]["original"]["url"]
# ######################


class Reacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.funx = bot.funx
        self.wolke = bot.consts["weeb_token"]

    async def weeb_power(self, r_type, ret):
        params = {"type": r_type, "hidden": "false"}
        headers = {"User-Agent": "Amathy/1.8", "Authorization": "Wolke {}".format(self.wolke)}
        url = "https://api-v2.weeb.sh/images/random"
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

    async def weeb_cats(self):
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

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def punch(self, ctx, target=None):
        """Media|Punch your friends/enemies!|"""
        ret = "Here's a punch for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets punched by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("punch", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def grope(self, ctx, target=None):
        """Media|Grope your senpai/waifu!|"""
        ret = f"Get groped, {ctx.author.mention}!"
        if target:
            ret = f"{ctx.author.mention} gropes target!"
        url = "http://api.giphy.com/v1/gifs/search?q=anime+grope&api_key=dc6zaTOxFJmzC&limit=20"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        data = data["data"]
        image = random.choice(data)["images"]["original"]["url"]
        embed = discord.Embed(description=ret, colour=discord.Colour.purple())
        embed.set_image(url=image)
        embed.set_footer(text="Powered by Giphy API V1.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["thinking"])
    @commands.cooldown(3, 8, BucketType.user)
    async def think(self, ctx, target=None):
        """Media|Look great while thinking!|"""
        ret = "Here's some thinking for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} think!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("thinking", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def greet(self, ctx, target=None):
        """Media|Greet in style!|"""
        ret = "Here's a greet for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets greeted by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("greet", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def insult(self, ctx, target=None):
        """Media|Get rekt!|"""
        ret = "Here's an insult for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets insulted by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("insult", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def lick(self, ctx, target=None):
        """Media|Delicious lick!|"""
        ret = "Here's a lick for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets licked by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("lick", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def smug(self, ctx, target=None):
        """Media|Smug like a boss!|"""
        ret = "Here's a smug for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} makes a smug face to {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("smug", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def wag(self, ctx, target=None):
        """Media|Show people how happy you are!|"""
        ret = "Here's a wag for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets wagged by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("wag", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def bite(self, ctx, target=None):
        """Media|Bite strong like a dog!|"""
        ret = "Here's a bite for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets bit by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("bite", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def slap(self, ctx, target=None):
        """Media|Slap the shit out of people!|"""
        ret = "Here's a slap for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets slapped by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("slap", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def tickle(self, ctx, target=None):
        """Media|Tickle them toes!|"""
        ret = "Here's a tickle for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets tickled by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("tickle", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def stare(self, ctx, target=None):
        """Media|Stare...|"""
        ret = "Here's a stare for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets stared at by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("stare", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def owo(self, ctx, target=None):
        """Media|Notices....owo|"""
        ret = "Here's some owo for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets some owo from {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("owo", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def smile(self, ctx, target=None):
        """Media|Be happy!|"""
        ret = "Here's a smile for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} smile!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("smile", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def pout(self, ctx, target=None):
        """Media|A cute pout never hurt anybody.|"""
        ret = "Here's a pout for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} pout!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("pout", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def nom(self, ctx, target=None):
        """Media|Monch the haters!|"""
        ret = "Feel free to nom, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} nom something!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("nom", ret)))

    @commands.command(aliases=["megumin"])
    @commands.cooldown(3, 8, BucketType.user)
    async def megu(self, ctx, target=None):
        """Media|The only loli you need!|"""
        ret = "Here's some Megumin for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets some Megumin from {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("megumin", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def dance(self, ctx, target=None):
        """Media|Dance 'till you break your legs!|"""
        ret = "Here's a dance for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} dance!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("dance", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def cuddle(self, ctx, target=None):
        """Media|Cuddle with your senpai/waifu!|"""
        ret = "Here's a cuddle for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets cuddled by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("cuddle", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def cry(self, ctx, target=None):
        """Media|Cry in a corner like you always do!|"""
        ret = "I'm crying with you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} cry!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("cry", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def blush(self, ctx, target=None):
        """Media|*blushes in japanese*|"""
        ret = "Here's a blush for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} blush!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("blush", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def awoo(self, ctx, target=None):
        """Media|Awoo at the glowing moon!|"""
        ret = "Here's an awoo for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets an awoo from {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("awoo", ret)))

    @commands.command(aliases=["nya"])
    @commands.cooldown(3, 8, BucketType.user)
    async def neko(self, ctx, target=None):
        """Media|Nekos! My only weakness!|"""
        ret = "Here's a neko for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} and {1} play with a neko!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("neko", ret)))

    @commands.command(aliases=["nya2"])
    @commands.cooldown(3, 8, BucketType.user)
    async def neko2(self, ctx):
        """Media|Nekos! Warning: Some lewd nekos exist! :eyes:|"""
        url = "https://nekos.life/api/neko"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                nekos = await response.json()
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.set_image(url=nekos['neko'])
        await ctx.send(embed=embed)

    @commands.command()
    @is_nsfw()
    @commands.cooldown(3, 8, BucketType.user)
    async def porn(self, context):
        """Explicit|Porn - consume it with pleasure!|"""
        link = "https://animevibe.ro/api/porn/pornvibe({}).gif"
        author = context.message.author.mention
        hentai = "**{0} onii-chan, here!**"
        choice = random.randint(1, 197)
        embed = discord.Embed(description=hentai.format(author), colour=discord.Colour.purple())
        embed.set_footer(text="Amathy | PornVibe Api V 0.2 | https://patreon.com/amathy/")
        embed.set_image(url=link.format(choice))
        await context.send(embed=embed)

    @commands.command(aliases=["bang"])
    @commands.cooldown(3, 8, BucketType.user)
    async def kill(self, ctx, target=None):
        """Media|Kill your foes in a stylish manner!|"""
        ret = "OK, I'm gonna kill you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets killed by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("bang", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def pat(self, ctx, target=None):
        """Media|Pat them heads!|"""
        ret = "Here's a pat for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets patted by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("pat", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def shrug(self, ctx, target=None):
        """Media|Shrug like a boss!|"""
        ret = "Here's a shrug for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} made {1} shrug!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("shrug", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def dab(self, ctx, target=None):
        """Media|Dab on them haters!|"""
        ret = "Here's a dab for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets dabbed on by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("dab", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def teehee(self, ctx, target=None):
        """Media|Troll :100:|"""
        ret = "Here's a teehee for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets a teehee from {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("teehee", ret)))

    @commands.command(aliases=["hi5"])
    @commands.cooldown(3, 8, BucketType.user)
    async def highfive(self, ctx, target=None):
        """Media|Good job, mate!|"""
        ret = "Here's a highfive for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets a highfive from {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("highfive", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def baka(self, ctx, target=None):
        """Media|Baka baka baka!|"""
        ret = "Y-You're a baka, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets called a baka by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("baka", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def handhold(self, ctx, target=None):
        """Media|Hold hands. That's what you're meant to do.|"""
        ret = "Here's how holding hands looks, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets his/her hand hold by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("handholding", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def wasted(self, ctx, target=None):
        """Media|The cops got you!|"""
        ret = "Here's how you get wasted, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets wasted by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("wasted", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def sleepy(self, ctx, target=None):
        """Media|zzz...|"""
        ret = "Here's a sleepy face for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} makes {1} feel sleepy!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("sleepy", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def poke(self, ctx, target=None):
        """Media|Did you just poke your eyeball?|"""
        ret = "Here's a poke for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets poked by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("poke", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def love(self, ctx, target=None):
        """Media|The love you never had...|"""
        ret = "Here's some love for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets loved by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("deredere", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def kiss(self, ctx, target=None):
        """Media|Kiss your senpai/waifu!|"""
        ret = "Here's a kiss for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets kissed by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("kiss", ret)))

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def hug(self, ctx, target=None):
        """Media|Hug your senpai/waifu!"""
        ret = "Here's a hug for you, {}!".format(ctx.message.author.mention)
        if target:
            ret = "{0} gets hugged by {1}!**".format(target, ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("hug", ret)))

    @commands.command()
    @commands.cooldown(1, 8, BucketType.user)
    async def weeb(self, ctx, target=None):
        """Media|Be the number one Weeb.sh fan!|"""
        if not target:
            cats = await self.weeb_cats()
            text = f"Pick one of the following **\"cats\"**:\n`{cats}`"
            return await ctx.send(text)
        ret = "You're the number one Weeb.sh fan now!"
        await ctx.send(embed=(await self.weeb_power(target, ret)))

    @commands.command(aliases=["birb", "tweet"])
    @commands.cooldown(3, 8, BucketType.user)
    async def bird(self, ctx):
        """Media|See? A random bird!|"""
        async with aiohttp.ClientSession()as session:
            async with session.get("http://random.birb.pw/tweet/") as get:
                assert isinstance(get, aiohttp.ClientResponse)
                _url = (await get.read()).decode("utf-8")
                url = "http://random.birb.pw/img/{}".format(str(_url))
            await session.close()
        await ctx.send(url)

    @commands.command(aliases=['foxo'])
    @commands.cooldown(3, 8, BucketType.user)
    async def fox(self, ctx):
        """Media|See? A random fox!|"""
        async with aiohttp.ClientSession() as cs:
            async with cs.get('https://randomfox.ca/floof') as r:
                res = await r.json()
                await cs.close()
        em = discord.Embed()
        await ctx.send(content=ctx.message.author.mention, embed=em.set_image(url=res['image']))

    @commands.command(aliases=["catto"])
    @commands.cooldown(3, 8, BucketType.user)
    async def cat(self, ctx):
        """Media|See? A random cat!|"""
        ret = "Here's a cat for you, {}!".format(ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("animal_cat", ret)))

    @commands.command(aliases=["doggo"])
    @commands.cooldown(3, 8, BucketType.user)
    async def dog(self, ctx):
        """Media|See? A random dog!|"""
        ret = "Here's a dog for you, {}!".format(ctx.message.author.mention)
        await ctx.send(embed=(await self.weeb_power("animal_dog", ret)))

    @commands.command(aliases=['catto2'])
    @commands.cooldown(3, 8, BucketType.user)
    async def cat2(self, ctx):
        """Media|See? A random cat!|"""
        headers = {"x-api-key": "527d4d23-baa3-42f5-918d-ed86920dc31e"}
        url = "https://api.thecatapi.com/v1/images/search"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, ) as response:
                data = await response.json()
        em = discord.Embed()
        await ctx.send(content=ctx.message.author.mention, embed=em.set_image(url=data[0]['url']))

    @commands.command(aliases=['doggo2'])
    @commands.cooldown(3, 8, BucketType.user)
    async def dog2(self, ctx):
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
        await ctx.send(content=ctx.message.author.mention, embed=em.set_image(url=res))

    @commands.command()
    @is_nsfw()
    @commands.cooldown(3, 8, BucketType.user)
    async def hentai(self, context):
        """Explicit|Hentai and chill with your senpai/waifu!|"""
        author = context.message.author.mention
        hentai = "**{0} onii-chan, baka, ecchi!**"
        script = "SELECT * FROM hentai"
        data = await self.funx.run_q(script, "all")
        index, image = random.choice(data)
        embed = discord.Embed(title=f"HentaiVibe Api V 0.3 | Hentai link [{index}]", description=hentai.format(author), colour=discord.Colour.purple(), url=image)
        embed.set_footer(text="Image won't load? Report broken link!")
        embed.set_image(url=image)
        await context.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, BucketType.user)
    async def anime(self, context):
        """Media|Surf for some anime images!|"""
        author = context.message.author.mention
        anime = "**{0}, here, onii-chan, animeee~!**"
        choice = random.randint(1, 922)
        link = f"https://animevibe.ro/api/anime/anime({choice}).gif"
        embed = discord.Embed(description=anime.format(author), colour=discord.Colour.purple())
        embed.set_footer(text="Amathy | AnimeVibe Api V 0.2 | https://patreon.com/amathy/")
        embed.set_image(url=link)
        await context.send(embed=embed)


def setup(bot):
    n = Reacts(bot)
    bot.add_cog(n)
