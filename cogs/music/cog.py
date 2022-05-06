import asyncio
import disnake
import wavelink
import firebase_admin
import config
from typing import List
from disnake.ext import commands
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
            await player.play(next_track)
        else:
            time = 0
            while True:
                print(time)
                await asyncio.sleep(1)
                time += 1
                if player.is_playing() and not player.is_paused():
                    time = 0
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
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        search: str,
    ):
        """Plays the song that matches the given search query."""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)
        print(f"Title: {track.title}/n Thumbnail: {track.title}")

        if voice.is_playing() or (voice.is_paused() and not voice.queue.is_empty):
            print("Some songs ahead.")
            voice.queue.put(track)
            await interaction.response.send_message("Song queued.")
        else:
            print("No songs yet.")
            await voice.play(track)
            await interaction.response.send_message(
                embed=views.NowPlayingEmbed(track, interaction.author),
            )

    @checks.check_voice()
    @commands.slash_command()
    async def stop(self, interaction: disnake.ApplicationCommandInteraction):
        """Stops the song that is currently playing"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        voice.stop()
        await interaction.response.send_message("Stopping current song.")

    @checks.check_voice()
    @commands.slash_command()
    async def volume(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        level: int = None,
    ):
        """Adjust the volume of the bot"""
        voice: wavelink.Player = await self.fetchVoice(interaction=interaction)
        current_volume = int(voice.volume)
        if not level:
            await interaction.response.send_message(
                f"My current volume is {current_volume}"
            )
        else:
            await voice.set_volume(level)
            await interaction.response.send_message(
                f"Volume changed from {current_volume} to {level}"
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
