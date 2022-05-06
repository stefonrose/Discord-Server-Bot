import disnake, wavelink
from . import errors
from disnake.ext import commands


def check_voice():
    def predicate(interaction: disnake.ApplicationCommandInteraction):
        if not interaction.author.voice:
            raise errors.NoVoiceConnection()

        try:
            if interaction.author.voice.channel != interaction.me.voice.channel:
                voiceClient: wavelink.Player = disnake.utils.get(
                    interaction.bot.voice_clients, guild=interaction.guild
                )
                if voiceClient.is_playing():
                    raise errors.DifferentVoiceChannel()
        except errors.DifferentVoiceChannel:
            raise errors.DifferentVoiceChannel
        except:
            pass

        return True

    return commands.check(predicate)
