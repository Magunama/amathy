from discord.ext import commands
import os
from shutil import copyfile
import discord


class FileCheck:
    @staticmethod
    def check_folder(path):
        if os.path.exists(path):
            return True
        return False

    def check_create_folder(self, path):
        if not self.check_folder(path):
            print(f"[Action] I'm creating a folder for you... ({path})")
            os.makedirs(path)

    @staticmethod
    def check_file(path):
        if os.path.isfile(path):
            return True
        return False

    def check_copy_file(self, path):
        if not self.check_file(path):
            print(f"[Action] I'm copying a base file for you... ({path}). \nYou have to manually edit something in it!")
            source_path = path.split("/")[-1]
            copyfile(f"utils/base/{source_path}", path)

    def check_create_file(self, path, content):
        if not self.check_file(path):
            print(f"[Action] I'm creating a file for you... ({path})")
            with open(path, "w") as f:
                f.write(content)


class AuthorCheck:
    @staticmethod
    def is_vip():
        async def vip_check(ctx):
            if ctx.bot:
                vip_days = await ctx.bot.funx.get_vip_days(ctx.author.id)
                if vip_days > 0:
                    return True
            await ctx.send("Sorry, only VIP users can use this command!")
            return False
        return commands.check(vip_check)

    @staticmethod
    def is_creator():
        async def is_creator_check(ctx):
            uid = ctx.message.author.id
            if uid in ctx.bot.owner_ids:
                return True
            else:
                await ctx.send("Creator only access!")
                return False

        return commands.check(is_creator_check)

    @staticmethod
    def is_guild_admin():
        async def inside_check(ctx):
            u = ctx.message.author
            if u.guild_permissions.administrator:
                return True
            await ctx.send("No access! You need to be a server administrator to run this command.")
            return False

        return commands.check(inside_check)


class ChannelCheck:
    @staticmethod
    def is_nsfw():
        async def inside_check(ctx):
            if ctx.channel.is_nsfw():
                return True
            desc = "NSFW commands can only be used in NSFW marked channels."
            emb = discord.Embed(title="You can't use this here!", description=desc)
            emb.set_image(url="https://i.imgur.com/oe4iK5i.gif")
            await ctx.send(embed=emb)
            return False
        return commands.check(inside_check)


class GuildCheck:
    @staticmethod
    def is_guild():
        async def guild_check(ctx):
            if ctx.guild:
                return True
            await ctx.send("Sorry, this command can only be used in a guild!")
            return False
        return commands.check(guild_check)
