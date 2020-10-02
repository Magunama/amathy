from math import ceil, floor
import datetime
import discord
import time
import json
import aiohttp


class BaseRequest:
    @staticmethod
    async def post_json(url, headers=None, payload=None):
        async with aiohttp.ClientSession() as session:
            data = await session.request('POST', url, json=payload, headers=headers)
            return await data.json()

    @staticmethod
    async def get_json(url, headers=None, params=None):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                return await response.json()


class Level:
    base_xp = 250
    exponent = 1.8

    def from_xp(self, xp):
        """Turn xp into level"""
        return ceil((xp / self.base_xp) ** (1 / self.exponent))

    def to_xp(self, lvl):
        """Turn level into xp"""
        return floor(self.base_xp * (lvl ** self.exponent))


class Funx:
    def __init__(self, bot):
        self.bot = bot
        self.date_format = bot.consts["date_format"]

    launch_time = time.time()

    @staticmethod
    def group_digit(number):
        number_str = str(number)
        digit_groups = []
        while number_str and number_str[-1].isdigit():
            digit_groups.append(number_str[-3:])
            number_str = number_str[:-3]
        return number_str + '.'.join(reversed(digit_groups))

    @staticmethod
    def seconds2delta(secs):
        return datetime.timedelta(seconds=secs)

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
    def search_for_text_channel(ctx, targ):
        if targ.isdigit():
            targ = ctx.guild.get_channel(int(targ))
            if not isinstance(targ, discord.channel.TextChannel):
                targ = None
        else:
            if targ.startswith("<#"):
                targ = targ[2:-1]
                targ = ctx.guild.get_channel(int(targ))
                if not isinstance(targ, discord.channel.TextChannel):
                    targ = None
            else:
                targ = discord.utils.find(lambda c: targ in c.name, ctx.guild.text_channels)
        return targ

    @staticmethod
    def search_for_channel(ctx, targ):
        if targ.isdigit():
            targ = ctx.guild.get_channel(int(targ))
        else:
            if targ.startswith("<#"):
                targ = targ[2:-1]
                targ = ctx.guild.get_channel(int(targ))
            else:
                targ = discord.utils.find(lambda c: targ in c.name, ctx.guild.channels)
        return targ

    def seconds2string(self, seconds, lang="en"):
        return self.delta2string(datetime.timedelta(seconds=seconds), lang)

    async def fetch_one(self, query, *args):
        return await self.bot.pool.fetchrow(query, *args)

    async def fetch_many(self, query, *args):
        return await self.bot.pool.fetch(query, *args)

    async def execute(self, query, *args):
        # print("Total Connections: {0.size} Free Connections: {0.freesize} Script: {1}".format(self.bot.pool, sql))
        connection = await self.bot.pool.acquire()
        async with connection.transaction():
            await self.bot.pool.execute(query, *args)
        await self.bot.pool.release(connection)

    async def get_coins(self, user_id):
        # todo: limit
        script = f"select pocket, bank from amathy.coins where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return 0, 0
        return data

    async def get_gems(self, user_id):
        script = f"select gems from amathy.stats where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return 0
        return data["gems"]

    async def get_stats(self, user_id):
        script = f"select xp, gems, vip_days from amathy.stats where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return 0, 0, 0
        return data

    async def get_xp(self, user_id):
        script = f"select xp from amathy.stats where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return 0
        return data["xp"]

    async def get_vip_days(self, user_id):
        if user_id in self.bot.owner_ids:
            return 999
        script = f"select vip_days from amathy.stats where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return 0
        return data["vip_days"]

    async def get_timer(self, user_id, cat):
        script = f"select {cat} from amathy.timers where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return datetime.datetime(1, 1, 1)
        return data[cat]

    async def get_inventory(self, user_id):
        script = f"select inventory from amathy.stats where user_id={user_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return {}
        return json.loads(data["inventory"])

    async def get_inv_item_count(self, user_id, item_name):
        inventory = await self.get_inventory(user_id)
        if item_name not in inventory:
            return 0
        return inventory[item_name]

    async def get_prefix(self, guild_id):
        script = f"select prefix from amathy.guilds where guild_id={guild_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return None
        prefix = data["prefix"]
        if not prefix:
            return None
        return prefix

    @staticmethod
    def inventory_add(inventory, item_name, quantity=1):
        if item_name not in inventory:
            inventory[item_name] = 0
        num = inventory[item_name] + quantity
        inventory[item_name] = num
        return inventory

    @staticmethod
    def inventory_rem(inventory, item_name, quantity=1):
        num = 0
        if item_name in inventory:
            num = inventory[item_name]
        if num > 0:
            del inventory[item_name]
            if quantity == "all":
                quantity = num
            if num > quantity:
                inventory[item_name] = num - quantity
        return inventory

    async def save_inventory(self, user_id, inv):
        inv = json.dumps(inv)
        script = f"insert into amathy.stats (user_id, inventory) values ({user_id}, '{inv}') on conflict (user_id) do update set inventory='{inv}'"
        await self.execute(script)

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
        script = f"insert into amathy.coins (user_id, pocket) values ({uid}, {val}) on conflict (user_id) do update set pocket={val}"
        await self.execute(script)

    async def save_bank(self, uid, val):
        script = f"insert into amathy.coins (user_id, bank) values ({uid}, {val}) on conflict (user_id) do update set bank={val}"
        await self.execute(script)

    async def save_gems(self, uid, val):
        script = f"insert into amathy.stats (user_id, gems) values ({uid}, {val}) on conflict (user_id) do update set gems={val}"
        await self.execute(script)

    async def save_xp(self, uid, val):
        script = f"insert into amathy.stats (user_id, xp) values ({uid}, {val}) on conflict (user_id) do update set xp={val}"
        await self.execute(script)

    async def save_timer(self, uid, cat, val):
        val = val.strftime(self.date_format)
        script = f"insert into amathy.timers (user_id, {cat}) values ({uid}, '{val}') on conflict (user_id) do update set {cat}='{val}'"
        await self.execute(script)

    async def set_prefix(self, guild_id, val):
        script = f"insert into amathy.guilds (guild_id, prefix) values ({guild_id}, '{val}') " \
                 f"on conflict (guild_id) do update set prefix='{val}'"
        await self.execute(script)

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