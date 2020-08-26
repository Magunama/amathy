import re
import discord
import lavalink
import asyncio
from utils.checks import AuthorCheck
from discord.ext import commands
from math import ceil

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        else:
            raise commands.CommandInvokeError("You may only use this command in a guild!")
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        should_connect = ctx.command.name in ("play", "findmusic")

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('You need to be in my voicechannel.')
            else:
                vchan_obj = self.bot.get_channel(int(player.channel_id))
                if not self.bot.user in vchan_obj.members:
                    # bot is not connected in vc but player is
                    player.store('channel', ctx.channel.id)
                    await self.connect_to(ctx.guild.id, str(ctx.author.voice.channel.id))

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # Disconnect from the channel -- there's nothing else to play.
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: str):
        """ Connects to the given voicechannel ID. A channel_id of `None` means disconnect. """
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)
        # The above looks dirty, we could alternatively use `bot.shards[shard_id].ws` but that assumes
        # the bot instance is an AutoShardedBot.

    @staticmethod
    def get_player_mode(player):
        shuffle = "disabled"
        if player.shuffle:
            shuffle = "enabled"
        repeat = "disabled"
        if player.repeat:
            repeat = "enabled"
        return f":repeat: {repeat}; :twisted_rightwards_arrows: {shuffle}."

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        before_chan = before.channel
        if before_chan:
            before_members = before_chan.members
            if len(before_members) == 1 and before_members[0].id == self.bot.user.id:
                player = self.bot.lavalink.player_manager.get(before.channel.guild.id)
                player.queue.clear()
                await player.stop()
                await self.connect_to(before.channel.guild.id, None)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """Music|Searches and plays a song from a given query.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send('🎧 | Sorry, nothing found!')

        embed = discord.Embed(color=discord.Color.blurple())

        estimated_time = 0
        estimated_time_str = ""
        if player.current:
            if player.current.stream:
                estimated_time = -1
            else:
                estimated_time += int(player.current.duration / 1000)
        if estimated_time > 0:
            if player.queue:
                for index, track in enumerate(player.queue):
                    if track.stream:
                        estimated_time = -1
                        break
                    elif estimated_time >= 888888:
                        estimated_time = -1
                        break
                    else:
                        estimated_time += int(track.duration / 1000)
            if estimated_time > 0:
                curr = int(player.position / 1000)
                estimated_time_str = "Estimated time until play: {}".format(self.bot.funx.seconds2string(estimated_time - curr, "en"))
        player_mode = self.get_player_mode(player)

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = '🎧 | Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks\n\n{player_mode}'
        else:
            track = results['tracks'][0]
            embed.title = f'🎧 | Track Enqueued\n{estimated_time_str}'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})\n\n{player_mode}'

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """Music|Disconnects the player from the voice channel and clears its queue.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!')

        player.queue.clear()
        await player.stop()
        await self.connect_to(ctx.guild.id, None)
        await ctx.send('*⃣ | Disconnected.')

    @commands.command()
    async def seek(self, ctx, *, seconds: int):
        """Music|Seeks to a given position in a track.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('🎧 **Not playing.** 🎧')

        track_time = player.position + (seconds * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.utils.format_time(track_time)}**')

    @commands.command(aliases=['skip'])
    async def skiptrack(self, ctx):
        """Music|Skips the current track.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        await player.skip()
        await ctx.send('⏭ | Skipped.')

    @commands.command(aliases=["stop"])
    async def stopplayer(self, ctx):
        """Music|Stops the player and clears its queue.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Stopped.')

    @commands.command(aliases=['np', 'now'])
    async def nowplaying(self, ctx):
        """Music|Shows some stats about the currently playing song.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.current:
            return await ctx.send('Nothing playing.')

        position = lavalink.utils.format_time(player.position)
        if player.current.stream:
            duration = '🔴 LIVE'
        else:
            duration = lavalink.utils.format_time(player.current.duration)
        requesterid = player.current.requester
        requester = self.bot.get_user(requesterid).name
        player_mode = self.get_player_mode(player)
        song = f'**[{player.current.title}]({player.current.uri})**\nrequested by **{requester}**\n({position}/{duration})\n\n{player_mode}'

        status = "🎧 Song is playing 🎧"
        if player.paused:
            status = "🎧 Song is paused 🎧"
        embed = discord.Embed(color=discord.Color.blurple(), title=status, description=song)
        await ctx.send(embed=embed)

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page: int = 1):
        """Music|Shows the player's queue.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send('🎧 **There\'s nothing in the queue! Why not queue something?** 🎧')

        items_per_page = 10
        pages = ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''
        for index, track in enumerate(player.queue[start:end], start=start):
            requesterid = track.requester
            requester = self.bot.get_user(requesterid).name
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri}) requested by **{requester}**\n'

        player_mode = self.get_player_mode(player)
        embed = discord.Embed(colour=discord.Color.purple(), title=f"**{len(player.queue)} tracks**",
                              description=f'\n\n{queue_list}\n{player_mode}')
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(aliases=['resume'])
    async def pause(self, ctx):
        """Music|Pauses/Resumes the current track.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('🎧 **Not playing.** 🎧')

        if player.paused:
            await player.set_pause(False)
            await ctx.send('🎧 ⏯ **| Resumed** 🎧')
        else:
            await player.set_pause(True)
            await ctx.send('🎧 ⏯ **| Paused** 🎧')

    @AuthorCheck.is_vip()
    @commands.command(aliases=['vol'])
    async def volume(self, ctx, volume: int = None):
        """Music|Changes the player's volume.(0-1000)|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not volume:
            return await ctx.send(f'🔈 | {player.volume}%')

        await player.set_volume(volume)
        await ctx.send(f'🎧 🔈 | **Set to {player.volume}%** 🎧')

    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        """Music|Shuffles the player's queue.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('🎧 **Nothing playing.** 🎧')

        player.shuffle = not player.shuffle
        await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'))

    @AuthorCheck.is_vip()
    @commands.command(aliases=['loop'])
    async def repeat(self, ctx):
        """Music|Repeats the current song until the command is invoked again.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('🎧 **Nothing playing.** 🎧')

        player.repeat = not player.repeat
        await ctx.send('🎧 🔁 **| Repeat** 🎧 ' + ('enabled' if player.repeat else 'disabled'))

    @commands.command()
    async def remove(self, ctx, index: int):
        """Music|Removes an item from the player's queue with the given index.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send('Nothing queued.')
        if index > len(player.queue) or index < 1:
            return await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}')
        removed = player.queue.pop(index - 1)  # Account for 0-index.
        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.command(aliases=["search", "searchmusic", "find"])
    async def findmusic(self, ctx, *, query):
        """Music|Lists the first 10 search results from a given query.|"""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not query.startswith('ytsearch:') and not query.startswith('scsearch:'):
            query = 'ytsearch:' + query

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('Nothing found.')

        tracks = results['tracks'][:10]  # First 10 results

        o = ''
        resp = dict()
        for index, track in enumerate(tracks, start=1):
            track_title = track["info"]["title"]
            track_uri = track["info"]["uri"]
            resp[index] = track_uri
            track_len = "{}".format(self.bot.funx.seconds2string(track["info"]["length"] / 1000, "en"))
            o += f'`{index}.` [{track_title}]({track_uri}) `[{track_len}]`\n'
        embed = discord.Embed(color=discord.Color.purple(), description=o)

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        first = await ctx.send("You can add a song directly to the queue. Just pick a number, onii-chan! :smile:", embed=embed)

        try:
            cf_mes = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("You had 30 seconds to decide on a song! Try again!")
        else:
            if cf_mes:
                await first.delete()
                cont = cf_mes.content
                if str.isdigit(cont):
                    cont = int(cont)
                    if 1 <= cont <= 10:
                        return await ctx.invoke(self.play, query=resp[cont])
            await ctx.send("You haven't picked a right number. Why are you like this? :confused:")
        finally:
            if player.current:
                return
            if len(player.queue) > 0:
                return
            await player.stop()
            await self.connect_to(ctx.guild.id, None)

    # @commands.command(aliases=['pv'])
    # async def previous(self, ctx):
    #     """ Plays the previous song. """
    #     player = self.bot.lavalink.players.get(ctx.guild.id)
    #
    #     try:
    #         await player.play_previous()
    #     except lavalink.NoPreviousTrack:
    #         await ctx.send('🎧 **There is no previous song to play.** 🎧')


def setup(bot):
    bot.add_cog(Music(bot))
