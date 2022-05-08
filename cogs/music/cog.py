import asyncio
import disnake
import wavelink
import firebase_admin
import config
from typing import List
from datetime import datetime, timezone
from disnake.ext import commands
from wavelink.ext import spotify
from . import errors, checks, utils, views
from firebase_admin import credentials, db


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hosts = ["lava.link", "lavalink.darrenofficial.com"]
        self.ports = [80, 80]
        self.passw = ["anything as a password", "anything as a password"]
        self.firebase_cred = credentials.Certificate(config.FIREBASE_CONFIG)
        self.firebase_app = firebase_admin.initialize_app(
            self.firebase_cred,
            {"databaseURL": "https://sinful-server-bot-default-rtdb.firebaseio.com/"},
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
    async def on_wavelink_track_end(
        self, player: wavelink.Player, track: wavelink.Track, reason
    ):
        await player.stop()
        if not player.queue.is_empty:
            next_track = player.queue.get()
            print(
                f"TITLE: {next_track.title}| ID:{next_track.id} | IDENTIFIER:{next_track.identifier}"
            )
            await player.play(next_track)
        else:
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
        await player.stop()
        await player.disconnect()

    @checks.check_voice()
    @commands.slash_command()
    async def join(self, interaction: disnake.ApplicationCommandInteraction):
        """Request the bot join your current voice channel"""
        voice = await self.fetchVoice(interaction=interaction)
        print(interaction.author.display_avatar.url)
        await interaction.response.send_message("Joining the channel now!")

    @checks.check_voice()
    @commands.slash_command()
    async def stop(self, interaction: disnake.ApplicationCommandInteraction):
        """Stop music playback and clear queue"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        voice.queue.clear()
        await voice.stop()
        await interaction.response.send_message(
            "Stopping music playback", ephemeral=True
        )

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
        level: int = None,
    ):
        """Adjust the volume of the bot"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        volumeRef = db.reference("settings/volume")
        current_volume = volumeRef.get()
        if not level:
            await interaction.response.send_message(
                f"My current volume is {current_volume}"
            )
        else:
            await voice.set_volume(level)
            settingsRef = db.reference("settings")
            settingsRef.update({"volume": level})
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

        if voice.is_playing() or (voice.is_paused() and not voice.queue.is_empty):
            voice.queue.put(track)
            await interaction.response.send_message("Song queued.", ephemeral=True)
        else:
            await voice.play(track)
            await interaction.response.send_message(
                embed=views.NowPlayingEmbed(track=track, bot=interaction.me),
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
            interaction.response.send_message(
                "Your search query must be a link to a Spotify song, album or playlist."
            )
            return
        elif decoded["type"] is spotify.SpotifySearchType.track:
            track = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"]
            )
            track.set_requester(interaction.author)
            track.set_requested(datetime.now())
        elif decoded["type"] is spotify.SpotifySearchType.album:
            await interaction.response.defer(ephemeral=True)
            tracks = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"]
            )
            for track in tracks:
                track.set_requester(interaction.author)
                track.set_requested(datetime.now())
        elif decoded["type"] is spotify.SpotifySearchType.playlist:
            await interaction.response.defer(ephemeral=True)
            tracks = await spotify.SpotifyTrack.search(
                query=decoded["id"], type=decoded["type"]
            )
            for track in tracks:
                track.set_requester(interaction.author)
                track.set_requested(datetime.now())

        if voice.is_playing() or (voice.is_paused() and not voice.queue.is_empty):
            try:
                voice.queue.put(track)
                await interaction.edit_original_message("Song queued.")
            except:
                voice.queue.extend(tracks)
                await interaction.edit_original_message("Songs added to the queue.")

        else:
            try:
                voice.play(track)
            except:
                voice.play(tracks[0])
                track = tracks.remove(0)
                voice.queue.extend(tracks)
            await voice.play(track)
            await interaction.edit_original_message(
                embed=views.NowPlayingEmbed(track=track, bot=None),
            )

    @join.error
    @play.error
    @stop.error
    @volume.error
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
        await interaction.response.send_message(
            embed=views.NowPlayingEmbed(track=None, bot=interaction.me)
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
            or interaction.author.voice.channel != interaction.me.voice.channel
        ):
            print("Connecting to user voice channel...")
            voice = await interaction.author.voice.channel.connect(cls=wavelink.Player)
            await voice.guild.change_voice_state(
                channel=voice.channel, self_mute=False, self_deaf=True
            )
        ref = db.reference("settings/volume")
        current_volume = ref.get()
        await voice.set_volume(current_volume)
        return voice


def setup(bot):
    bot.add_cog(MusicCog(bot))
