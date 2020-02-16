import discord
import random
import datetime


class Embed:
    def __init__(self):
        self.colors = [0x004080, 0x008080, 0xff8040, 0xff0000, 0x804040, 0x400000, 0x004000, 0x008080, 0x004080,
                       0x8000ff, 0xff00ff, 0x800040, 0x000040]

    def color_list(self):
        return self.colors

    def make_emb(self, title, desc, author, fields, footer=None, url=None, timestamp=None, empty_field=False):
        embed = discord.Embed(title=title, description=desc, color=random.choice(self.color_list()), url=url)
        embed.set_author(name=author["name"], icon_url=author["icon_url"])
        for field in fields:
            name = field[0]
            value = field[1]

            if empty_field:
                if not name:
                    name = "\u200b"
                if not value:
                    value = "\u200b"

            inline = field[2]
            if not inline:
                inline = True
            if name and value:
                embed.add_field(name=name, value=value, inline=inline)
        if not timestamp:
            timestamp = datetime.datetime.utcnow()
        embed.timestamp = timestamp
        if not footer:
            footer = ">>> Please donate to keep me alive <<<"
        embed.set_footer(text=footer)
        return embed
