from enum import Enum
from firebase_admin import db
from datetime import datetime
from discord import app_commands, CustomActivity, PartialEmoji
from . import checks, views, errors
from typing import List, Union, Any
from discord.ext import commands, tasks
from urllib.parse import parse_qs, urlparse
import discord, logging, wavelink, traceback, validators


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())
        self.kick.start()

    async def connect_nodes(self):
        """Connect to Lavalink node"""
        await self.bot.wait_until_ready()

        node = wavelink.Node(
            identifier="lavalinkNode",
            uri="http://lavalink:2521",
            password="sinful-server-lava",
            retries=5
        )

        await wavelink.Pool.connect(nodes=[node],client=self.bot)

    @tasks.loop(minutes=5)
    async def kick(self):
        players: List[wavelink.Player] = self.bot.voice_clients
        if len(players) > 0:
            for player in players:
                if (
                    not player.playing
                    and not player.paused
                    and player.queue.is_empty
                ):
                    await player.disconnect()
                    emoji = PartialEmoji.from_str(":crazyeyes:908023063621296170")
                    activity = CustomActivity(name="Watching over the realms.", emoji=emoji)
                    await self.bot.change_presence(activity=activity)
                else:
                    channel = player.channel.name
                    name = f"Streaming in {channel}."
                    activity = CustomActivity(name=name, emoji="🎶")
                    await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.NodeReadyEventPayload):
        """Node connection event."""
        self.node = node.node
        logging.info(f"Node: <{self.node.identifier}> is ready!")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        player = await self.get_voice(member.guild)
        if member.id == member.guild.me.id:
            pass
        else:
            if after.channel is None and player is not None:
                if len(before.channel.members) == 1:
                    await player.disconnect()

    @checks.voice_check()
    @app_commands.command()
    async def join(self, interaction: discord.Interaction):
        """Have the bot join your current voice channel."""
        voice = await self.join_voice(interaction=interaction)
        response = f"Joining the channel now!"
        await interaction.response.send_message(content=response,ephemeral=True)

    @app_commands.command()
    async def connect(self, interaction: discord.Interaction, channel_name: str):
        """Have the bot join the specified voice channel."""
        channels = interaction.guild.voice_channels
        channel = discord.utils.get(channels, name=channel_name)
        await channel.connect(cls=wavelink.Player)
        response = f"Joining the channel now!"
        await interaction.response.send_message(content=response,ephemeral=True)

    @checks.voice_check()
    @app_commands.command()
    async def leave(self, interaction: discord.Interaction):
        """Have the bot leave your current voice channel."""
        voice = await self.get_voice(guild=interaction.guild)
        if voice is not None:
            response = "Leaving the voice channel now."
            await voice.disconnect()
        else:
            response = "I'm not connected to your voice channel right now."
        await interaction.response.send_message(content=response,ephemeral=True)

    @checks.voice_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.command()
    async def pause(self, interaction: discord.Interaction):
        """Pause and resume music playback. Keeps queue!"""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if voice.paused:
            await voice.pause(False)
            response = "Music playback resumed."
        elif voice.playing:
            await voice.pause(True)
            response = "Music playback paused."
        else:
            response = "No music is playing or paused."
        await interaction.response.send_message(content=response,ephemeral=True)

    @checks.voice_check()
    @app_commands.command()
    async def stop(self, interaction: discord.Interaction):
        """Stop music playback. Clears queue!"""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if not voice.playing and not voice.paused and voice.queue.is_empty:
            response = "There is no music playing or queued!"
        else:
            voice.queue.clear()
            await voice.stop()
            response = "Stopping music playback and clearing queue!"
        await interaction.response.send_message(content=response,ephemeral=True)

    @checks.voice_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.command()
    async def skip(self, interaction: discord.Interaction):
        """Stops the currently song and plays the next song in the queue (If it exists)."""
        voice: wavelink.Player = await self.join_voice(interaction=interaction)
        if not voice.playing and not voice.paused and voice.queue.is_empty:
            response = "There is no music playing or queued!"
        else:
            await voice.stop()
            response = "Skipping to the next track!"
        await interaction.response.send_message(content=response,ephemeral=True)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.command()
    async def volume(
        self,
        interaction: discord.Interaction,
        level: app_commands.Range[int, 0, 100] = None,
    ):
        """
        Display or adjust the volume of the bot.

        Parameters
        ----------
        level: :class:`int`
            The level to change the volume to (0-100)
        """
        voice = await self.get_voice(guild=interaction.guild)
        current_volume = voice.volume
        if not level:
            response = f"My current volume is {current_volume}."
        else:
            try:
                await voice.set_volume(level)
            except:
                logging.debug("Supressed exception in '/volume'")
            response = (
                f"Volume changed from {current_volume} to {level}."
            )
        await interaction.response.send_message(content=response, ephemeral=True)

    @checks.voice_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @app_commands.command()
    async def play(
        self,
        interaction: discord.Interaction,
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
        requester = interaction.user
        requested = datetime.now().timestamp()
        
        tracks: wavelink.Search = await wavelink.Playable.search(search, source="ytsearch")
        message = ""
        if not tracks:
            message: str = "Can't find anything with the input given."
        else:
            if type(tracks) is list:
                for track in tracks:
                    track.extras = {"requester": requester.id, "requested": requested}
            else:
                tracks.extras = {"requester": requester.id, "requested": requested}
            
            url = validators.url(search)
            num_tracks = 0
            if not url and type(tracks) is list:
                num_tracks = await voice.queue.put_wait(tracks[0])
                message: str = f"1 song has been added to the queue. Use '/queue' command to view the queue."
            else:
                num_tracks = await voice.queue.put_wait(tracks)
                message: str = f"{num_tracks} song(s) has been added to the queue. Use '/queue' to view the queue."
        
        await interaction.edit_original_response(content=message)

        if not voice.playing and not voice.paused:
            track = await voice.queue.get_wait()
            await voice.play(track)
        if not voice.playing and voice.paused:
            await voice.pause(False)

    @checks.is_creator()
    @app_commands.command()
    async def playing(self, interaction: discord.Interaction):
        """Displays the song that is currently playing."""
        voice = await self.get_voice(guild=interaction.guild)
        if voice is not None:
            current: wavelink.Playable = voice.current
            if current is not None:
                requester = await voice.guild.fetch_member(current.extras.requester)
                requested = datetime.fromtimestamp(current.extras.requested)
                embed = views.NowPlayingEmbed(
                    track=current, requester=requester, requested=requested
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    content="There is no song currently playing.",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                content="There is no song currently playing.",
                ephemeral=True
            )

    @checks.voice_check()
    @app_commands.command()
    async def queue(self, interaction: discord.Interaction):
        """Displays the songs currently queued."""
        await interaction.response.defer(ephemeral=True)
        player = await self.get_voice(guild=interaction.guild)
        embeds = []
        if player is not None:
            if player.queue.is_empty:
                message = "There are currently no songs in the queue."
                await interaction.edit_original_response(content=message)
            else:
                queue = views.QueueEmbed(player.queue)
                embeds.append(queue)
                await interaction.edit_original_response(embeds=embeds)

    ### HELPER FUNCTIONS ###

    async def join_voice(self, interaction: discord.Interaction):
        voice = await self.get_voice(guild=interaction.guild)
        if not voice:
            voice = await interaction.user.voice.channel.connect(cls=wavelink.Player, self_deaf=True)

        await voice.set_volume(15)
        if voice.autoplay is not wavelink.AutoPlayMode.partial:
            voice.autoplay = wavelink.AutoPlayMode.partial
        return voice

    async def get_voice(self, guild: discord.Guild) -> Union[wavelink.Player, None]:
        voice: wavelink.Player = discord.utils.get(self.bot.voice_clients, guild=guild)
        return voice

    ### ERROR HANDLER ###

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        match error:
            case errors.NoVoiceConnection():
                message = "You have to be in a voice channel to use that."
                if interaction.response.is_done():
                    await interaction.edit_original_response(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case errors.DifferentVoiceChannel():
                message = "I'm currently playing music in another channel."
                if interaction.response.is_done():
                    await interaction.edit_original_response(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case errors.NotMyCreator():
                message = "You are not my creator"
                if interaction.response.is_done():
                    await interaction.edit_original_response(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case commands.CommandOnCooldown():
                message = f"There is a cooldown associated with this command. Try again in {error.cooldown.get_retry_after()} seconds."
                if interaction.response.is_done():
                    await interaction.edit_original_response(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case _:
                message = (
                    "An uncaught exception has occured. This problem has been logged."
                )
                if interaction.response.is_done():
                    await interaction.edit_original_response(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

                tb = "".join(traceback.format_exception(error))
                user = await self.bot.fetch_user(self.bot.owner_id)

                try:
                    message = (
                        f"User: {interaction.user.display_name}(ID:{interaction.user.id}) caused an exception\n"
                        f"```py\n{tb}\n```"
                    )
                    await user.send(content=message[:2000])
                    logging.error(tb)
                except Exception as e:
                    logging.error("Unable to send error message to bot owner!")
                    tb = "".join(traceback.format_exception(e))
                    logging.error(tb)


class Music(Enum):
    youtube = 1
    spotify = 2
    youtubeVideo = 3
    youtubePlaylist = 4


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
