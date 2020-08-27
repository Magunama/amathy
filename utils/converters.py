from discord.ext import commands
import discord.utils


class MemberNotFound(Exception):
    """Simple Exception that carries the error message"""
    def __init__(self, message):
        self.message = message


class MemberConverter(commands.Converter):
    async def convert(self, ctx, member_str):
        """Converts input string to discord.Member object"""

        # id check
        if member_str.isdigit():
            guild = ctx.guild
            if guild:
                member = guild.get_member(int(member_str))
                if member:
                    return member

        # mention check
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
            if member:
                return member

        # name+disc check
        if len(member_str) > 5 and member_str[-5] == '#':
            name = member_str[:-5].lower()
            discrim = member_str[-4:]
            pred = lambda m: m.name.lower() == name and m.discriminator == discrim
            member = discord.utils.find(pred, ctx.guild.members)
            if member:
                return member

        member_str_lookup = member_str.lower()

        # nick check
        pred = lambda m: m.nick.lower() == member_str_lookup if m.nick else False
        member = discord.utils.find(pred, ctx.guild.members)
        if member:
            return member

        # (partial) name check
        pred = lambda m: member_str_lookup in m.name.lower()
        member = discord.utils.find(pred, ctx.guild.members)
        if member:
            return member

        raise MemberNotFound(f"Member `{member_str}` not found in current guild!")

