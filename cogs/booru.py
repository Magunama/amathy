from discord.ext import commands
from utils.funx import BaseRequest
from discord import Embed
import json


class BooruPost:
    def __init__(self, target, post_data):
        self.tag_string = None
        self.source = None
        self.image_url = None

        if target == "danbooru":
            self.tag_string = post_data["tag_string"]
        elif target == "lolibooru":
            self.image_url = post_data["file_url"].replace(" ", "+")
        elif target == "realbooru":
            directory = post_data["directory"]
            image = post_data["image"]
            self.image_url = f"https://realbooru.com/images/{directory}/{image}"
        elif target == "e621":
            self.tag_string = " ".join(post_data["tags"]["general"])
            if post_data["sources"]:
                self.source = post_data["sources"][0]
            self.image_url = post_data["file"]["url"]

        if not self.tag_string:
            self.tag_string = post_data["tags"]
        if not self.source and "source" in post_data:
            self.source = post_data["source"]
        if not self.image_url:
            self.image_url = post_data["file_url"]


class Booru(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_urls = {
            "konachan": "https://konachan.com/post.json",
            "gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1",
            "lolibooru": "https://lolibooru.moe/post/index.json",
            "danbooru": "http://danbooru.donmai.us/posts.json",
            "e621": "http://e621.net/posts.json",
            "realbooru": "https://realbooru.com/index.php?page=dapi&s=post&q=index&json=1"
        }

    async def fetch_posts(self, target, limit=1, randomize=False):
        url = self.base_urls[target]
        tags = ""
        if randomize:
            if target in ["gelbooru", "realbooru"]:
                tags += "sort:random"
            else:
                tags += "order:random"
        headers = {"User-Agent": "Amathy v1.8"}
        params = {"limit": limit, "tags": tags}
        data = await BaseRequest().get_text(url, headers=headers, params=params)
        data = json.loads(data)
        # todo: check for bad response
        if target == "e621":
            return data["posts"][0]
        return data[0]

    def embed_post(self, post):
        emb = Embed(description=f"Tags:\n```{post.tag_string}```")
        emb.set_image(url=post.image_url)
        if post.source:
            emb.add_field(name="Source", value=f"[Click here for that juicy sauce!]({post.source})")
        return emb

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["kona"])
    async def konachan(self, ctx):
        """Explicit|Retrieve images from Konachan.com|"""
        if ctx.invoked_subcommand is None:
            pass

    @konachan.command(name="random", aliases=["r"])
    async def k_random(self, ctx):
        """Explicit|Retrieve a random image from Konachan.com|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("konachan", randomize=True)
        post = BooruPost("konachan", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["gel"])
    async def gelbooru(self, ctx):
        """Explicit|Retrieve images from Gelbooru.com|"""
        if ctx.invoked_subcommand is None:
            pass

    @gelbooru.command(name="random", aliases=["r"])
    async def g_random(self, ctx):
        """Explicit|Retrieve a random image from Gelbooru.com|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("gelbooru", randomize=True)
        post = BooruPost("gelbooru", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["loli"])
    async def lolibooru(self, ctx):
        """Explicit|Retrieve images from Lolibooru.moe|"""
        if ctx.invoked_subcommand is None:
            pass

    @lolibooru.command(name="random", aliases=["r"])
    async def l_random(self, ctx):
        """Explicit|Retrieve a random image from Lolibooru.moe|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("lolibooru", randomize=True)
        post = BooruPost("lolibooru", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["dan"])
    async def danbooru(self, ctx):
        """Explicit|Retrieve images from Danbooru.donmai.us|"""
        if ctx.invoked_subcommand is None:
            pass

    @danbooru.command(name="random", aliases=["r"])
    async def d_random(self, ctx):
        """Explicit|Retrieve a random image from Danbooru.donmai.us|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("danbooru", randomize=True)
        post = BooruPost("danbooru", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["furry"])
    async def e621(self, ctx):
        """Explicit|Retrieve images from e621.net|"""
        if ctx.invoked_subcommand is None:
            pass

    @e621.command(name="random", aliases=["r"])
    async def e_random(self, ctx):
        """Explicit|Retrieve a random image from e621.net|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("e621", randomize=True)
        post = BooruPost("e621", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)

    @commands.guild_only()
    @commands.is_nsfw()
    @commands.group(aliases=["real"])
    async def realbooru(self, ctx):
        """Explicit|Retrieve images from Realbooru.com|"""
        if ctx.invoked_subcommand is None:
            pass

    @realbooru.command(name="random", aliases=["r"])
    async def r_random(self, ctx):
        """Explicit|Retrieve a random image from Realbooru.com|"""
        await ctx.trigger_typing()
        post_data = await self.fetch_posts("realbooru", randomize=True)
        post = BooruPost("realbooru", post_data)
        emb = self.embed_post(post)
        await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(Booru(bot))
