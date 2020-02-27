import math
import re
import discord
import lavalink
from utils.checks import is_vip
from discord.ext import commands

url_rx = re.compile('https?:\\/\\/(?:www\\.)?.+')  # noqa: W605


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.funx = bot.funx

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')  # Host, Port, Password, Region, Name
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        bot.lavalink.add_event_hook(self.track_hook)

    def get_player_mode(self, player):
        shuffle = "disabled"
        if player.shuffle:
            shuffle = "enabled"
        repeat = "disabled"
        if player.repeat:
            repeat = "enabled"
        return f":repeat: {repeat}; :twisted_rightwards_arrows: {shuffle}."

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        else:
            raise commands.CommandInvokeError("You may only use this command in a guild!")
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def track_hook(self, event):
        # todo: announce disconnect
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)
            # Disconnect from the channel -- there's nothing else to play.

    async def connect_to(self, guild_id: int, channel_id: str):
        """ Connects to the given voicechannel ID. A channel_id of `None` means disconnect. """
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)
        # The above looks dirty, we could alternatively use `bot.shards[shard_id].ws` but that assumes
        # the bot instance is an AutoShardedBot.

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            chk = before.channel.members
            if chk:
                if len(chk) == 1 and chk[0].id == self.bot.user.id:
                    player = self.bot.lavalink.players.get(before.channel.guild.id)
                    player.queue.clear()
                    await player.stop()
                    await self.connect_to(before.channel.guild.id, None)
        except Exception as e:
            pass

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """Music|Searches and plays a song from a given query.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results or not results['tracks']:
            return await ctx.send('🎧 **Onii-chan, nothing found!** 🎧')

        embed = discord.Embed(color=discord.Color.purple())
        etup = 0
        if player.current:
            if player.current.stream:
                etup = -1
            else:
                etup += int(player.current.duration / 1000)
        if etup > 0:
            if player.queue:
                for index, track in enumerate(player.queue):
                    if track.stream:
                        etup = -1
                        break
                    elif etup >= 888888:
                        etup = -1
                        break
                    else:
                        etup += int(track.duration / 1000)
            curr = int(player.position / 1000)
            etup = "Estimated time until play: {}".format(self.funx.seconds2string(etup - curr, "en"))
        else:
            etup = ""
        player_mode = self.get_player_mode(player)
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                player.add(requester=ctx.author.id, track=track)

            embed.title = '🎧 **Onii-chan, your playlist is enqueued!** 🎧'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks\n\n  {player_mode}'
        else:
            track = results['tracks'][0]
            embed.title = '🎧 **Onii-chan, your track is enqueued! 🎧\n{}**'.format(etup)
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})\n\n{player_mode}'
            player.add(requester=ctx.author.id, track=track)

        await ctx.send(embed=embed)
        if not player.is_playing:
            await player.play()

    @commands.command()
    async def seek(self, ctx, *, seconds: int):
        """Music|Seeks to a given position in a track.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('🎧 **Not playing.** 🎧')

        track_time = player.position + (seconds * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.utils.format_time(track_time)}**')

    @commands.command(aliases=['forceskip'])
    async def skip(self, ctx):
        """Music|Skips the current track.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        await player.skip()
        await ctx.send('⏭ | Skipped.')

    @commands.command()
    async def stop(self, ctx):
        """Music|Stops the player and clears its queue.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('Not playing.')

        player.queue.clear()
        await player.stop()
        await ctx.send('⏹ | Stopped.')

    @commands.command(aliases=['np', 'now'])
    async def nowplaying(self, ctx):
        """Music|Shows some stats about the currently playing song.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

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
        embed = discord.Embed(color=discord.Color.blurple(),
                              title=status, description=song)
        await ctx.send(embed=embed)

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page: int = 1):
        """Music|Shows the player's queue.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send('🎧 **There\'s nothing in the queue! Why not queue something?** 🎧')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

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
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('🎧 **Not playing.** 🎧')

        if player.paused:
            await player.set_pause(False)
            await ctx.send('🎧 ⏯ **| Resumed** 🎧')
        else:
            await player.set_pause(True)
            await ctx.send('🎧 ⏯ **| Paused** 🎧')

    @commands.command(aliases=['vol'])
    @is_vip()
    async def volume(self, ctx, volume: int = None):
        """Music|Changes the player's volume.(0-1000)|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not volume:
            return await ctx.send(f'🔈 | {player.volume}%')

        await player.set_volume(volume)
        await ctx.send(f'🎧 🔈 | **Set to {player.volume}%** 🎧')

    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        """Music|Shuffles the player's queue.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send('🎧 **Nothing playing.** 🎧')

        player.shuffle = not player.shuffle
        await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'))

    @commands.command(aliases=['loop'])
    @is_vip()
    async def repeat(self, ctx):
        """Music|Repeats the current song until the command is invoked again.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            return await ctx.send('🎧 **Nothing playing.** 🎧')

        player.repeat = not player.repeat
        await ctx.send('🎧 🔁 **| Repeat** 🎧 ' + ('enabled' if player.repeat else 'disabled'))

    @commands.command()
    async def remove(self, ctx, index: int):
        """Music|Removes an item from the player's queue with the given index.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('Nothing queued.')

        if index > len(player.queue) or index < 1:
            return await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}')

        removed = player.queue.pop(index - 1)  # Account for 0-index.

        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.command(aliases=["search", "searchmusic", "find"])
    async def findmusic(self, ctx, *, query):
        """Music|Lists the first 10 search results from a given query.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)
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
            track_len = "{}".format(self.funx.seconds2string(track["info"]["length"] / 1000, "en"))
            o += f'`{index}.` [{track_title}]({track_uri}) `[{track_len}]`\n'
        embed = discord.Embed(color=discord.Color.purple(), description=o)

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        try:
            second = await ctx.send(embed=embed)
            first = await ctx.send("You can add a song directly to the queue. Just pick a number, onii-chan! :smile:")
            cf_mes = await self.bot.wait_for("message", check=check, timeout=30)
            if cf_mes:
                await first.delete()
                await second.delete()
                cont = cf_mes.content
                if str.isdigit(cont):
                    cont = int(cont)
                    if 1 <= cont <= 10:
                        await ctx.invoke(self.play, query=resp[cont])
                    else:
                        raise Exception
                else:
                    raise Exception
        except Exception as e:
            await ctx.send("You haven't picked a right number. Why are you like this, onii-chan?")
            print(e)
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

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """Music|Disconnects the player from the voice channel and clears its queue.|"""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_connected:
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await ctx.send('You\'re not in my voicechannel!')

        player.queue.clear()
        await player.stop()
        await self.connect_to(ctx.guild.id, None)
        await ctx.send('*⃣ | Disconnected.')

    async def ensure_voice(self, ctx):
        """This check ensures that the bot and command author are in the same voicechannel."""
        try:
            # Create returns a player if one exists, otherwise creates.
            player = self.bot.lavalink.players.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        except Exception as e:
            print(e)
            raise commands.CommandInvokeError("There's been an error connecting to a voice channel.")
        no_connect = ctx.command.name in ["lyrics", "queue", "now"]

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not no_connect:
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


def setup(bot):
    bot.add_cog(Music(bot))
