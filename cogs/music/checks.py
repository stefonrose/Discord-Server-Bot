from . import errors
import discord, wavelink, logging
from discord import app_commands, Interaction


def voice_check():
    def predicate(interaction: Interaction):
        if not interaction.user.voice:
            logging.warning(
                f"{interaction.user.display_name}(ID:{interaction.user.id}) triggered NoVoiceConnection error."
            )
            raise errors.NoVoiceConnection()

        try:
            channel = interaction.user.voice.channel
            bot = interaction.client.user
            if bot not in channel.members:
                voiceClient: wavelink.Player = discord.utils.get(
                    interaction.client.voice_clients, guild=interaction.guild
                )
                if voiceClient.channel != channel:
                    logging.warning(
                        f"{interaction.user.display_name}(ID:{interaction.user.id}) triggered DifferentVoiceChannel error."
                    )
                    raise errors.DifferentVoiceChannel()
        except errors.DifferentVoiceChannel:
            raise errors.DifferentVoiceChannel()
        except errors.NoVoiceConnection:
            raise errors.NoVoiceConnection()
        except Exception as e:
            logging.debug(
                f"{interaction.user.display_name}(ID:{interaction.user.id}) triggered an exception in check_voice: {e}"
            )

        return True

    return app_commands.check(predicate)


def is_creator():
    def predicate(interaction: Interaction):
        if interaction.user.id != 329109742742011904:
            logging.warning(
                f"{interaction.user.display_name}(ID:{interaction.user.id}) triggered NotMyCreator error."
            )
            raise errors.NotMyCreator()
        return True

    return app_commands.check(predicate)
