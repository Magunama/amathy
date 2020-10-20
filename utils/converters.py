import discord.ext.commands.converter as converter
import discord.utils
from discord.ext.commands.errors import MemberNotFound
import re


class MemberConverter(converter.MemberConverter):
    def __init__(self, glob=False):
        super().__init__()
        # whether to query every guild's cache for the member
        self.glob = glob

    @staticmethod
    async def get_member_named(guild, name, query=False):
        # name+disc check
        if len(name) > 5 and name[-5] == '#':
            name, _, discriminator = name.rpartition('#')
            name = name.lower()
            pred = lambda m: m.name.lower() == name and m.discriminator == discriminator
        # nick & (partial) name check
        else:
            name = name.lower()
            pred = lambda m: (m.nick is not None and m.nick.lower() == name) or m.name.lower().startswith(name)

        members = guild.members
        # fetch members
        if query:
            cache = guild._state._member_cache_flags.joined
            members = await guild.query_members(name, limit=100, cache=cache)

        return discord.utils.find(pred, members)

    async def convert(self, ctx, member_str):
        """Converts input string to discord.Member object"""
        bot = ctx.bot
        match = self._get_id_match(member_str) or re.match(r'<@!?([0-9]+)>$', member_str)
        guild = ctx.guild

        result = None
        user_id = None
        if match is None:
            # name check [cache]
            if guild:
                result = await self.get_member_named(guild, member_str)
            elif self.glob:
                result = converter._get_from_guilds(bot, 'get_member_named', member_str)
        else:
            # id & mention check [cache]
            user_id = int(match.group(1))
            if guild:
                result = discord.utils.get(ctx.message.mentions, id=user_id) or guild.get_member(user_id)
            elif self.glob:
                result = converter._get_from_guilds(bot, 'get_member', user_id)

        if result is None:
            if guild is None:
                raise MemberNotFound(member_str)

            if user_id is not None:
                # id check [fetch]
                result = await self.query_member_by_id(bot, guild, user_id)
            else:
                # name check [fetch]
                result = await self.get_member_named(guild, member_str, query=True)

            if not result:
                raise MemberNotFound(member_str)

        return result
