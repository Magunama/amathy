import asyncio
import async_timeout
import copy
import datetime
import discord
import math
import random
import re
import typing
import wavelink
from discord.ext import commands, menus
from utils.checks import AuthorCheck
from utils.music import QueueExtension, Spotify, SimplifiedSpotifyTrack

# Spotify URI/URL regex
SPOTIFY_REG = re.compile("^(https?://open.spotify.com/(playlist|track)/|spotify:(playlist|track):)([a-zA-Z0-9]+)(.*)$")

# URL matching REGEX...
URL_REG = re.compile(r"https?://(?:www\.)?.+")


class NoChannelProvided(commands.CommandError):
    """Error raised when no suitable voice channel was supplied."""
    pass


class IncorrectChannelError(commands.CommandError):
    """Error raised when commands are issued outside of the players session channel."""
    pass


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ("requester",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get("requester")


class Player(wavelink.Player):
    """Custom wavelink Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context: commands.Context = kwargs.get('context', None)

        self.queue = QueueExtension()
        self.controller = None

        self.previous_track = None
        self.repeat = False

        self.waiting = False
        self.updating = False

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    async def do_next(self) -> None:
        if self.is_playing or self.waiting:
            return

        # Clear the votes for a new song...
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        try:
            self.waiting = True
            with async_timeout.timeout(180):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            # No music has been played for 3 minutes, cleanup and disconnect...
            await self.teardown()
            if self.context:
                await self.context.send("No music enqueued in the last 3 minutes, disconnecting...")
            return

        if isinstance(track, SimplifiedSpotifyTrack):
            results = await self.node.get_tracks(f'ytsearch:{track.desc}')
            if not results:
                return await self.do_next()
            yt_track = results[0]
            track = Track(yt_track.id, yt_track.info, requester=track.requester)

        self.previous_track = track
        await self.play(track)
        self.waiting = False

        # Invoke our players controller...
        await self.invoke_controller()

    async def invoke_controller(self) -> None:
        """Method which updates or sends a new player controller."""
        if self.updating:
            return

        self.updating = True

        if not self.controller:
            self.controller = InteractiveController(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        elif not await self.is_position_fresh():
            try:
                await self.controller.message.delete()
            except discord.HTTPException:
                pass

            self.controller.stop()

            self.controller = InteractiveController(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        else:
            embed = self.build_embed()
            await self.controller.message.edit(content=None, embed=embed)

        self.updating = False

    def build_embed(self) -> typing.Optional[discord.Embed]:
        """Method which builds our players controller embed."""
        track = self.current
        if not track:
            return

        channel = self.bot.get_channel(int(self.channel_id))
        qsize = self.queue.qsize()

        thumbnail = track.thumb
        if not thumbnail:
            thumbnail = "https://media.discordapp.net/attachments/758008323021996126/758008650089627698/404.gif"
        duration = 0
        if not track.is_stream:
            duration = self.bot.funx.seconds2string(track.length / 1000)
        # try:
        #     duration = self.bot.funx.seconds2string(1000 * track.length)
        # except OverflowError:
        #     duration = 0

        embed = discord.Embed(title=f"Music Controller | {channel.name}", colour=discord.Color.purple())
        embed.description = f"**Now Playing**:\n[{track.title}]({track.uri})\n\n"
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Duration", value=duration)
        embed.add_field(name="Requested by", value=track.requester.mention, inline=False)
        embed.add_field(name="Volume", value=f"**`{self.volume}%`**")
        embed.add_field(name="Queue Length", value=str(qsize))
        embed.add_field(name="Repeat :repeat:", value=("enabled" if self.repeat else "disabled"))

        return embed

    async def is_position_fresh(self) -> bool:
        """Method which checks whether the player controller should be remade or updated."""
        try:
            async for message in self.context.channel.history(limit=5):
                if message.id == self.controller.message.id:
                    return True
        except (discord.HTTPException, AttributeError):
            return False

        return False

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        if self.controller:
            try:
                await self.controller.message.delete()
            except discord.errors.HTTPException:
                pass
            # except Exception as e:
            #     # todo: check exception thrown
            #     print(type(e))
            #     print(e)

            self.controller.stop()

        try:
            await self.destroy()
        except KeyError:
            pass


class InteractiveController(menus.Menu):
    """The Players interactive controller menu class."""

    def __init__(self, *, embed: discord.Embed, player: Player):
        super().__init__(timeout=None)

        self.embed = embed
        self.player = player

    def update_context(self, payload: discord.RawReactionActionEvent):
        """Update our context with the user who reacted."""
        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload: discord.RawReactionActionEvent):
        if payload.event_type == 'REACTION_REMOVE':
            return False

        if not payload.member:
            return False
        if payload.member.bot:
            return False
        if payload.message_id != self.message.id:
            return False
        if payload.member not in self.bot.get_channel(int(self.player.channel_id)).members:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx: commands.Context, channel: discord.TextChannel) -> discord.Message:
        return await channel.send(embed=self.embed)

    @menus.button(emoji='\u25B6')
    async def resume_command(self, payload: discord.RawReactionActionEvent):
        """Resume button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('resume')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23F8')
    async def pause_command(self, payload: discord.RawReactionActionEvent):
        """Pause button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command('pause')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23F9')
    async def stop_command(self, payload: discord.RawReactionActionEvent):
        """Stop button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('stop')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23ED')
    async def skip_command(self, payload: discord.RawReactionActionEvent):
        """Skip button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('skip')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\U0001F500')
    async def shuffle_command(self, payload: discord.RawReactionActionEvent):
        """Shuffle button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('shuffle')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F501")
    async def repeat_command(self, payload: discord.RawReactionActionEvent):
        """Repeat button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("repeat")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u2795')
    async def volup_command(self, payload: discord.RawReactionActionEvent):
        """Volume up button"""
        ctx = self.update_context(payload)

        # avoid spam of button
        if not Music.is_privileged(ctx):
            return

        command = self.bot.get_command('volup')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u2796')
    async def voldown_command(self, payload: discord.RawReactionActionEvent):
        """Volume down button."""
        ctx = self.update_context(payload)

        # avoid spam of button
        if not Music.is_privileged(ctx):
            return

        command = self.bot.get_command('voldown')
        ctx.command = command

        await self.bot.invoke(ctx)

    # @menus.button(emoji='\U0001F1F6')
    # async def queue_command(self, payload: discord.RawReactionActionEvent):
    #     """Player queue button."""
    #     ctx = self.update_context(payload)
    #
    #     command = self.bot.get_command('queue')
    #     ctx.command = command
    #
    #     await self.bot.invoke(ctx)


class Music(commands.Cog, wavelink.WavelinkMixin):
    """Music Cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        spotify_credentials = bot.consts["spotify_api"]
        self.spotify = Spotify(spotify_credentials)

        if not hasattr(bot, 'wavelink'):
            bot.wavelink = wavelink.Client(bot=bot)

        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self) -> None:
        """Connect and intiate nodes."""
        await self.bot.wait_until_ready()

        if self.bot.wavelink.nodes:
            previous = self.bot.wavelink.nodes.copy()

            for node in previous.values():
                await node.destroy()

        nodes = {'MAIN': {'host': '127.0.0.1',
                          'port': 2333,
                          'rest_uri': 'http://127.0.0.1:2333',
                          'password': 'youshallnotpass',
                          'identifier': 'MAIN',
                          'region': 'us_central'
                          }}

        for n in nodes.values():
            await self.bot.wavelink.initiate_node(**n)

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        print(f'Music node {node.identifier} is ready!')

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload):
        if isinstance(payload, wavelink.events.TrackEnd):
            if payload.player.repeat and payload.player.previous_track:
                await payload.player.queue.put(payload.player.previous_track)

        await payload.player.do_next()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        player: Player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """Cog wide error handler."""
        if isinstance(error, IncorrectChannelError):
            return

        if isinstance(error, NoChannelProvided):
            return await ctx.send('You must be in a voice channel or provide one to connect to.')

    async def cog_check(self, ctx: commands.Context):
        """Cog wide check, which disallows commands in DMs."""
        if not ctx.guild:
            await ctx.send('Music commands are not available in Private Messages.')
            return False

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        """Coroutine called before command invocation.

        We mainly just want to check whether the user is in the players controller channel.
        """
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context:
            if player.context.channel != ctx.channel:
                await ctx.send(f'{ctx.author.mention}, you must be in {player.context.channel.mention} to use music commmands for this session.')
                raise IncorrectChannelError

        if ctx.command.name == 'connect' and not player.context:
            return

        # todo: think about privileged permissions
        # elif await self.is_privileged(ctx):
        #     return

        if not player.channel_id:
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected:
            if ctx.author not in channel.members:
                await ctx.send(f'{ctx.author.mention}, you must be in `{channel.name}` to use voice commands.')
                raise IncorrectChannelError

    def required_votes(self, ctx: commands.Context):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop':
            if len(channel.members) - 1 == 2:
                required = 2

        return required

    @staticmethod
    async def is_privileged(ctx: commands.Context):
        """Check whether the user is an Admin or VIP."""
        vip_days = await ctx.bot.funx.get_vip_days(ctx.author.id)
        if vip_days == 0:
            admin_chk = ctx.author.permissions_in(ctx.channel).administrator
            if not admin_chk:
                return False
        return True

    @commands.command(aliases=["summon"], hidden=True)
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Music|Connect to a voice channel.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if player.is_connected:
            return

        channel = getattr(ctx.author.voice, 'channel', channel)
        if channel is None:
            raise NoChannelProvided

        permissions = channel.permissions_for(ctx.me)

        if not permissions.connect or not permissions.speak:  # Check user limit too?
            return await ctx.send("I need the `CONNECT` and `SPEAK` permissions.")

        await player.connect(channel.id)

    @commands.command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """
            Music|Play or queue a song with the given query.
            Spotify "playback" is also possible through YouTube conversion.|
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            await ctx.invoke(self.connect)

        # check if query is a valid spotify link
        valid_spotify_link = SPOTIFY_REG.fullmatch(query)
        if valid_spotify_link:
            return await self.spotify.play(ctx, player, valid_spotify_link)

        query = query.strip('<>')
        if not URL_REG.match(query):
            query = f'ytsearch:{query}'
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send('No songs were found with that query. Please try again.', delete_after=8)

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.send(f'```ini\nAdded the playlist {tracks.data["playlistInfo"]["name"]}'
                           f' with {len(tracks.tracks)} songs to the queue.\n```', delete_after=8)
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.send(f'```ini\nAdded {track.title} to the queue\n```', delete_after=8)
            await player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Music|Pauses the current track.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if player.is_paused or not player.is_connected:
            return

        if await self.is_privileged(ctx):
            await ctx.send('A privileged user has paused the player.', delete_after=8)
            player.pause_votes.clear()

            return await player.set_pause(True)

        required = self.required_votes(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send('Vote to pause passed. Pausing player.', delete_after=8)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to pause the player.', delete_after=8)

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Music|Resumes the current track.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_paused or not player.is_connected:
            return

        if await self.is_privileged(ctx):
            await ctx.send('A privileged user has resumed the player.', delete_after=8)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required_votes(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send('Vote to resume passed. Resuming player.', delete_after=8)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to resume the player.', delete_after=8)

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Music|Skip the currently playing song.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_playing:
            return

        if await self.is_privileged(ctx):
            await ctx.send('⏭ | A privileged user has skipped the song.', delete_after=8)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send('⏭ | The song requester has skipped the song.', delete_after=8)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required_votes(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send('⏭ | Vote to skip passed. Skipping song.', delete_after=8)
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(f'{ctx.author.mention} has voted to skip the song.', delete_after=8)

    @commands.command(aliases=["disconnect", "dc"])
    async def stop(self, ctx: commands.Context):
        """Music|Disconnects the player from the voice channel and clears its queue.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if await self.is_privileged(ctx):
            await ctx.send('⏹ | A privileged user has stopped the player.', delete_after=8)
            return await player.teardown()

        required = self.required_votes(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send('⏹ | Vote to stop passed. Stopping the player.', delete_after=8)
            await player.teardown()
        else:
            await ctx.send(f'{ctx.author.mention} has voted to stop the player.', delete_after=8)

    @AuthorCheck.is_privileged()
    @commands.command(aliases=["vol"])
    async def volume(self, ctx: commands.Context, *, vol: int = None):
        """
            Music|Changes the player's volume. (0-200)
            Note that going above 100 may reduce audio quality.|VIP or administrator permission
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if vol is None:
            return await ctx.send(f'🔈 | {player.volume}%')

        if not 0 <= vol <= 200:
            return await ctx.send('Please enter a value between 0 and 200.')

        await player.set_volume(vol)
        await ctx.send(f'🎧 🔈 | **Set the volume to {vol}%** 🎧', delete_after=8)

    @commands.command(aliases=['mix'])
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the players queue."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.send('Add more songs to the queue before shuffling. (> 2)', delete_after=8)

        if await self.is_privileged(ctx):
            await ctx.send('A privileged user has shuffled the playlist.', delete_after=8)
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        required = self.required_votes(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send('Vote to shuffle passed. Shuffling the playlist.', delete_after=8)
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to shuffle the playlist.', delete_after=8)

    @AuthorCheck.is_privileged()
    @commands.command(aliases=["vol+"])
    async def volup(self, ctx: commands.Context):
        """
            Music|Increases the player's volume by 10 units.
            Note that going above 100 may reduce audio quality.|VIP or administrator permission
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 200:
            return await ctx.send(':grey_exclamation: | Maximum volume reached.', delete_after=8)

        await player.set_volume(vol)
        await ctx.send(f'🎧 🔈 | **Set the volume to {vol}%** 🎧', delete_after=8)

    @AuthorCheck.is_privileged()
    @commands.command(aliases=["vol-"])
    async def voldown(self, ctx: commands.Context):
        """Music|Decreases the player's volume by 10 units.|VIP or administrator permission"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            return await ctx.send(':grey_exclamation: | Player is now muted.', delete_after=8)

        await player.set_volume(vol)
        await ctx.send(f'🎧 🔈 | **Set the volume to {vol}%** 🎧', delete_after=8)

    # @commands.has_permissions(administrator=True)
    # @commands.command(aliases=['eq'])
    # async def equalizer(self, ctx: commands.Context, *, equalizer: str = None):
    #     """Change the players equalizer."""
    #     player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
    #
    #     if not player.is_connected:
    #         return
    #
    #     eqs = {'flat': wavelink.Equalizer.flat(),
    #            'boost': wavelink.Equalizer.boost(),
    #            'metal': wavelink.Equalizer.metal(),
    #            'piano': wavelink.Equalizer.piano()}
    #     options = "\n> ".join(eqs.keys())
    #
    #     if not equalizer:
    #         return await ctx.send(f'Invalid EQ provided. Valid EQs:\n>{options}')
    #
    #     equalizer = eqs.get(equalizer, None)
    #
    #     if not equalizer:
    #         return await ctx.send(f'Invalid EQ provided. Valid EQs:\n>{options}')
    #
    #     await ctx.send(f'Successfully changed equalizer to {equalizer}', delete_after=8)
    #     await player.set_eq(equalizer)

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page: int = 1):
        """Music|Shows the player's queue.|"""
        # todo: add duration to tracks

        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if player.queue.empty():
            return await ctx.send('🎧 **There\'s nothing in the queue! Why not queue something?** 🎧')

        queue_list = player.queue.list()
        queue_len = len(queue_list)

        from math import ceil
        items_per_page = 10
        pages = ceil(queue_len / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        embed_desc = ""
        for index, track in enumerate(queue_list[start:end], start=start):
            requester = track.requester
            if isinstance(track, SimplifiedSpotifyTrack):
                link = track.url
                emoji = "<:spotify:757887449098879006>"
            else:
                print(track.identifier)
                link = track.uri
                emoji = "<:youtube:757887446271918090>"
                if URL_REG.search(str(track.identifier)):
                    emoji = ":grey_question:"

            embed_desc += f'`{index + 1}.` {emoji} [**{track.title}**]({link}) requested by **{requester}**\n'

        embed = discord.Embed(colour=discord.Color.purple(), title=f"Queue | **{queue_len} tracks**",
                              description=f"\n\n{embed_desc}")
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(aliases=["np", "now", "current"])
    async def nowplaying(self, ctx: commands.Context):
        """Music|Shows some stats about the currently playing song.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        await player.invoke_controller()

    @AuthorCheck.is_privileged()
    @commands.command(aliases=["loop"])
    async def repeat(self, ctx):
        """Music|Repeats the current queue until the command is invoked again.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        player.repeat = not player.repeat
        repeat_status = "enabled" if player.repeat else "disabled"
        await ctx.send(f"🎧 🔁 | Repeat **{repeat_status}**. 🎧")

    @commands.command()
    async def seek(self, ctx, *, seconds: int):
        """Music|Seeks to a given position in a track.|"""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_playing:
            return

        track_time = player.position + (seconds * 1000)
        await player.seek(track_time)

        if track_time < 0:
            track_time = 0
        progress = str(datetime.timedelta(milliseconds=track_time)).split(".")[0]
        await ctx.send(f"Moved track to **{progress}**.")

    @commands.command(aliases=["search", "searchmusic", "find"])
    async def findmusic(self, ctx, *, query):
        """Music|Lists the first 10 search results from a given query.|"""

        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        query = 'ytsearch:' + query
        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send('No songs were found with that query. Please try again.', delete_after=8)

        tracks = tracks[:10]
        page = ""
        for index, track in enumerate(tracks, start=1):
            track_title = track.title
            track_uri = track.uri
            track_len = "{}".format(self.bot.funx.seconds2string(track.length / 1000))
            page += f'`{index}.` [{track_title}]({track_uri}) `[{track_len}]`\n'
        embed = discord.Embed(color=discord.Color.purple(), description=page)

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        first = await ctx.send("You can add a song directly to the queue. Just pick a number, onii-chan! :smile:",
                               embed=embed)

        try:
            option = await self.bot.wait_for("message", check=check, timeout=20)
        except asyncio.TimeoutError:
            await ctx.send("You had 20 seconds to decide on a song! Try again?")
        else:
            await first.delete()
            option = option.content
            if not option.isdigit():
                return
            option = int(option)
            if 1 <= option <= 10:
                await ctx.invoke(self.connect)
                track = tracks[option]
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)
                await player.do_next()


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
