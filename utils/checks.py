from discord.ext import commands
import os
from shutil import copyfile


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
    def is_privileged():
        async def privileged_check(ctx):
            if ctx.bot:
                vip_days = await ctx.bot.funx.get_vip_days(ctx.author.id)
                if vip_days > 0:
                    return True
            admin_chk = ctx.author.permissions_in(ctx.channel).administrator
            if admin_chk:
                return True
            await ctx.send("Sorry, only VIP users & guild administrators can use this command!")
            return False
        return commands.check(privileged_check)

    @staticmethod
    def is_creator():
        async def creator_check(ctx):
            uid = ctx.message.author.id
            if uid in ctx.bot.owner_ids:
                return True
            else:
                await ctx.send("Creator only access!")
                return False
        return commands.check(creator_check)


class ChannelCheck:
    pass


class GuildCheck:
    pass
