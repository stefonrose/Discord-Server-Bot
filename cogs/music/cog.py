from typing import List
from pyparsing import empty
from disnake.ext import commands
from wavelink.ext import spotify
from datetime import datetime, timezone
from . import errors, checks, utils, views
from firebase_admin import credentials, db
import config, disnake, asyncio, wavelink, firebase_admin


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hosts = ["lava.link", "lavalink.darrenofficial.com"]
        self.ports = [80, 80]
        self.passw = ["anything as a password", "anything as a password"]
        self.firebase_cred = credentials.Certificate(config.FIREBASE_CONFIG)
        self.firebase_app = firebase_admin.initialize_app(
            self.firebase_cred,
            {
                "databaseURL": "https://sinful-server-bot-default-rtdb.firebaseio.com/",
                "databaseAuthVariableOverride": {"uid": "discord_bot"},
            },
        )
        bot.loop.create_task(self.connect_nodes(1))

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

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Node connection event."""
        print(f"Node: <{node.identifier}> is ready!")

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, player: wavelink.Player, track: wavelink.Track
    ):
        """Edit now-playing & queue when song starts playing"""
        await self.editNowPlaying(guild=player.guild, track=track)
        await asyncio.sleep(5)
        await self.editQueue(player=player, guild=player.guild)

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
            await self.editNowPlaying(guild=player.guild)
            time = 0
            while True:
                print(time)
                await asyncio.sleep(1)
                time += 1
                if player.is_playing() and not player.is_paused():
                    break
                if time == 60:
                    await player.disconnect()
                if not player.is_connected():
                    break

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, player: wavelink.Player, reason, code):
        """Stops the player and disconnects if the socket connection is lost"""
        print(reason, code)
        await player.stop()
        await player.disconnect()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState,
    ):
        if member.id == member.guild.me.id:
            if before.channel is not None:
                await self.editNowPlaying(guild=member.guild)
                await asyncio.sleep(5)
                await self.editQueue(guild=member.guild, empty=True)

    @checks.check_voice()
    @commands.slash_command()
    async def join(self, interaction: disnake.ApplicationCommandInteraction):
        """Request the bot join your current voice channel."""
        voice = await self.fetchVoice(interaction=interaction)
        print(interaction.author.display_avatar.url)
        response = "Joining the channel now!"
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.slash_command()
    async def leave(self, interaction: disnake.ApplicationCommandInteraction):
        """Have the bot leave your current voice channel."""
        voice: wavelink.Player = disnake.utils.get(
            self.bot.voice_clients, guild=interaction.guild
        )
        if voice is not None:
            response = "Leaving the voice channel now."
            voice.disconnect()
        else:
            response = "I'm not connected to your voice channel right now."
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.slash_command()
    async def pause(self, interaction: disnake.ApplicationCommandInteraction):
        """Pause and resume music playback. Keeps queue!"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        if voice.is_paused():
            await voice.resume()
            await self.editNowPlaying(guild=interaction.guild, track=voice.track)
            response = "Music playback resumed."
        elif voice.is_playing():
            await voice.pause()
            await self.editNowPlaying(
                guild=interaction.guild, track=voice.track, pause=True
            )
            response = "Music playback paused."
        else:
            response = "No music is playing or paused."
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.slash_command()
    async def stop(self, interaction: disnake.ApplicationCommandInteraction):
        """Stop music playback. Clears queue!"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        voice.queue.clear()
        await voice.stop()
        response = "Stopping music playback"
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.check_voice()
    @commands.slash_command()
    async def skip(self, interaction: disnake.ApplicationCommandInteraction):
        """Skips to the next track in the queue."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        await voice.stop()
        await interaction.response.send_message(
            "Skipping to the next track!", ephemeral=True
        )

    @checks.check_voice()
    @commands.slash_command()
    async def volume(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        level: commands.Range[0, 100] = None,
    ):
        """Display or adjust the volume of the bot."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)

        volumeRef = db.reference(f"{interaction.guild_id}/properties/volume")
        current_volume = volumeRef.get()
        if not level:
            await interaction.response.send_message(
                f"My current volume is {current_volume}"
            )
        else:
            await voice.set_volume(level)
            propertiesRef = db.reference(f"{interaction.guild_id}/properties")
            propertiesRef.update({"volume": level})
            await interaction.response.send_message(
                f"Volume changed from {current_volume} to {level}"
            )

    @checks.check_voice()
    @commands.slash_command()
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        search: str,
    ):
        """Plays the song that matches the given search query."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        track.set_requester(interaction.author)
        track.set_requested(datetime.now())
        dbReference = f"{voice.guild.id}/tracks/{track.identifier}"
        self.saveRequestInfo(
            dbReference=dbReference,
            track=track,
        )

        if voice.is_playing() or (voice.is_paused() and not voice.queue.is_empty):
            voice.queue.put(track)
            await self.editQueue(player=voice, guild=voice.guild)
            await interaction.response.send_message(
                embed=views.TrackEnqueuedEmbed(track=track), ephemeral=True
            )
        else:
            await voice.play(track)
            await interaction.response.send_message(
                embed=views.TrackEnqueuedEmbed(track=track), ephemeral=True
            )

    @checks.check_voice()
    @commands.slash_command()
    async def spotify(
        self, interaction: disnake.ApplicationCommandInteraction, url: str
    ):
        """Play music using a Spotify playlist or album URL."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        decoded = spotify.decode_url(url=url)
        if not decoded:
            await interaction.response.send_message(
                "Your search query must be a link to a Spotify song, album or playlist."
            )
            return
        elif decoded["type"] is spotify.SpotifySearchType.track:
            print("isTrack")
            track = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"], return_first=True
            )
            track.set_requester(interaction.author)
            track.set_requested(datetime.now())
            dbReference = f"{voice.guild.id}/tracks/{track.identifier}"
            self.saveRequestInfo(
                dbReference=dbReference,
                track=track,
            )
        elif decoded["type"] is spotify.SpotifySearchType.album:
            print("isAlbum")
            await interaction.response.defer(ephemeral=True)
            tracks = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"]
            )
            for track in tracks:
                track.set_requester(interaction.author)
                track.set_requested(datetime.now())
                dbReference = f"{voice.guild.id}/tracks/{track.identifier}"
                self.saveRequestInfo(
                    dbReference=dbReference,
                    track=track,
                )
            track = None

        elif decoded["type"] is spotify.SpotifySearchType.playlist:
            print("isPlaylist")
            await interaction.response.defer(ephemeral=True)
            tracks = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"]
            )
            for track in tracks:
                track.set_requester(interaction.author)
                track.set_requested(datetime.now())
                dbReference = f"{voice.guild.id}/tracks/{track.identifier}"
                self.saveRequestInfo(
                    dbReference=dbReference,
                    track=track,
                )
            track = None

        if voice.is_playing() or (voice.is_paused() and not voice.queue.is_empty):
            if track is not None:
                voice.queue.put(track)
                await interaction.edit_original_message(
                    embed=views.TrackEnqueuedEmbed(track=track),
                )
            elif tracks is not None:
                voice.queue.extend(tracks)
                message = f"{len(tracks)} songs added to the queue."
                await interaction.edit_original_message(content=message)
            await self.editQueue(player=voice, guild=voice.guild)

        else:
            if track is not None:
                print(track)
                await voice.play(track)
                await interaction.edit_original_message(
                    embed=views.TrackEnqueuedEmbed(track=track),
                )
            elif tracks is not None:
                track = tracks.pop(0)
                voice.queue.extend(tracks)
                await voice.play(track)
                message = f"{len(tracks)+1} songs added to the queue."
                await interaction.edit_original_message(content=message)

    @join.error
    @leave.error
    @play.error
    @pause.error
    @stop.error
    @skip.error
    @volume.error
    @spotify.error
    async def voice_error(
        self, interaction: disnake.ApplicationCommandInteraction, error
    ):
        if isinstance(error, errors.NoVoiceConnection):
            await interaction.response.send_message(
                "You have to be in a voice channel to use that.", ephemeral=True
            )
        if isinstance(error, errors.DifferentVoiceChannel):
            await interaction.response.send_message(
                "I'm currently playing music in another channel.", ephemeral=True
            )

    @checks.is_creator()
    @commands.slash_command()
    async def now_playing(
        self, interaction: disnake.ApplicationCommandInteraction, default: bool = False
    ):
        """Displays new now playing message. Reequires permissions."""
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
        """Displays new queue message. Reequires permissions."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        embeds = await self.populateEmbeds(player=voice, bot=interaction.me)
        await interaction.response.send_message(content="", embeds=embeds)
        message: disnake.InteractionMessage = await interaction.original_message()
        channel: disnake.TextChannel = message.channel
        if default:
            queueRef = db.reference(f"{interaction.guild_id}/properties")
            queueRef.update(
                {"queue": {"message_id": message.id, "channel_id": channel.id}}
            )

    @now_playing.error
    async def creator_error(
        self, interaction: disnake.ApplicationCommandInteraction, error
    ):
        if isinstance(error, errors.NotMyCreator):
            await interaction.response.send_message(
                "You are not my creator", ephemeral=True
            )

    async def fetchVoice(self, interaction: disnake.ApplicationCommandInteraction):
        voice: wavelink.Player = disnake.utils.get(
            self.bot.voice_clients, guild=interaction.guild
        )
        if (
            not voice
            # or interaction.author.voice.channel != interaction.me.voice.channel
        ):
            print("Connecting to user voice channel...")
            voice = await interaction.author.voice.channel.connect(cls=wavelink.Player)
            await voice.guild.change_voice_state(channel=voice.channel, self_deaf=True)
        ref = db.reference(f"{interaction.guild_id}/properties/volume")
        current_volume = ref.get()
        await voice.set_volume(current_volume)
        return voice

    def saveRequestInfo(self, *, dbReference: str, track: wavelink.YouTubeTrack):
        songRef = db.reference(dbReference)
        songRef.update(
            {
                "requester": track.requester.id,
                "requested": track.requested.timestamp(),
                "thumbnail": track.thumbnail,
            }
        )

    async def populateEmbeds(
        self,
        *,
        player: wavelink.Player = None,
        bot: disnake.Member,
        empty: bool = False,
    ) -> List[disnake.Embed]:
        embeds = []

        if empty:
            # for i in range(1, 11):
            #    embeds.append(views.EmptyQueueItem(count=1, bot=bot))
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
            # for i in range(empty_count):
            #     embed_count += 1
            #     embeds.append(views.EmptyQueueItem(count=embed_count, bot=bot))

        embeds.reverse()
        return embeds

    async def editNowPlaying(
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

    async def editQueue(
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
            embeds = await self.populateEmbeds(bot=guild.me, empty=empty)
            await queue_message.edit(content="No songs in queue.", embeds=embeds)
        else:
            embeds = await self.populateEmbeds(player=player, bot=guild.me, empty=empty)
            if queue_message.embeds == embeds:
                return
            await queue_message.edit(content="", embeds=embeds)


def setup(bot):
    bot.add_cog(MusicCog(bot))
