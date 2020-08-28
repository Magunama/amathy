from discord.ext import commands
import aiohttp
import discord


class MAL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.err_text = "Something went wrong. Type `<p>mal help` to learn how to use this command."

    async def fetch_resp(self, url, params):
        headers = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    @commands.bot_has_permissions(embed_links=True)
    @commands.group()
    async def mal(self, ctx):
        """Info|Get information from MyAnimeList.|"""
        if ctx.invoked_subcommand is None:
            line1 = "Available subcommands `top`, `user`, `anime`, `manga`, `character`, `person`, `search`.\n```css\n\n"
            line2 = "mal.top Usage: [#mal top anime airing/upcoming/tv/movie/ova/special]\n"
            line3 = "               [#mal top manga manga/novels/oneshots/doujin/manhua/manhwa]\n"
            line4 = "               [#mal top people]\n"
            line5 = "               [#mal top characters]\n\n"
            line6 = "mal.user Usage: [#mal user <mal_user>]\n"
            line7 = "                [#mal user <mal_user> profile]\n"
            line8 = "                [#mal user <mal_user> history]\n"
            line9 = "                [#mal user <mal_user> friends]\n\n"
            line10 = "mal.anime Usage: [#mal anime <id>]\n\n"
            line11 = "mal.manga Usage: [#mal manga <id>]\n\n"
            line12 = "mal.character Usage: [#mal char/character <id>]\n\n"
            line14 = "mal.person Usage: [#mal person <id>]\n\n"
            line15 = "mal.search Usage: [#mal s/search anime/manga/char/character/person <query>]"
            string = line1+line2+line3+line4+line5+line6+line7+line8+line9+line10+line11+line12+line14+line15+"```"
            await ctx.send(string)
            # await ctx.send(embed=(await self.bot.cogs["Help"].send_help(ctx.command)))

    @mal.group(aliases=["s"])
    async def search(self, ctx, q_type=None, *, q):
        """Info|Search something on MAL.|"""
        if not q_type:
            return await ctx.send(self.err_text)
        if not q:
            return await ctx.send(self.err_text)
        if q_type == "char":
            q_type = "character"
        url = "https://api.jikan.moe/v3/search/{}".format(q_type)
        data = await self.fetch_resp(url, {"q": q, "limit": 10})
        embeds = []

        c = 0
        for k in data["results"]:
            c += 1
            embed = discord.Embed(title="[Amathy v1.8]", description="Search results for search with query **{}**:\n[Link to result]({})".format(q, k["url"]), color=discord.Colour.purple())
            embed.set_image(url=k["image_url"])
            embed.add_field(name="Id", value="{}".format(k["mal_id"]), inline=True)
            if "title" in k:
                embed.add_field(name="Title", value=k["title"], inline=True)
            if "type" in k:
                embed.add_field(name="Type", value=k["type"], inline=True)
            if "episodes" in k:
                embed.add_field(name="Episodes", value=k["episodes"], inline=True)
            if "chapters" in k:
                embed.add_field(name="Chapters", value=k["chapters"], inline=True)
            if "score" in k:
                embed.add_field(name="Score", value=k["score"], inline=True)
            if "rated" in k:
                embed.add_field(name="Rated", value=k["rated"], inline=True)
            if "name" in k:
                embed.add_field(name="Name", value=k["name"], inline=True)
            if "anime" in k:
                a_list = []
                for l in k["anime"]:
                    a_list.append(l["name"])
                if len(a_list) > 0:
                    val = str(", ".join(a_list))
                    if len(val) > 1000:
                        val = val[:1000] + "..."
                else:
                    val = "None"
                embed.add_field(name="Anime appearances", value=val, inline=True)
            if "manga" in k:
                a_list = []
                for l in k["manga"]:
                    a_list.append(l["name"])
                if len(a_list) > 0:
                    val = str(", ".join(a_list))
                    if len(val) > 1000:
                        val = val[:1000] + "..."
                else:
                    val = "None"
                embed.add_field(name="Manga appearances", value=val, inline=True)
            if "alternative_names" in k:
                if len(k["alternative_names"]) > 0:
                    alt = ", ".join(k["alternative_names"])
                else:
                    alt = "None"
            if "synopsis" in k:
                syn = k["synopsis"]
                if len(syn) == 0:
                    syn = "None"
                embed.add_field(name="Synopsis", value=syn, inline=True)
            embed.set_footer(text="{}/10 - Powered by Jikan API.".format(c))
            embeds.append(embed)

        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @mal.group()
    async def person(self, ctx, id=None):
        """Info|Get an actor by its id on MAL.|"""
        if not id:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/person/{}".format(id)
        data = await self.fetch_resp(url, {})
        if "error" in data:
            return await ctx.send("There's been an error searching for this person.")
        embed = discord.Embed(title="[Amathy v1.8]", description="Person details for person with id **{}**:\n[Link to person]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed.set_image(url=data["image_url"])
        embed.add_field(name="Name", value=data["name"], inline=True)
        if len(data["alternate_names"]) > 0:
            nicks = ", ".join(data["alternate_names"])
        else:
            nicks = "None"
        embed.add_field(name="Alternate names", value=nicks, inline=True)
        ab = str(data["about"])
        if len(ab) > 1000:
            ab = ab[:1000] + "[...]"
        embed.add_field(name="About", value=ab, inline=True)
        for k in ["voice_acting_roles", "anime_staff_positions", "published_manga"]:
            elem = str(len(data[k]))
            embed.add_field(name=k.replace("_", " ").capitalize(), value=elem, inline=True)
        embed.set_footer(text="1/1 - Powered by Jikan API.")

        await ctx.send(embed=embed)

    @mal.group(aliases=["char"])
    async def character(self, ctx, id=None):
        """Info|Get a character by its id on MAL.|"""
        if not id:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/character/{}".format(id)
        data = await self.fetch_resp(url, {})
        if "error" in data:
            return await ctx.send("There's been an error searching for this character.")
        embeds = []

        embed = discord.Embed(title="[Amathy v1.8]", description="Character details for character with id **{}**:\n[Link to character]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed.set_image(url=data["image_url"])
        embed.add_field(name="Name", value=data["name"], inline=True)
        if len(data["nicknames"]) > 0:
            nicks = ", ".join(data["nicknames"])
        else:
            nicks = "None"
        embed.add_field(name="Nicknames", value=nicks, inline=True)
        ab = str(data["about"])
        if len(ab) > 1000:
            ab = ab[:1000] + "[...]"
        embed.add_field(name="About", value=ab, inline=True)
        va = data["voice_actors"]
        va_list = []
        for k in va:
            if k["language"] in ["English", "Japanese"]:
                va_list.append(k["name"])
        embed.add_field(name="Voice actors", value="; ".join(va_list), inline=True)
        embed.set_footer(text="1/2 - Powered by Jikan API.")
        embeds.append(embed)

        embed = discord.Embed(title="[Amathy v1.8]", description="Character details for character with id **{}**:\n[Link to character]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed.set_thumbnail(url=data["image_url"])
        for k in ["animeography", "mangaography"]:
            elems = data[k]
            ret_list = []
            for l in elems:
                ret_list.append(l["name"])
            if len(ret_list) > 0:
                ret = str(", ".join(ret_list))
                if len(ret) > 1000:
                    ret = ret[:1000] + "[...]"
            else:
                ret = "None"
            embed.add_field(name=k.capitalize(), value=ret, inline=True)
        embed.set_footer(text="2/2 - Powered by Jikan API.")
        embeds.append(embed)

        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @mal.group()
    async def manga(self, ctx, id=None):
        """Info|Get a manga by its id on MAL.|"""
        if not id:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/manga/{}".format(id)
        data = await self.fetch_resp(url, {})
        if "error" in data:
            return await ctx.send("There's been an error searching for this manga.")
        embeds = []

        embed = discord.Embed(title="[Amathy v1.8]", description="Manga details for manga with id **{}**:\n[Link to manga]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed.set_image(url=data["image_url"])
        embed.add_field(name="Title", value="{}\n{}".format(data["title"], data["title_english"]), inline=True)
        embed.add_field(name="Type", value=data["type"], inline=True)
        embed.add_field(name="Status", value=data["status"], inline=True)
        embed.add_field(name="Chapters", value="{}".format(data["chapters"]), inline=True)
        embed.add_field(name="Score", value=data["score"], inline=True)
        embed.add_field(name="Rank", value=data["rank"], inline=True)
        embed.set_footer(text="1/5 - Powered by Jikan API.")
        embeds.append(embed)

        embed2 = discord.Embed(title="[Amathy v1.8]", description="Manga details for manga with id **{}**:\n[Link to manga]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed2.set_thumbnail(url=data["image_url"])
        syn = str(data["synopsis"])
        if len(syn) > 1000:
            syn = syn[:1000] + "[...]"
        embed2.add_field(name="Synopsis", value=syn, inline=True)
        genres_list = []
        for k in data["genres"]:
            genres_list.append(k["name"])
        embed2.add_field(name="Genres", value=", ".join(genres_list), inline=True)
        authors_list = []
        for k in data["authors"]:
            authors_list.append(k["name"])
        embed2.add_field(name="Authors", value=", ".join(authors_list), inline=True)
        serializations_list = []
        for k in data["serializations"]:
            serializations_list.append(k["name"])
        embed2.add_field(name="Serializations", value=", ".join(serializations_list), inline=True)
        embed2.set_footer(text="2/5 - Powered by Jikan API.")
        embeds.append(embed2)

        embed3 = discord.Embed(title="[Amathy v1.8]", description="Manga details for manga with id **{}**:\n[Link to manga]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed3.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Sequel", "Prequel", "Alternative setting", "Alternative version"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000] + "[...]"
            else:
                val = "None"
            embed3.add_field(name=l, value=val, inline=True)
        embed3.set_footer(text="3/5 - Powered by Jikan API.")
        embeds.append(embed3)

        embed4 = discord.Embed(title="[Amathy v1.8]", description="Manga details for manga with id **{}**:\n[Link to manga]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed4.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Side story", "Summary", "Full story", "Parent story"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000] + "[...]"
            else:
                val = "None"
            embed4.add_field(name=l, value=val, inline=True)
        embed4.set_footer(text="4/5 - Powered by Jikan API.")
        embeds.append(embed4)

        embed5 = discord.Embed(title="[Amathy v1.8]", description="Manga details for manga with id **{}**:\n[Link to manga]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed5.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Spin-off", "Adaptation", "Character", "Other"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000] + "[...]"
            else:
                val = "None"
            embed5.add_field(name=l, value=val, inline=True)
        embed5.set_footer(text="5/5 - Powered by Jikan API.")
        embeds.append(embed5)

        await self.bot.funx.embed_menu(ctx=ctx, embeds=embeds, message=None, page=0)

    @mal.group()
    async def anime(self, ctx, id=None):
        """Info|Get an anime by its id on MAL.|"""
        if not id:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/anime/{}".format(id)
        data = await self.fetch_resp(url, {})
        if "error" in data:
            return await ctx.send("There's been an error searching for this anime.")
        embeds = []

        embed = discord.Embed(title="[Amathy v1.8]", description="Anime details for anime with id **{}**:\n[Link to anime]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed.set_image(url=data["image_url"])
        embed.add_field(name="Title", value="{}\n{}".format(data["title"], data["title_english"]), inline=True)
        embed.add_field(name="Type", value=data["type"], inline=True)
        embed.add_field(name="Status", value=data["status"], inline=True)
        embed.add_field(name="Episodes", value="{}".format(data["episodes"]), inline=True)
        embed.add_field(name="Duration", value=data["duration"], inline=True)
        embed.add_field(name="Rating", value=data["rating"], inline=True)
        embed.add_field(name="Score", value=data["score"], inline=True)
        embed.add_field(name="Rank", value=data["rank"], inline=True)
        embed.set_footer(text="1/5 - Powered by Jikan API.")
        embeds.append(embed)

        embed2 = discord.Embed(title="[Amathy v1.8]", description="Anime details for anime with id **{}**:\n[Link to anime]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed2.set_thumbnail(url=data["image_url"])
        syn = str(data["synopsis"])
        if len(syn) > 1000:
            syn = syn[:1000] + "[...]"
        embed2.add_field(name="Synopsis", value=syn, inline=True)
        genres_list = []
        for k in data["genres"]:
            genres_list.append(k["name"])
        embed2.add_field(name="Genres", value=", ".join(genres_list), inline=True)
        producers_list = []
        for k in data["producers"]:
            producers_list.append(k["name"])
        embed2.add_field(name="Producers", value=", ".join(producers_list), inline=True)
        licensors_list = []
        for k in data["licensors"]:
            licensors_list.append(k["name"])
        embed2.add_field(name="Licensors", value=", ".join(licensors_list), inline=True)
        studios_list = []
        for k in data["studios"]:
            studios_list.append(k["name"])
        embed2.add_field(name="Studios", value=", ".join(studios_list), inline=True)
        embed2.set_footer(text="2/5 - Powered by Jikan API.")
        embeds.append(embed2)

        embed3 = discord.Embed(title="[Amathy v1.8]", description="Anime details for anime with id **{}**:\n[Link to anime]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed3.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Sequel", "Prequel", "Alternative setting", "Alternative version"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000]+"[...]"
            else:
                val = "None"
            embed3.add_field(name=l, value=val, inline=True)
        embed3.set_footer(text="3/5 - Powered by Jikan API.")
        embeds.append(embed3)

        embed4 = discord.Embed(title="[Amathy v1.8]", description="Anime details for anime with id **{}**:\n[Link to anime]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed4.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Side story", "Summary", "Full story", "Parent story"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000] + "[...]"
            else:
                val = "None"
            embed4.add_field(name=l, value=val, inline=True)
        embed4.set_footer(text="4/5 - Powered by Jikan API.")
        embeds.append(embed4)

        embed5 = discord.Embed(title="[Amathy v1.8]", description="Anime details for anime with id **{}**:\n[Link to anime]({})".format(id, data["url"]), color=discord.Colour.purple())
        embed5.set_thumbnail(url=data["image_url"])
        rel = data["related"]
        params = ["Spin-off", "Adaptation", "Character", "Other"]
        for l in params:
            a_list = []
            if l in rel:
                for k in rel[l]:
                    a_list.append(k["name"])
            if len(a_list) > 0:
                val = str(", ".join(a_list))
                if len(val) > 1000:
                    val = val[:1000] + "[...]"
            else:
                val = "None"
            embed5.add_field(name=l, value=val, inline=True)
        embed5.set_footer(text="5/5 - Powered by Jikan API.")
        embeds.append(embed5)

        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @mal.group()
    async def user(self, ctx, targ=None, q_type=None, kwargs=None):
        """Info|Get info about an user on MAL.|"""
        # todo: animelist, mangalist
        model = ["profile", "history", "friends", "animelist", "mangalist"]
        if not q_type:
            q_type = "profile"
        if not q_type in model:
            return await ctx.send(self.err_text)
        if not targ:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/user/{}".format(targ)
        if q_type == "profile":
            k = await self.fetch_resp(url, {})
            embeds = []
            prof_desc = "User details for **{}**:\nSection `Profile`\n[Link to profile]({})".format(targ, k["url"])

            embed = discord.Embed(title="[Amathy v1.8]", description=prof_desc, color=discord.Colour.purple())
            join_date_str = str(k["joined"]).split("T")[0]
            last_online_str = str(k["last_online"]).split("T")[0]
            embed.add_field(name="Join date", value=join_date_str, inline=True)
            embed.add_field(name="Last online", value=last_online_str, inline=True)
            birth_str = str(k["birthday"]).split("T")[0]
            embed.add_field(name="Gender", value=k["gender"])
            embed.add_field(name="Location", value=k["location"])
            embed.add_field(name="Birthday", value=birth_str)
            embed.set_image(url=k["image_url"])
            embed.set_footer(text="1/3 - Powered by Jikan API.")
            embeds.append(embed)

            embed2 = discord.Embed(title="[Amathy v1.8]", description=prof_desc, color=discord.Colour.purple())
            a = k["anime_stats"]
            anime_stats = "```\nDays watched: {}\nMean score: {}\nWatching: {}\nCompleted: {}\nOn hold: {}\nDropped: {}\nPlan to watch: {}\nTotal entries: {}\nEpisodes watched: {}```".format(a["days_watched"], a["mean_score"], a["watching"], a["completed"], a["on_hold"], a["dropped"], a["plan_to_watch"], a["total_entries"], a["episodes_watched"])
            embed2.add_field(name="Anime stats", value=anime_stats, inline=True)
            m = k["manga_stats"]
            manga_stats = "```\nDays read: {}\nMean score: {}\nReading: {}\nCompleted: {}\nOn hold: {}\nDropped: {}\nPlan to read: {}\nTotal entries: {}\nVolumes read: {}```".format(m["days_read"], m["mean_score"], m["reading"], m["completed"], m["on_hold"], m["dropped"], m["plan_to_read"], m["total_entries"], m["volumes_read"])
            embed2.add_field(name="Manga stats", value=manga_stats, inline=True)
            embed2.set_footer(text="2/3 - Powered by Jikan API.")
            embeds.append(embed2)

            embed3 = discord.Embed(title="[Amathy v1.8]", description=prof_desc, color=discord.Colour.purple())
            af_str = ""
            for l in k["favorites"]["anime"]:
                af_str += "\n{}".format(l["name"])
            mf_str = ""
            for l in k["favorites"]["manga"]:
                mf_str += "\n{}".format(l["name"])
            pf_str = ""
            for l in k["favorites"]["people"]:
                pf_str += "\n{}".format(l["name"])
            embed3.add_field(name="Anime favorites", value="```\n{}```".format(af_str), inline=True)
            embed3.add_field(name="Manga favorites", value="```\n{}```".format(mf_str), inline=True)
            embed3.add_field(name="People favorites", value="```\n{}```".format(pf_str), inline=True)
            embed3.set_footer(text="3/3 - Powered by Jikan API.")
            embeds.append(embed3)

            await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

        elif q_type == "history":
            url += "/{}".format(q_type)
            data = await self.fetch_resp(url, {})
            data = data["history"]
            embed = discord.Embed(title="[Amathy v1.8]", description="User details for **{}**:\nSection `History`".format(targ), color=discord.Colour.purple())
            count = 0
            for k in data:
                count += 1
                if count > 10:
                    break
                name = k["meta"]["name"]
                k_type = k["meta"]["type"]
                inc = "{} " + str(k["increment"])
                if k_type == "anime":
                    inc = inc.format("Episode")
                else:
                    inc = inc.format("Volume")
                date_str = str(k["date"]).split("T")[0]
                url = k["meta"]["url"]
                val = "[Link to {}]({})\n```Update: {}\nDate: {}```".format(k_type, url, inc, date_str)
                embed.add_field(name=name, value=val)
            embed.set_footer(text="Powered by Jikan API.")
            await ctx.send(embed=embed)

        elif q_type == "friends":
            url += "/{}".format(q_type)
            data = await self.fetch_resp(url, {})
            data = data["friends"]
            embed = discord.Embed(title="[Amathy v1.8]", description="User details for **{}**:\nSection `Friends`".format(targ), color=discord.Colour.purple())
            for k in data:
                name = k["username"]
                last_online = str(k["last_online"]).split("T")[0]
                friends_since = str(k["friends_since"]).split("T")[0]
                url = k["url"]
                val = "[Link to friend]({})\n```Last online: {}\nFriends since: {}```".format(url, last_online, friends_since)
                embed.add_field(name=name, value=val)
            embed.set_footer(text="Powered by Jikan API.")
            await ctx.send(embed=embed)

    @mal.group()
    async def top(self, ctx, q_type=None, q_subtype=None):
        """Info|Get the top listed entries on MAL.|"""
        model = {"anime": ["airing", "upcoming", "tv", "movie", "ova", "special"],
                 "manga": ["manga", "novels", "oneshots", "doujin", "manhwa", "manhua"],
                 "people": [], "characters": []}
        if not q_type in model:
            return await ctx.send(self.err_text)
        url = "https://api.jikan.moe/v3/top/{}/1".format(q_type)
        if q_subtype:
            if not q_subtype in model[q_type]:
                return await ctx.send(self.err_text)
            url = "{}/{}".format(url, q_subtype)
        data = await self.fetch_resp(url, {})
        data = data["top"]
        embeds = []
        if data:
            a = 0
            for k in data:
                a += 1
                if a > 10:
                    break
                embed = discord.Embed(title="[Amathy v1.8]", description="MAL Top 10: `{}`. Filter: `{}`".format(q_type, q_subtype), color=discord.Colour.purple())
                embed.add_field(name="Title", value=k["title"], inline=True)
                embed.add_field(name="MAL id", value=k["mal_id"], inline=True)
                embed.add_field(name="Rank", value="#{}".format(k["rank"]), inline=True)
                if "type" in k:
                    embed.add_field(name="Type", value=k["type"], inline=True)
                if "episodes" in k:
                    embed.add_field(name="Episodes", value=k["episodes"], inline=True)
                if "volumes" in k:
                    embed.add_field(name="Volumes", value=k["volumes"], inline=True)
                if "start_date" in k:
                    embed.add_field(name="Start date", value=str(k["start_date"]), inline=True)
                if "end_date" in k:
                    embed.add_field(name="End date", value=str(k["end_date"]), inline=True)
                if "score" in k:
                    embed.add_field(name="Score", value=k["score"], inline=True)
                embed.add_field(name="Link MAL", value="[Click me!]({})".format(k["url"]), inline=True)
                embed.set_image(url=k["image_url"])
                embed.set_footer(text="{}/10 - Powered by Jikan API.".format(a))

                embeds.append(embed)
            await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)


def setup(bot):
    n = MAL(bot)
    bot.add_cog(n)
