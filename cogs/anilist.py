from discord.ext import commands
from utils.embed import Embed
from utils.funx import BaseRequest
import discord.errors
from asyncio import TimeoutError


class Queries:
    ani_anime = """
        query ($id: Int) {
            Media (id: $id, type: ANIME) {
                id
                siteUrl
                coverImage {
                    large
                }
                title {
                    romaji
                    english
                }
                format
                status
                episodes
                duration
                isAdult
                averageScore
                meanScore
                rankings{
                    rank
                    type
                    allTime
                }
                description
                genres
                studios{
                    nodes{
                        name
                        isAnimationStudio
                    }
                }
                relations{
                    edges{
                        relationType
                        node{
                            title{
                                romaji
                            }
                            siteUrl
                            type
                        }
                    }
                }
            } 
        }
    """

    ani_manga = """
        query ($id: Int) {
            Media (id: $id, type: MANGA) {
                id
                siteUrl
                coverImage {
                    large
                }
                title {
                    romaji
                    english
                }
                format
                status
                chapters
                volumes
                isAdult
                averageScore
                meanScore
                rankings{
                    rank
                    type
                    allTime
                }
                description
                genres
                studios{
                    nodes{
                        name
                        isAnimationStudio
                    }
                }
                relations{
                    edges{
                        relationType
                        node{
                            title{
                                romaji
                            }
                            siteUrl
                            type
                        }
                    }
                }
            } 
        }
    """

    ani_character = """
        query ($id: Int) {
            Character(id: $id) {
                id
                siteUrl
                name {
                    full
                    alternative
                }
                favourites
                image{
                    large
                }
                description
                media{
                    edges{
                        voiceActors{
                            name{
                                last
                            }
                            siteUrl
                        }
                        node{
                            title{
                                romaji
                            }
                            siteUrl
                            type
                        }
                    }
                }
            }
        }
    """

    ani_person = """
        query ($id: Int) {
            Staff(id: $id) {
                id
                siteUrl
                name {
                    full
                    alternative
                }
                language
                favourites
                image{
                    large
                }
                description
                staffMedia{
                    nodes{
                        title{
                            romaji
                        }
                    siteUrl
                    } 
                }
                characters{
                    nodes{
                        name{
                            full
                        }
                    siteUrl
                    }
                }
            }
        }

    """

    ani_user = """
        query ($name: String, $id: Int) {
            User(id: $id, name: $name){
                id
                name
                siteUrl
                about
                avatar{
                    large
                }
                bannerImage
                mediaListOptions{
                    scoreFormat
                }
                statistics{
                    anime{
                        count
                        meanScore
                        episodesWatched
                        statuses{
                            status
                            count
                        }
                    }
                    manga{
                        count
                        meanScore
                        chaptersRead
                        statuses{
                            status
                            count
                        }
                    }
                }
                favourites{
                    anime{
                        nodes{
                            title{
                                romaji
                            }
                            siteUrl
                        }
                    }
                    manga{
                        nodes{
                            title{
                                romaji
                            }
                            siteUrl
                        }
                    }
                    characters{
                        nodes{
                            name{
                                full
                            }
                            siteUrl
                        }
                    }
                    staff{
                        nodes{
                            name{
                                full
                            }
                            siteUrl
                        }
                    }
                }
            }
        }
    
    """

    ani_search_media = """
        query ($q: String, $type: MediaType) {
            Page(perPage: 10){
                media(search: $q, type: $type){
                    id
                    siteUrl
                    coverImage {
                        large
                    }
                    title {
                        romaji
                        english
                    }
                    format
                    status
                    episodes
                    duration
                    isAdult
                    averageScore
                    meanScore
                    rankings{
                        rank
                        type
                        allTime
                    }
                    description
                    genres
                }
            }
        }
    """

    ani_search_character = """
        query ($q: String) {
            Page(perPage: 10) {
                characters(search: $q) {
                    id
                    siteUrl
                    name {
                        full
                        alternative
                    }
                    favourites
                    image {
                        large
                    }
                    description
                    media {
                        edges {
                            voiceActors {
                                name {
                                    last
                                }
                                siteUrl
                            }
                            node {
                                title {
                                    romaji
                                }
                                siteUrl
                                type
                            }
                        }
                    }
                }
            }
        }
    """

    ani_search_person = """
    query ($q: String) {
        Page(perPage: 10) {
            staff(search: $q) {
                id
                siteUrl
                name {
                    full
                    alternative
                }
                language
                favourites
                image {
                    large
                }
                description
            }
        }
    }
    """


# todo: Add top command
class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ani_url = "https://graphql.anilist.co"

    @staticmethod
    def ani_media_relations(data):
        # Take relations by type as long as the final string is not too long
        relations = dict()
        for r in data["relations"]["edges"]:
            r_type = r["relationType"]
            r_title = r["node"]["title"]["romaji"]
            if r_type not in relations:
                relations[r_type] = list()
            r_url = r["node"]["siteUrl"]
            row = f"[{r_title}]({r_url})"
            relations[r_type].append(row+ "\n")
        relations_str = dict()
        for r_type in relations:
            titles = relations[r_type]
            r_str = ""
            for i in range(0, len(titles)):
                if len(r_str) + len(titles[i]) > 1000:
                    r_str += "[...]"
                    break
                r_str += titles[i]
            relations_str[r_type] = r_str
        return relations_str

    @staticmethod
    def get_relation_str(relations_str, r_type):
        if r_type in relations_str:
            return relations_str[r_type]
        return "None"

    @staticmethod
    def not_found_embed(title):
        desc = "Sorry, no matching entry found! "
        return Embed().make_emb(title, desc)

    @staticmethod
    def ani_anime_page_1(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for anime with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]

        title_romaji = data["title"]["romaji"]
        title_english = data["title"]["english"]
        explicit = "Yes" if data["isAdult"] else "No"
        average_score = data["averageScore"]
        mean_score = data["meanScore"]
        rank = None
        for r in data["rankings"]:
            if r["type"] == "POPULAR" and r["allTime"]:
                rank = r["rank"]
                break
        fields = [
            ["Title", f"{title_romaji}\n{title_english}"],
            ["Type", data["format"]],
            ["Status", data["status"]],
            ["Episodes", data["episodes"]],
            ["Duration", data["duration"]],
            ["Explicit", explicit],
            ["Score", f"{average_score} ({mean_score})"],
            ["Rank", rank]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_image(url=pic_url)
        emb.set_footer(text="1/5 - Powered by AniList API")
        return emb

    @staticmethod
    def ani_anime_page_2(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for anime with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]

        synopsis = data["description"]
        if synopsis and len(synopsis) > 1000:
            synopsis = synopsis[:1000] + "[...]"
        producers = list()
        studios = list()
        for s in data["studios"]["nodes"]:
            if s["isAnimationStudio"]:
                studios.append(s["name"])
            else:
                producers.append(s["name"])
        fields = [
            ["Synopsis", synopsis, False],
            ["Genres", ", ".join(data["genres"])],
            ["Studios", ", ".join(studios)],
            ["Producers/Licensors", ", ".join(producers)]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="2/5 - Powered by AniList API")
        return emb

    def ani_anime_page_3(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for anime with id **{id}**:\n[Link to page]({url})"
        get_rel_str = self.get_relation_str
        pic_url = data["coverImage"]["large"]

        fields = [
            ["Adaptation", get_rel_str(relations, "ADAPTATION"), False],
            ["Prequel", get_rel_str(relations, "PREQUEL"), False],
            ["Sequel", get_rel_str(relations, "SEQUEL"), False],
            ["Alternative", get_rel_str(relations, "ALTERNATIVE")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="3/5 - Powered by AniList API")
        return emb

    def ani_anime_page_4(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for anime with id **{id}**:\n[Link to page]({url})"
        get_rel_str = self.get_relation_str
        pic_url = data["coverImage"]["large"]

        fields = [
            ["Side story", get_rel_str(relations, "SIDE_STORY"), False],
            ["Summary", get_rel_str(relations, "SUMMARY"), False],
            ["Parent", get_rel_str(relations, "PARENT")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="4/5 - Powered by AniList API")
        return emb

    def ani_anime_page_5(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for anime with id **{id}**:\n[Link to page]({url})"
        get_rel_str = self.get_relation_str
        pic_url = data["coverImage"]["large"]

        fields = [
            ["Spin-off", get_rel_str(relations, "SPIN_OFF"), False],
            ["Character", get_rel_str(relations, "CHARACTER"), False],
            ["Other", get_rel_str(relations, "OTHER")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="5/5 - Powered by AniList API")
        return emb

    def ani_anime_embeds(self, title, data):
        page_1 = self.ani_anime_page_1(title, data)
        page_2 = self.ani_anime_page_2(title, data)

        relations = self.ani_media_relations(data)
        page_3 = self.ani_anime_page_3(title, data, relations)
        page_4 = self.ani_anime_page_4(title, data, relations)
        page_5 = self.ani_anime_page_5(title, data, relations)

        return [page_1, page_2, page_3, page_4, page_5]

    @staticmethod
    def ani_manga_page_1(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for manga with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]

        title_romaji = data["title"]["romaji"]
        title_english = data["title"]["english"]
        explicit = "Yes" if data["isAdult"] else "No"
        average_score = data["averageScore"]
        mean_score = data["meanScore"]
        rank = None
        for r in data["rankings"]:
            if r["type"] == "POPULAR" and r["allTime"]:
                rank = r["rank"]
                break
        fields = [
            ["Title", f"{title_romaji}\n{title_english}"],
            ["Type", data["format"]],
            ["Status", data["status"]],
            ["Chapters", data["chapters"]],
            ["Volumes", data["volumes"]],
            ["Explicit", explicit],
            ["Score", f"{average_score} ({mean_score})"],
            ["Rank", rank]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_image(url=pic_url)
        emb.set_footer(text="1/5 - Powered by AniList API")
        return emb

    @staticmethod
    def ani_manga_page_2(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for manga with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]

        synopsis = data["description"]
        if synopsis and len(synopsis) > 1000:
            synopsis = synopsis[:1000] + "[...]"
        producers = list()
        studios = list()
        for s in data["studios"]["nodes"]:
            if s["isAnimationStudio"]:
                studios.append(s["name"])
            else:
                producers.append(s["name"])
        fields = [
            ["Synopsis", synopsis, False],
            ["Genres", ", ".join(data["genres"])],
            ["Studios", ", ".join(studios)],
            ["Producers/Licensors", ", ".join(producers)]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="2/5 - Powered by AniList API")
        return emb

    def ani_manga_page_3(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for manga with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]
        get_rel_str = self.get_relation_str

        fields = [
            ["Adaptation", get_rel_str(relations, "ADAPTATION"), False],
            ["Prequel", get_rel_str(relations, "PREQUEL"), False],
            ["Sequel", get_rel_str(relations, "SEQUEL"), False],
            ["Alternative", get_rel_str(relations, "ALTERNATIVE")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="3/5 - Powered by AniList API")
        return emb

    def ani_manga_page_4(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for manga with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]
        get_rel_str = self.get_relation_str

        fields = [
            ["Side story", get_rel_str(relations, "SIDE_STORY"), False],
            ["Summary", get_rel_str(relations, "SUMMARY"), False],
            ["Parent", get_rel_str(relations, "PARENT")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="4/5 - Powered by AniList API")
        return emb

    def ani_manga_page_5(self, title, data, relations):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for manga with id **{id}**:\n[Link to page]({url})"
        pic_url = data["coverImage"]["large"]
        get_rel_str = self.get_relation_str

        fields = [
            ["Spin-off", get_rel_str(relations, "SPIN_OFF"), False],
            ["Character", get_rel_str(relations, "CHARACTER"), False],
            ["Other", get_rel_str(relations, "OTHER")]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="5/5 - Powered by AniList API")
        return emb

    def ani_manga_embeds(self, title, data):
        page_1 = self.ani_manga_page_1(title, data)
        page_2 = self.ani_manga_page_2(title, data)

        relations = self.ani_media_relations(data)
        page_3 = self.ani_manga_page_3(title, data, relations)
        page_4 = self.ani_manga_page_4(title, data, relations)
        page_5 = self.ani_manga_page_5(title, data, relations)

        return [page_1, page_2, page_3, page_4, page_5]

    @staticmethod
    def ani_character_media(data):
        voice_actors = set()
        media = {"ANIME": "", "MANGA": ""}
        stop_flag = {"ANIME": False, "MANGA": False}
        for e in data["media"]["edges"]:
            for va in e["voiceActors"]:
                va_name = va["name"]["last"]
                va_url = va["siteUrl"]
                voice_actors.add(f"[{va_name}]({va_url})")
            node_type = e["node"]["type"]
            node_title = e["node"]["title"]["romaji"]
            node_url = e["node"]["siteUrl"]
            media_str = media[node_type]
            row = f"\n[{node_title}]({node_url})"
            if len(media_str) + len(row) > 1000:
                if not stop_flag[node_type]:
                    media_str += "\n[...]"
                    stop_flag[node_type] = True
            else:
                media_str += row
            media[node_type] = media_str
        return voice_actors, media

    @staticmethod
    def ani_character_page_1(title, data, char_media):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for character with id **{id}**:\n[Link to page]({url})"
        pic_url = data["image"]["large"]

        voice_actors, media = char_media
        va_str = ""
        for va in voice_actors:
            row = va + ", "
            if len(va_str) + len(row) > 1000:
                va_str += "[...]"
                break
            va_str += row

        name_full = data["name"]["full"]
        name_alternative = ", ".join(data["name"]["alternative"])
        about = data["description"]
        if about and len(about) > 1000:
            about = about[:1000] + "[...]"
        fields = [
            ["Name", name_full],
            ["Nickname", name_alternative],
            ["Favourites", data["favourites"]],
            ["About", about, False],
            ["Voice actors", va_str[:-2], False]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_image(url=pic_url)
        emb.set_footer(text="1/2 - Powered by AniList API")
        return emb

    def ani_character_page_2(self, title, data, char_media):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for character with id **{id}**:\n[Link to page]({url})"
        pic_url = data["image"]["large"]

        voice_actors, media = char_media

        fields = [
            ["Animeography", media["ANIME"]],
            ["Mangaography", media["MANGA"], False]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="2/2 - Powered by AniList API")
        return emb

    def ani_character_embeds(self, title, data):
        char_media = self.ani_character_media(data)

        page_1 = self.ani_character_page_1(title, data, char_media)
        page_2 = self.ani_character_page_1(title, data, char_media)

        return [page_1, page_2]

    @staticmethod
    def ani_person_page_1(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for person with id **{id}**:\n[Link to page]({url})"
        pic_url = data["image"]["large"]

        name_full = data["name"]["full"]
        name_alternative = ", ".join(data["name"]["alternative"])
        about = data["description"]
        if about and len(about) > 1000:
            about = about[:1000] + "[...]"
        fields = [
            ["Name", name_full],
            ["Nickname", name_alternative],
            ["Favourites", data["favourites"]],
            ["About", about, False]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_image(url=pic_url)
        emb.set_footer(text="1/2 - Powered by AniList API")
        return emb

    @staticmethod
    def ani_person_page_2(title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for person with id **{id}**:\n[Link to page]({url})"
        pic_url = data["image"]["large"]

        media = ""
        for n in data["staffMedia"]["nodes"]:
            title = n["title"]["romaji"]
            url = n["siteUrl"]
            row = f"[{title}]({url})\n"
            if len(media) + len(row) > 1000:
                media += "[...]"
                break
            media += row
        chars = ""
        for n in data["characters"]["nodes"]:
            name = n["name"]["full"]
            url = n["siteUrl"]
            row = f"[{name}]({url})\n"
            if len(chars) + len(row) > 1000:
                chars += "[...]"
                break
            chars += row
        fields = [
            ["Staff positions", media],
            ["Voice acting roles", chars, False]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=pic_url)
        emb.set_footer(text="2/2 - Powered by AniList API")
        return emb

    def ani_person_embeds(self, title, data):
        page_1 = self.ani_person_page_1(title, data)
        page_2 = self.ani_person_page_2(title, data)

        return [page_1, page_2]

    @staticmethod
    def ani_user_page_1(title, desc, data):
        name = data["name"]
        about = data["about"]
        if about and len(about) > 1000:
            about = about[:1000] + "[...]"
        avatar = data["avatar"]["large"]
        banner = data["bannerImage"]
        score_format = data["mediaListOptions"]["scoreFormat"]

        anime = data["statistics"]["anime"]
        anime_str = "```Episodes watched: {}\nMean score: {}"
        anime_str = anime_str.format(anime["episodesWatched"], anime["meanScore"])
        for s in anime["statuses"]:
            st = s["status"]
            c = s["count"]
            anime_str += f"\n{st.title()}: {c}"
        anime_str += "\nTotal entries: {}```".format(anime["count"])
        manga = data["statistics"]["manga"]
        manga_str = "```Chapters read: {}\nMean score: {}"
        manga_str = manga_str.format(manga["chaptersRead"], manga["meanScore"])
        for s in manga["statuses"]:
            st = s["status"]
            c = s["count"]
            manga_str += f"\n{st.title()}: {c}"
        manga_str += "\nTotal entries: {}```".format(manga["count"])

        fields = [
            ["Name", name],
            ["Score format", score_format],
            ["About", about, False],
            ["Anime stats", anime_str, False],
            ["Manga stats", manga_str]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_image(url=avatar)
        if banner:
            emb.set_thumbnail(url=banner)
        emb.set_footer(text="1/3 - Powered by AniList API")
        return emb

    @staticmethod
    def ani_user_page_2(title, desc, data):
        avatar = data["avatar"]["large"]
        fav = dict()
        for f in data["favourites"]:
            if f in ["anime", "manga"]:
                fav[f] = str()
                for n in data["favourites"][f]["nodes"]:
                    title = n["title"]["romaji"]
                    url = n["siteUrl"]
                    row = f"[{title}]({url})\n"
                    if len(fav[f]) + len(row) > 1000:
                        fav[f] += "[...]"
                        break
                    fav[f] += row
        anime_str = fav["anime"] if fav["anime"] else "None"
        manga_str = fav["manga"] if fav["manga"] else "None"
        fields = [
            ["Favourite anime", anime_str],
            ["Favourite manga", manga_str]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=avatar)
        emb.set_footer(text="2/3 - Powered by AniList API")
        return emb

    @staticmethod
    def ani_user_page_3(title, desc, data):
        avatar = data["avatar"]["large"]
        fav = dict()
        for f in data["favourites"]:
            if f in ["characters", "staff"]:
                fav[f] = str()
                for n in data["favourites"][f]["nodes"]:
                    title = n["name"]["full"]
                    url = n["siteUrl"]
                    row = f"[{title}]({url})\n"
                    if len(fav[f]) + len(row) > 1000:
                        fav[f] += "[...]"
                        break
                    fav[f] += row
        chars_str = fav["characters"] if fav["characters"] else "None"
        staff_str = fav["staff"] if fav["staff"] else "None"
        fields = [
            ["Favourite characters", chars_str],
            ["Favourite people", staff_str]
        ]
        emb = Embed().make_emb(title=title, desc=desc, fields=fields)
        emb.set_thumbnail(url=avatar)
        emb.set_footer(text="3/3 - Powered by AniList API")
        return emb

    def ani_user_embeds(self, title, data):
        url = data["siteUrl"]
        id = data["id"]
        desc = f"Details for user with id **{id}**:\n[Link to page]({url})"

        page_1 = self.ani_user_page_1(title, desc, data)
        page_2 = self.ani_user_page_2(title, desc, data)
        page_3 = self.ani_user_page_3(title, desc, data)

        return [page_1, page_2, page_3]

    async def ani_search_anime_embeds(self, query):
        title = "[Amathy v1.8] - AniList anime search by name"
        variables = {"q": query, "type": "ANIME"}
        payload = {"query": Queries.ani_search_media, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Page"]["media"]
        if not data:
            return
        embeds = list()
        for index, entry in enumerate(data):
            page = self.ani_anime_page_1(title, entry)
            # todo: add about and genres
            page.set_footer(text=f"{index+1}/{len(data)} - Powered by AniList API")
            embeds.append(page)
        return embeds

    async def ani_search_manga_embeds(self, query):
        title = "[Amathy v1.8] - AniList manga search by name"
        variables = {"q": query, "type": "MANGA"}
        payload = {"query": Queries.ani_search_media, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Page"]["media"]
        if not data:
            return
        embeds = list()
        for index, entry in enumerate(data):
            page = self.ani_anime_page_1(title, entry)
            # todo: add about and genres
            page.set_footer(text=f"{index + 1}/{len(data)} - Powered by AniList API")
            embeds.append(page)
        return embeds

    async def ani_search_character_embeds(self, query):
        title = "[Amathy v1.8] - AniList character search by name"
        variables = {"q": query}
        payload = {"query": Queries.ani_search_character, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Page"]["characters"]
        if not data:
            return
        embeds = list()
        for index, entry in enumerate(data):
            char_media = self.ani_character_media(entry)
            page = self.ani_character_page_1(title, entry, char_media)
            page.set_footer(text=f"{index + 1}/{len(data)} - Powered by AniList API")
            embeds.append(page)
        return embeds

    async def ani_search_person_embeds(self, query):
        title = "[Amathy v1.8] - AniList person search by name"
        variables = {"q": query}
        payload = {"query": Queries.ani_search_person, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Page"]["staff"]
        if not data:
            return
        embeds = list()
        for index, entry in enumerate(data):
            page = self.ani_person_page_1(title, entry)
            page.set_footer(text=f"{index + 1}/{len(data)} - Powered by AniList API")
            embeds.append(page)
        return embeds

    async def ani_search_embed_menu(self, ctx, query):
        title = "[Amathy v1.8] - AniList search by name"
        desc = (
            f"Which category should I look up `{query}` in?\n"
            "1️⃣ -> **Anime**\n"
            "2️⃣ -> **Manga**\n"
            "3️⃣ -> **Characters**\n"
            "4️⃣ -> **People**\n"
        )
        expected = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        def check(react, user):
            return user.id == ctx.author.id and str(react.emoji) in expected and react.message.id == message.id

        emb = Embed().make_emb(title=title, desc=desc)
        message = await ctx.send(embed=emb)
        for r in expected:
            await message.add_reaction(r)

        try:
            react, user = await self.bot.wait_for('reaction_add', check=check, timeout=10)
        except discord.errors.Forbidden:
            await ctx.send("I need permission to add reactions!")
        except TimeoutError:
            await ctx.send("I see you've changed your mind...")
            await message.delete()
        except Exception as e:
            print(e)
        else:
            await message.delete()
            react = str(react)
            if react == "1️⃣":
                embeds = await self.ani_search_anime_embeds(query)
            elif react == "2️⃣":
                embeds = await self.ani_search_manga_embeds(query)
            elif react == "3️⃣":
                embeds = await self.ani_search_character_embeds(query)
            else:
                embeds = await self.ani_search_person_embeds(query)

            if not embeds:
                return await ctx.send(embed=self.not_found_embed(title))
            await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @commands.group(aliases=["ani", "anichart"])
    async def anilist(self, ctx, *, query=None):
        """Info|Get information from AniList.
        To search for something, use `a ani <query>`|"""
        if not query:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

        split = query.split(" ", 1)
        cmd = split[0]
        args = ""
        if len(split) > 1:
            args = split[1]

        cmd_found = None
        for c in ctx.command.commands:
            if cmd == c.name or cmd in c.aliases:
                cmd_found = c
                break
        if cmd_found:
            await ctx.invoke(cmd_found, args)
        else:
            await self.ani_search_embed_menu(ctx, query)

    @anilist.command()
    async def anime(self, ctx, anime_id=None):
        """Info|Get an anime by its id from AniList.|"""
        if not anime_id:
            return await ctx.send("Hey! You must tell me an anime id.")
        if not anime_id.isdigit():
            return await ctx.send("Wait, that's not a valid anime id!")

        title = "[Amathy v1.8] - AniList anime search by id"
        variables = {"id": anime_id}
        payload = {"query": Queries.ani_anime, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Media"]
        if not data:
            return await ctx.send(embed=self.not_found_embed(title))

        embeds = self.ani_anime_embeds(title, data)
        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @anilist.command()
    async def manga(self, ctx, manga_id=None):
        """Info|Get a manga by its id from AniList.|"""
        if not manga_id:
            return await ctx.send("Hey! You must tell me a manga id.")
        if not manga_id.isdigit():
            return await ctx.send("Wait, that's not a valid manga id!")

        title = "[Amathy v1.8] - AniList manga search by id"
        variables = {"id": manga_id}
        payload = {"query": Queries.ani_manga, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Media"]
        if not data:
            return await ctx.send(embed=self.not_found_embed(title))

        embeds = self.ani_manga_embeds(title, data)
        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @anilist.command(aliases=["char"])
    async def character(self, ctx, char_id=None):
        """Info|Get a character by its id from AniList.|"""
        if not char_id:
            return await ctx.send("Hey! You must tell me a character id.")
        if not char_id.isdigit():
            return await ctx.send("Wait, that's not a valid character id!")

        title = "[Amathy v1.8] - AniList character search by id"
        variables = {"id": char_id}
        payload = {"query": Queries.ani_character, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Character"]
        if not data:
            return await ctx.send(embed=self.not_found_embed(title))

        embeds = self.ani_character_embeds(title, data)
        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @anilist.command(aliases=["staff"])
    async def person(self, ctx, person_id=None):
        """Info|Get a person by its id from AniList.|"""
        if not person_id:
            return await ctx.send("Hey! You must tell me a person id.")
        if not person_id.isdigit():
            return await ctx.send("Wait, that's not a valid personid!")

        title = "[Amathy v1.8] - AniList person search by id"
        variables = {"id": person_id}
        payload = {"query": Queries.ani_person, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["Staff"]
        if not data:
            return await ctx.send(embed=self.not_found_embed(title))

        embeds = self.ani_person_embeds(title, data)
        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)

    @anilist.command()
    async def user(self, ctx, user=None):
        """Info|Get a user by its name or id from AniList|"""
        if not user:
            return await ctx.send("Hey! You must tell me a user id or full name.")

        if user.isdigit():
            title = "[Amathy v1.8] - AniList user search by id"
            variables = {"id": user}
        else:
            title = "[Amathy v1.8] - AniList user search by name"
            variables = {"name": user}
        payload = {"query": Queries.ani_user, "variables": variables}
        data = await BaseRequest().post_json(url=self.ani_url, payload=payload, headers={})
        data = data["data"]["User"]
        if not data:
            return await ctx.send(embed=self.not_found_embed(title))

        embeds = self.ani_user_embeds(title, data)
        await self.bot.funx.embed_menu(ctx=ctx, emb_list=embeds, message=None, page=0)


def setup(bot):
    n = Anime(bot)
    bot.add_cog(n)
