from discord.ext import commands
from utils.checks import GuildCheck
from utils.embed import Embed


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events_names = None

    async def set_events_names(self):
        script = "SELECT column_name FROM information_schema.columns WHERE table_schema = 'amathy' and table_name = 'disabled_events';"
        data = await self.bot.funx.fetch_many(script)
        events = list()
        for record in data:
            ev_name = record["column_name"]
            if not ev_name == "guild_id":
                events.append(ev_name)
        return events

    async def get_disabled_events_list(self, guild_id):
        script = f"select * from amathy.disabled_events where guild_id={guild_id}"
        data = await self.bot.funx.fetch_one(script)
        if data:
            ret = dict(data)
            del ret["guild_id"]
        else:
            ret = dict()
            if not self.events_names:
                self.events_names = await self.set_events_names()
            for ev_name in self.events_names:
                ret[ev_name] = list()
        return ret

    async def get_disabled_event(self, guild_id, ev_name):
        script = f"select {ev_name} from amathy.disabled_events where guild_id={guild_id}"
        data = await self.bot.funx.fetch_one(script)
        if not data:
            return []
        return data[ev_name]

    async def set_disabled_event(self, guild_id, ev_name, disabled_channels):
        script = (
            f"insert into amathy.disabled_events (guild_id, {ev_name}) values ({guild_id}, array {disabled_channels}) "
            f"on conflict (guild_id) do update set {ev_name}=array {disabled_channels}"
        )
        await self.bot.funx.execute(script)

    @staticmethod
    def format_event(ctx, ev_name, disabled_channels):
        fields = list()
        status = "Enabled everywhere"
        disabled_channels_count = len(disabled_channels)
        if disabled_channels_count > 0:
            status = f"Disabled in {disabled_channels_count} channels"
        fields.append(["Status", status, True])
        chan_mentions = list()
        for chan in ctx.guild.text_channels:
            chan_id = str(chan.id)
            if chan_id in disabled_channels:
                chan_mentions.append(chan.mention)
        chan_mentions = ", ".join(chan_mentions)
        if len(chan_mentions) < 1024:
            fields.append(["Disabled in channels:", chan_mentions, True])
        else:
            fields.append(["Disabled in channels:", "Not currently available! (coming soon)", True])
        return Embed().make_emb(title=f"Event {ev_name.title()}", desc="", fields=fields)

    @staticmethod
    def format_events_list(events_list):
        fields = list()
        for ev in events_list:
            # ev_name = ev.replace("_", " ")
            status = "Enabled everywhere"
            disabled_channels_count = len(events_list[ev])
            if disabled_channels_count > 0:
                status = f"Disabled in {disabled_channels_count} channels"
            fields.append([ev.title(), status, True])
        footer = "To see details about a certain event, use ama event list [event]."
        return Embed().make_emb(title="Guild events", desc="", fields=fields, footer=footer)

    @commands.has_permissions(administrator=True)
    @GuildCheck.is_guild()
    @commands.group(aliases=["ev", "events"])
    async def event(self, ctx):
        """Utility|Manage events in your guild.|Administrator permission"""
        if ctx.invoked_subcommand is None:
            emb = await self.bot.cogs["Help"].send_help(ctx.command)
            await ctx.send(embed=emb)

    @event.command(aliases=["show"])
    async def list(self, ctx, ev_name=None):
        """Utility|Lists events in your guild.|"""
        guild_id = ctx.guild.id
        if not ev_name:
            events_list = await self.get_disabled_events_list(guild_id)
            emb = self.format_events_list(events_list)
            return await ctx.send(embed=emb)
        if not self.events_names:
            self.events_names = await self.set_events_names()
        if ev_name not in self.events_names:
            return await ctx.send(f"Sorry, I don't know of any event called `{ev_name}`.")
        disabled_channels = await self.get_disabled_event(guild_id, ev_name)
        emb = self.format_event(ctx, ev_name, disabled_channels)
        await ctx.send(embed=emb)

    @event.command()
    async def enable(self, ctx, ev_name=None, chan=None):
        """Utility|Enables events in your guild.|"""
        if not ev_name:
            usage_text = (
                "Usage:\n"
                "       • `ama event enable [event]` - enables [event] in all text channels;\n"
                "       • `ama event enable [event] [#channel_name]` - enables [event] in selected channel;\n"
                "       • `ama event enable [event] [channel_id]` - enables [event] in selected channel."
            )
            return await ctx.send(usage_text)
        if not self.events_names:
            self.events_names = await self.set_events_names()
        if ev_name not in self.events_names:
            return await ctx.send(f"Sorry, I don't know of any event called `{ev_name}`.")
        guild_id = ctx.guild.id
        if not chan:
            script = (
                f"insert into amathy.disabled_events (guild_id, {ev_name}) values ({guild_id}, '{{}}'::text[]) "
                f"on conflict (guild_id) do update set {ev_name}='{{}}'::text[]"
            )
            await self.bot.funx.execute(script)
            return await ctx.send(f"Event {ev_name} is now enabled in all channels.")
        chan_obj = self.bot.funx.search_for_text_channel(ctx, chan)
        if not chan_obj:
            return await ctx.send(f"No channel found for input `{chan}`!")
        disabled_channels = await self.get_disabled_event(guild_id, ev_name)
        chan_id = str(chan_obj.id)
        if chan_id not in disabled_channels:
            return await ctx.send(f"Event {ev_name} is already enabled in channel {chan_obj.mention}!")
        disabled_channels.remove(chan_id)
        await self.set_disabled_event(guild_id, ev_name, disabled_channels)
        await ctx.send(f"Event {ev_name} is now enabled in channel {chan_obj.mention}.")

    @event.command()
    async def disable(self, ctx, ev_name=None, chan=None):
        """Utility|Disables events in your guild.|"""
        if not ev_name:
            usage_text = (
                "Usage:\n"
                "       • `ama event disable [event]` - disables [event] in all text channels;\n"
                "       • `ama event disable [event] [#channel_name]` - disables [event] in selected channel;\n"
                "       • `ama event disable [event] [channel_id]` - disables [event] in selected channel."
            )
            return await ctx.send(usage_text)
        if not self.events_names:
            self.events_names = await self.set_events_names()
        if ev_name not in self.events_names:
            return await ctx.send(f"Sorry, I don't know of any event called `{ev_name}`.")
        guild_id = ctx.guild.id
        if not chan:
            disabled_channels = list()
            for chan in ctx.guild.text_channels:
                disabled_channels.append(chan.id)
            await self.set_disabled_event(guild_id, ev_name, disabled_channels)
            return await ctx.send(f"Event {ev_name} is now disabled in all channels.")
        chan_obj = self.bot.funx.search_for_channel(ctx, chan)
        if not chan_obj:
            return await ctx.send(f"No channel found for input `{chan}`!")
        disabled_channels = await self.get_disabled_event(guild_id, ev_name)
        chan_id = str(chan_obj.id)
        if chan_id in disabled_channels:
            return await ctx.send(f"Event {ev_name} is already disabled in channel {chan_obj.mention}!")
        disabled_channels.append(chan_id)
        await self.set_disabled_event(guild_id, ev_name, disabled_channels)
        await ctx.send(f"Event {ev_name} is now disabled in channel {chan_obj.mention}.")


def setup(bot):
    bot.add_cog(Events(bot))
