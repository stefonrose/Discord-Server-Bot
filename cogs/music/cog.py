import re
import disnake
import wavelink
from typing import List
from disnake.ext import commands


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to Lavalink node"""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(
            bot=self.bot,
            host="lava.link",
            port=80,
            password="anything as a password",
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Node connection event."""
        print(f"Node: <{node.identifier}> is ready!")

    @commands.slash_command()
    async def join(self, interaction: disnake.ApplicationCommandInteraction):
        """Request the bot join your current voice channel"""
        if interaction.author.voice is None:
            await interaction.response.send_message(
                "You have to be in a voice channel to use that."
            )
        else:
            voiceChannel = interaction.author.voice.channel
            voiceClient = await voiceChannel.connect()
            await voiceClient.guild.change_voice_state(
                channel=voiceChannel, self_mute=False, self_deaf=True
            )

            await interaction.response.send_message("Connecting to the channel now.")

    @commands.slash_command()
    async def play(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        search: str,
    ):
        """Plays the song that matches the given search query."""
        if interaction.author.voice.channel is None or interaction.author.voice is None:
            await interaction.response.send_message(
                "You have to be in a voice channel to use that."
            )
            return
        voiceClient = disnake.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not voiceClient:
            voice: wavelink.Player = await interaction.author.voice.channel.connect(
                cls=wavelink.Player
            )
        else:
            voice: wavelink.Player = voiceClient

        track = await wavelink.YouTubeTrack.search(query=search, return_first=True)

        await voice.play(track)


def setup(bot):
    bot.add_cog(MusicCog(bot))
