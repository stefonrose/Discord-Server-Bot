from enum import Enum
from . import checks, views
from firebase_admin import db
from datetime import datetime
from typing import List, Union
from wavelink.ext import spotify
from disnake.ext import commands, tasks
from urllib.parse import parse_qs, urlparse
import re, config, disnake, asyncio, logging, wavelink, validators


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hosts = ["lava.link", "lavalink.darrenofficial.com"]
        self.ports = [80, 80]
        self.passw = ["anything as a password", "anything as a password"]
        bot.loop.create_task(self.connect_nodes(1))
        self.idle_bot.start()

    async def connect_nodes(self, index: int):
        """Connect to Lavalink node"""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=self.hosts[index],
            port=self.ports[index],
            password=self.passw[index],
            spotify_client=spotify.SpotifyClient(
                client_id=config.SPOTIFY_CLIENT_ID,
                client_secret=config.SPOTIFY_CLIENT_SECRET,
            ),
        )

    @tasks.loop(minutes=5)
    async def idle_bot(self):
        players: List[wavelink.Player] = self.bot.voice_clients
        if len(players) > 0:
            for player in players:
                if (
                    not player.is_playing()
                    and not player.is_paused()
                    and player.queue.is_empty
                ):
                    await player.disconnect()

    @idle_bot.before_loop
    async def before_idle_bot(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Node connection event."""
        self.node = node
        logging.info(f"Node: <{node.identifier}> is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, player: wavelink.Player, track: wavelink.Track
    ):
        """Edit now-playing & queue when song starts playing"""
        await self.edit_now_playing(guild=player.guild, track=track)
        await asyncio.sleep(5)
        await self.edit_queue(player=player, guild=player.guild)

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track: wavelink.Track, reason
    ):
        """When song ends, checks for next song in queue and plays it
        If there is no other song in the queue, clear the now playing message & start idle counter
        """
        await player.stop()
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)
        else:
            await self.edit_now_playing(guild=player.guild)
            await asyncio.sleep(5)
            await self.edit_queue(player=player, guild=player.guild)

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, player: wavelink.Player, reason, code):
        """Stops the player and disconnects if the socket connection is lost"""
        await player.stop()
        await player.disconnect()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ):
        player = await self.check_voice(member.guild)
        if member.id == member.guild.me.id:
            if before.channel is not None:
                await self.edit_now_playing(guild=member.guild)
                await asyncio.sleep(5)
                await self.edit_queue(guild=member.guild, empty=True)
        else:
            if after.channel is None and player is not None:
                if len(before.channel.members) == 1:
                    await player.disconnect()

    @checks.check_voice()
    @commands.slash_command()
    async def join(self, interaction: disnake.ApplicationCommandInteraction):
        """Have the bot join your current voice channel."""
        voice = await self.join_voice(interaction=interaction)
        response = f"Joining the channel now! {config.BOT_ACK}"
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.slash_command()
    async def leave(self, interaction: disnake.ApplicationCommandInteraction):
        """Have the bot leave your current voice channel."""
        voice = await self.check_voice(guild=interaction.guild)
        if voice is not None:
            response = "Leaving the voice channel now."
            await voice.disconnect()
        else:
            response = "I'm not connected to your voice channel right now."
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command()
    async def pause(self, interaction: disnake.ApplicationCommandInteraction):
        """Pause and resume music playback. Keeps queue!"""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if voice.is_paused():
            await voice.resume()
            await self.edit_now_playing(guild=interaction.guild, track=voice.track)
            response = "Music playback resumed."
        elif voice.is_playing():
            await voice.pause()
            await self.edit_now_playing(
                guild=interaction.guild, track=voice.track, pause=True
            )
            response = "Music playback paused."
        else:
            response = "No music is playing or paused."
        await interaction.response.send_message(content=response)

    @checks.check_voice()
    @commands.slash_command()
    async def stop(self, interaction: disnake.ApplicationCommandInteraction):
        """Stop music playback. Clears queue!"""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if not voice.is_playing() and not voice.is_paused() and voice.queue.is_empty:
            response = "There is no music playing or queued!"
        else:
            voice.queue.clear()
            await voice.stop()
            response = "Stopping music playback and clearing queue!"
        await interaction.response.send_message(content=response)

    @checks.check_voice()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.slash_command()
    async def skip(self, interaction: disnake.ApplicationCommandInteraction):
        """Stops the currently song and plays the next song in the queue (If it exists)."""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if not voice.is_playing() and not voice.is_paused() and voice.queue.is_empty:
            response = "There is no music playing or queued!"
        else:
            await voice.stop()
            response = "Skipping to the next track!"
        await interaction.response.send_message(content=response)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.slash_command()
    async def volume(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        level: commands.Range[0, 100] = None,
    ):
        """
        Display or adjust the volume of the bot.

        Parameters
        ----------
        level: :class:`int`
            The level to change the volume to (0-100)
        """
        voice = await self.check_voice(guild=interaction.guild)
        volumeRef = db.reference(f"{interaction.guild_id}/properties/volume")
        current_volume = volumeRef.get()
        if not level:
            response = f"My current volume is {current_volume}. {config.BOT_ACK}"
        else:
            try:
                await voice.set_volume(level)
            except:
                logging.debug("Supressed exception in '/volume'")
            propertiesRef = db.reference(f"{interaction.guild_id}/properties")
            propertiesRef.update({"volume": level})
            response = (
                f"Volume changed from {current_volume} to {level}. {config.BOT_ACK}"
            )
        await interaction.response.send_message(content=response)

    @checks.check_voice()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.slash_command()
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        search: str,
    ):
        """
        Plays the song that matches the given search query.

        Parameters
        ----------
        search: :class:`str`
            A song title, youtube or spotify link
        """
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        await interaction.response.defer(ephemeral=True)
        if validators.url(search):
            linkInfo = self.link_type(search)
            match linkInfo["type"]:
                case Music.youtube:
                    match linkInfo["data"]:
                        case Music.youtubeVideo:
                            track = await wavelink.YouTubeTrack.search(
                                query=search, return_first=True
                            )
                            self.save_track(inter=interaction, track=track, voice=voice)
                            await voice.queue.put_wait(track)
                            await interaction.edit_original_message(
                                content=f"{config.BOT_ACK}",
                                embed=views.TrackEnqueuedEmbed(track=track),
                            )
                            track = None
                        case Music.youtubePlaylist:
                            playlist = await self.node.get_playlist(
                                wavelink.YouTubePlaylist, search
                            )
                            for track in playlist.tracks:
                                self.save_track(
                                    inter=interaction, track=track, voice=voice
                                )
                                await voice.queue.put_wait(track)
                            message = f"{len(playlist.tracks)} songs added to the queue. {config.BOT_ACK}"
                            await interaction.edit_original_message(content=message)
                            track = None

                case Music.spotify:
                    spotifyInfo = linkInfo["data"]
                    match spotifyInfo["type"]:
                        case spotify.SpotifySearchType.track:
                            track = await spotify.SpotifyTrack.search(
                                query=spotifyInfo["id"],
                                type=spotifyInfo["type"],
                                return_first=True,
                            )
                            self.save_track(inter=interaction, track=track, voice=voice)
                            await voice.queue.put_wait(track)
                            await interaction.edit_original_message(
                                content=f"{config.BOT_ACK}",
                                embed=views.TrackEnqueuedEmbed(track=track),
                            )
                            track = None
                        case spotify.SpotifySearchType.album:
                            tracks = await spotify.SpotifyTrack.search(
                                query=spotifyInfo["id"], type=spotifyInfo["type"]
                            )
                            for track in tracks:
                                self.save_track(
                                    inter=interaction, track=track, voice=voice
                                )
                                await voice.queue.put_wait(track)
                            message = f"{len(tracks)} songs added to the queue. {config.BOT_ACK}"
                            await interaction.edit_original_message(content=message)
                            track = None

                        case spotify.SpotifySearchType.playlist:
                            tracks = await spotify.SpotifyTrack.search(
                                query=spotifyInfo["id"], type=spotifyInfo["type"]
                            )
                            for track in tracks:
                                self.save_track(
                                    inter=interaction, track=track, voice=voice
                                )
                                await voice.queue.put_wait(track)
                            message = f"{len(tracks)} songs added to the queue. {config.BOT_ACK}"
                            await interaction.edit_original_message(content=message)
                            track = None
                case None:
                    message = "Only YouTube and Spotify links are supported."
                    await interaction.edit_original_message(content=message)
        else:
            track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
            self.save_track(inter=interaction, track=track, voice=voice)
            await voice.queue.put_wait(track)
            await interaction.edit_original_message(
                content=f"{config.BOT_ACK}",
                embed=views.TrackEnqueuedEmbed(track=track),
            )
            track = None

        if not voice.is_playing() and not voice.is_paused():
            track = await voice.queue.get_wait()
            await voice.play(track)
        if not voice.is_playing() and voice.is_paused():
            await voice.resume()

    @checks.is_creator()
    @commands.slash_command()
    async def now_playing(
        self, interaction: disnake.ApplicationCommandInteraction, default: bool = False
    ):
        """Displays new now playing message. Requires permissions."""
        np_embed = views.NowPlayingEmbed(track=None, bot=interaction.me)
        await interaction.response.send_message(embed=np_embed)
        message: disnake.InteractionMessage = await interaction.original_message()
        channel: disnake.TextChannel = message.channel
        if default:
            playingRef = db.reference(f"{interaction.guild_id}/properties")
            playingRef.update(
                {"now_playing": {"message_id": message.id, "channel_id": channel.id}}
            )

    @checks.is_creator()
    @commands.slash_command()
    async def show_queue(
        self, interaction: disnake.ApplicationCommandInteraction, default: bool = False
    ):
        """Displays new queue message. Requires permissions."""
        # voice: wavelink.Player = await self.join_voice(interaction=interaction)
        embeds = await self.populate_embeds(player=None, bot=interaction.me, empty=True)
        await interaction.response.send_message(
            content="No songs in queue.", embeds=embeds
        )
        message: disnake.InteractionMessage = await interaction.original_message()
        channel: disnake.TextChannel = message.channel
        if default:
            queueRef = db.reference(f"{interaction.guild_id}/properties")
            queueRef.update(
                {"queue": {"message_id": message.id, "channel_id": channel.id}}
            )

    ### Helper functions

    async def join_voice(self, interaction: disnake.ApplicationCommandInteraction):
        voice = await self.check_voice(guild=interaction.guild)
        if not voice:
            voice = await interaction.author.voice.channel.connect(cls=wavelink.Player)
            await voice.guild.change_voice_state(channel=voice.channel, self_deaf=True)
        ref = db.reference(f"{interaction.guild_id}/properties/volume")
        current_volume = ref.get()
        await voice.set_volume(current_volume)
        return voice

    async def check_voice(self, guild: disnake.Guild) -> Union[wavelink.Player, None]:
        voice: wavelink.Player = disnake.utils.get(self.bot.voice_clients, guild=guild)
        return voice

    async def populate_embeds(
        self,
        *,
        player: wavelink.Player = None,
        bot: disnake.Member,
        empty: bool = False,
    ) -> List[disnake.Embed]:
        embeds = []

        if empty:
            pass
        else:
            songs_count = min(player.queue.count, 10)
            queue_copy: wavelink.WaitQueue = player.queue.copy()

            empty_count = max((10 - songs_count), 0)
            embed_count = 0

            for i in range(songs_count):
                embed_count += 1
                track = await queue_copy.get_wait()
                trackReferences = db.reference(
                    f"{player.guild.id}/tracks/{track.identifier}"
                ).get()
                requester = await player.guild.get_or_fetch_member(
                    trackReferences["requester"]
                )
                requested = datetime.fromtimestamp(trackReferences["requested"])
                thumbnail = trackReferences["thumbnail"]

                embeds.append(
                    views.QueueItem(
                        count=embed_count,
                        requested=requested,
                        requester=requester,
                        thumbnail=thumbnail,
                        track=track,
                    )
                )

        embeds.reverse()
        return embeds

    async def edit_now_playing(
        self, *, guild: disnake.Guild, track: wavelink.Track = None, pause: bool = False
    ):
        np_ch_id = db.reference(f"{guild.id}/properties/now_playing/channel_id").get()
        np_msg_id = db.reference(f"{guild.id}/properties/now_playing/message_id").get()
        channel = guild.get_channel(np_ch_id)
        now_playing_message = await channel.fetch_message(np_msg_id)

        if track is not None:
            trackRefs = db.reference(f"{guild.id}/tracks/{track.identifier}").get()
            requester = await guild.get_or_fetch_member(trackRefs["requester"])
            requested = datetime.fromtimestamp(trackRefs["requested"])
            thumbnail = trackRefs["thumbnail"]

            await now_playing_message.edit(
                embed=views.NowPlayingEmbed(
                    track=track,
                    requester=requester,
                    requested=requested,
                    thumbnail=thumbnail,
                    pause=pause,
                )
            )
        else:
            await now_playing_message.edit(embed=views.NowPlayingEmbed(bot=guild.me))

    async def edit_queue(
        self,
        *,
        guild: disnake.Guild = None,
        player: wavelink.Player = None,
        empty: bool = False,
    ):
        queue_ch_id = db.reference(f"{guild.id}/properties/queue/channel_id").get()
        queue_msg_id = db.reference(f"{guild.id}/properties/queue/message_id").get()
        channel = guild.get_channel(queue_ch_id)
        queue_message = await channel.fetch_message(queue_msg_id)
        if empty:
            if len(queue_message.embeds) == 0:
                return
            embeds = await self.populate_embeds(bot=guild.me, empty=empty)
            await queue_message.edit(content="No songs in queue.", embeds=embeds)
        else:
            embeds = await self.populate_embeds(
                player=player, bot=guild.me, empty=empty
            )
            if embeds == queue_message.embeds:
                return
            if len(embeds) == 0:
                await queue_message.edit(content="No songs in queue.", embeds=embeds)
                return
            await queue_message.edit(content="", embeds=embeds)

    def save_track(
        self,
        *,
        inter: disnake.ApplicationCommandInteraction,
        track: wavelink.YouTubeTrack,
        voice: wavelink.Player,
    ):
        dbReference = f"{voice.guild.id}/tracks/{track.identifier}"
        songRef = db.reference(dbReference)
        songRef.update(
            {
                "requester": inter.author.id,
                "requested": datetime.now().timestamp(),
                "thumbnail": track.thumbnail,
            }
        )

    def link_type(self, url: str):
        youtubePattern = re.compile("you")
        spotifyPattern = re.compile("spotify")

        youtubeResult = youtubePattern.search(url)
        spotifyResult = spotifyPattern.search(url)

        if youtubeResult is not None:
            ytQuery = parse_qs(urlparse(url).query, keep_blank_values=True)
            if "v" in ytQuery:
                return {"type": Music.youtube, "data": Music.youtubeVideo}
            if "list" in ytQuery:
                return {"type": Music.youtube, "data": Music.youtubePlaylist}
        elif spotifyResult is not None:
            spotifyInfo = spotify.decode_url(url=url)
            return {"type": Music.spotify, "data": spotifyInfo}
        else:
            return {"type": None}


class Music(Enum):
    youtube = 1
    spotify = 2
    youtubeVideo = 3
    youtubePlaylist = 4


def setup(bot):
    bot.add_cog(MusicCog(bot))
