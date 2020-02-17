import datetime
import discord


class Funx:
    def __init__(self, bot):
        self.bot = bot
        self.date_format = bot.consts["date_format"]

    @staticmethod
    def group_digit(number):
        number_str = str(number)
        digit_groups = []
        while number_str and number_str[-1].isdigit():
            digit_groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return number_str + '.'.join(reversed(digit_groups))

    @staticmethod
    def delta2string(string, lang="en"):
        dic1 = {"ro": ["zile", "ore", "minute", "secunde"],
                "en": ["days", "hours", "minutes", "seconds"],
                "de": ["Tage", "Stunden", "Minuten", "Sekunden"]}
        dic2 = {"ro": ["zi", "ora", "minut", "secunda"],
                "en": ["day", "hour", "minute", "second"],
                "de": ["Tag", "Stunde", "Minute", "Sekunde"]}
        string = str(string).split(".")[0]
        if "," in string:
            daystr, hrstr = string.split(", ")
            daystr = daystr.split(" ")[0]
            hrstr = hrstr.split(":")
        else:
            daystr = "0"
            hrstr = string.split(":")
        split = list()
        split.append(daystr)
        split.extend(hrstr)
        aux1 = dic1[lang]
        aux2 = dic2[lang]
        text = list()
        if lang == "ro":
            salt = " de "
        else:
            salt = " "
        for i in range(len(split)):
            k = split[i]
            if int(k) > 0:
                if int(k) >= 20:
                    text.append(str(int(k)) + salt + aux1[i])
                elif int(k) > 1:
                    text.append(str(int(k)) + " " + aux1[i])
                else:
                    text.append(str(int(k)) + " " + aux2[i])
        ret = ", ".join(text)
        return ret

    @staticmethod
    def get_member_named(server, param):
        member = discord.utils.find(lambda m: param in m.name.lower(), server.members)
        if not member:
            member = discord.utils.find(lambda m: param in m.nick.lower() if m.nick is not None else False, server.members)
        if not member:
            member = discord.utils.find(lambda m: param in str(m).lower(), server.members)
        return member

    @staticmethod
    def get_member_by_id(server, param):
        return server.get_member(param)

    def search_for_member(self, ctx, targ):
        server = ctx.guild
        user = None
        if len(ctx.message.mentions) > 0:
            return ctx.essage.mentions[0]
        if targ:
                user = self.get_member_by_id(server, targ) or self.get_member_named(server, targ.lower())
        return user

    def seconds2string(self, seconds, lang="en"):
        return self.delta2string(datetime.timedelta(seconds=seconds), lang)

    async def run_q(self, sql, multi=False):
        async with self.bot.pool.acquire() as conn:
            print("Total Connections: {0.size} Free Connections: {0.freesize} Script: {1}".format(self.bot.pool, sql))
            # aiomysql.DictCursor
            async with conn.cursor() as cur:
                await cur.execute(sql)
                if not multi:
                    return await cur.fetchone()
                return await cur.fetchall()

    async def run_cq(self, sql, sql_err=None):
        async with self.bot.pool.acquire() as conn:
            print("Total Connections: {0.size} Free Connections: {0.freesize} Script: {1}".format(self.bot.pool, sql))
            async with conn.cursor() as cur:
                try:
                    await cur.execute(sql)
                except Exception as e:
                    print("Eroare executie sql: {}".format(e))
                    if sql_err:
                        await cur.execute(sql_err)
                await conn.commit()

    async def get_coins(self, user_id):
        script = f"select pocket, bank from coins where user_id={user_id}"
        data = await self.bot.funx.run_q(script)
        if not data:
            data = (0, 0)
        return data

    async def get_timer(self, user_id, cat):
        script = f"select {cat} from timers where user_id={user_id}"
        data = await self.bot.funx.run_q(script)
        if not data:
            data = (datetime.datetime(1, 1, 1),)
        return data

    async def save_pocket(self, uid, val):
        # urank = await self.get_rank(uid)
        # if 3 <= urank <= 6:
        #     climit, blimit = 80 * (10 ** 6), 120 * (10 ** 6)
        # elif urank > 6:
        #     climit, blimit = 80 * (10 ** 6), 170 * (10 ** 6)
        # else:
        #     climit, blimit = 20 * (10 ** 6), 100 * (10 ** 6)
        # if val > climit:
        #     val = climit
        # todo: move to bank if limit is surpassed
        script = f"insert into coins (user_id, pocket) values ({uid}, {val}) on duplicate key update pocket={val}"
        await self.run_cq(script)

    async def save_bank(self, uid, val):
        script = f"insert into coins (user_id, bank) values ({uid}, {val}) on duplicate key update bank={val}"
        await self.run_cq(script)

    async def save_timer(self, uid, cat, val):
        val = val.strftime(self.date_format)
        script = f"insert into timers (user_id, {cat}) values ({uid}, \"{val}\") on duplicate key update {cat}=\"{val}\""
        await self.run_cq(script)

    async def embed_menu(self, ctx, emb_list: list, message=None, page=0, timeout=30):
        cog = emb_list[page]
        expected = ["➡", "⬅", "❌"]
        numbs = {
            "next": "➡",
            "back": "⬅",
            "exit": "❌"
        }

        def check(react, user):
            return user.id == ctx.message.author.id and str(react.emoji) in expected and react.message.id == message.id

        if not message:
            message = await ctx.send(embed=cog)
            await message.add_reaction("⬅")
            await message.add_reaction("❌")
            await message.add_reaction("➡")
        else:
            await message.edit(embed=cog)
        try:
            react, user = await self.bot.wait_for('reaction_add', check=check, timeout=timeout)
        except Exception as e:
            print(e)
            react = None
        if react is None:
            try:
                try:
                    await message.clear_reactions()
                except:
                    await message.remove_reaction("⬅", self.bot.user)
                    await message.remove_reaction("❌", self.bot.user)
                    await message.remove_reaction("➡", self.bot.user)
            except Exception as e:
                print(e)
            return None
        reacts = {v: k for k, v in numbs.items()}
        react = reacts[react.emoji]
        if react == "next":
            page += 1
            next_page = page % len(emb_list)
            try:
                await message.remove_reaction("➡", ctx.message.author)
            except:
                pass
            return await self.embed_menu(ctx, emb_list, message=message,
                                         page=next_page, timeout=timeout)
        elif react == "back":
            page -= 1
            next_page = page % len(emb_list)
            try:
                await message.remove_reaction("⬅", ctx.message.author)
            except:
                pass
            return await self.embed_menu(ctx, emb_list, message=message,
                                         page=next_page, timeout=timeout)

        else:
            try:
                return await message.delete()
            except Exception as e:
                print(e)