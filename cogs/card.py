from discord.ext import commands
from utils.checks import FileCheck
from utils.embed import Embed
from PIL import Image, ImageFont, ImageDraw
import discord.errors
import random
import asyncio
import os


class Card(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_key_drops = set()
        self.key_drop_imgs_path = "data/card/images/key_drop"
        self.key_drop_font_path = "utils/base/card/fonts/Resotedream.ttf"
        images_found = FileCheck().check_folder(self.key_drop_imgs_path)
        if not images_found:
            self.gen_key_drop_imgs()

    async def should_send_key_drop(self, guild_id, chan_id):
        chan_id = str(chan_id)
        await self.bot.wait_until_ready()
        disabled_channels = await self.bot.cogs["Events"].get_disabled_event(guild_id, "key_drop")
        if chan_id in disabled_channels:
            return False
        return True

    async def send_key_drop(self, chan_obj, forced_drop=False):
        chan_id = chan_obj.id
        if forced_drop:
            if chan_id in self.active_key_drops:
                return await chan_obj.send("Key drop is already active... Please wait and try again, master.")
        self.active_key_drops.add(chan_id)
        pick = random.choice(os.listdir(self.key_drop_imgs_path))
        key_phrase = pick.split(".")[0]

        title = "A magical :key: has appeared!"
        desc = "Be the first to type the word **between the arrow heads** from the picture to get it!"
        perms = chan_obj.permissions_for(chan_obj.guild.me)
        if perms.embed_links:
            with open(f"{self.key_drop_imgs_path}/{pick}", 'rb') as g:
                embed = Embed().make_emb(title, desc)
                file = discord.File(g, filename="keydrop.png")
                embed.set_image(url="attachment://keydrop.png")
                first = await chan_obj.send(file=file, embed=embed)
        elif perms.attach_files:
            with open(f"{self.key_drop_imgs_path}/{pick}", 'rb') as g:
                prev_text = title + "\n" + desc
                first = await chan_obj.send(prev_text, file=discord.File(g, filename="keydrop.png"))
        else:
            if perms.send_messages:
                await chan_obj.send("I was going to drop a key for you, but you're not giving me perms to `attach files`! :confused:")
            return self.active_key_drops.remove(chan_id)

        def check(msg):
            if msg.content.lower() == key_phrase:
                return True
            return False

        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=25)
        except asyncio.TimeoutError:
            key_missed = "So sad, the word was `{}`... :disappointed:\nBe faster next time!".format(key_phrase)
            await chan_obj.send(key_missed)
        except Exception as e:
            print(e)
            return
        else:
            if cf_mes:
                user_id = cf_mes.author.id
                inv = await self.bot.funx.get_inventory(user_id)
                inv = self.bot.funx.inventory_add(inv, "keys")
                await self.bot.funx.save_inventory(user_id, inv)
                await chan_obj.send(f"Nicely done, {cf_mes.author.mention}. You will get the key right away!")
        finally:
            self.active_key_drops.remove(chan_id)
            await first.delete()

    def gen_key_drop_imgs(self):
        word_list = [
            'anime', 'baka', 'bell', 'bookshop', 'bottle', 'brother', 'candle', 'chest', 'coffee', 'coins', 'color', 'corgi', 'crush', 'dark',
            'darling', 'flower', 'gems', 'glass', 'gold', 'green', 'gun', 'honey', 'horns', 'invite', 'jar', 'juice', 'kawaii', 'kiss', 'knife',
            'leaf', 'library', 'light', 'loli', 'love', 'manga', 'monkey', 'movie', 'neko', 'passion', 'pearl', 'pepper', 'phone', 'potato',
            'rain', 'rainbow', 'report', 'salt', 'scarf', 'schedule', 'senpai', 'silver', 'smile', 'snowdrop', 'star', 'sugar', 'summer', 'tea',
            'tomato', 'trophy', 'vision', 'vote', 'waifu', 'yogurt'
        ]
        FileCheck().check_create_folder(self.key_drop_imgs_path)
        font = ImageFont.truetype(self.key_drop_font_path, 60)
        shadow_color = "white"
        for key_word in word_list:
            img = Image.open("utils/base/card/key_background.png")
            draw = ImageDraw.Draw(img)
            text = "> " + key_word + " <"
            text_w, text_h = draw.textsize(text, font=font)
            img_w, img_h = img.size
            x = (img_w - text_w) / 2
            y = 360
            b = 3  # outline border
            draw.text((x - b, y - b), text, font=font, fill=shadow_color)
            draw.text((x + b, y - b), text, font=font, fill=shadow_color)
            draw.text((x - b, y + b), text, font=font, fill=shadow_color)
            draw.text((x + b, y + b), text, font=font, fill=shadow_color)
            draw.text((x, y), text, (128, 0, 0), font=font)
            img.save(f'{self.key_drop_imgs_path}/{key_word}.png')

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.content.lower() == "dropakey":
            forced_drop = message.author.id in self.bot.owner_ids
            if forced_drop:
                return await self.send_key_drop(message.channel, forced_drop)
        dropped = random.choices([1, 0], [1, 1000])[0]
        if dropped:
            should_send = await self.should_send_key_drop(message.guild.id, message.channel.id)
            if should_send:
                await self.send_key_drop(message.channel)


def setup(bot):
    bot.add_cog(Card(bot))
