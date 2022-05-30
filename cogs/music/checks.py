import disnake, wavelink, logging
from . import errors
from disnake.ext import commands


def check_voice():
    def predicate(interaction: disnake.ApplicationCommandInteraction):
        if not interaction.author.voice:
            logging.warning(
                f"{interaction.author.display_name}(ID:{interaction.author.id}) triggered NoVoiceConnection error."
            )
            raise errors.NoVoiceConnection()

        try:
            if interaction.author.voice.channel != interaction.me.voice.channel:
                voiceClient: wavelink.Player = disnake.utils.get(
                    interaction.bot.voice_clients, guild=interaction.guild
                )
                if voiceClient.is_playing():
                    logging.warning(
                        f"{interaction.author.display_name}(ID:{interaction.author.id}) triggered DifferentVoiceChannel error."
                    )
                    raise errors.DifferentVoiceChannel()
        except errors.DifferentVoiceChannel:
            raise errors.DifferentVoiceChannel
        except Exception as e:
            logging.warning(
                f"{interaction.author.display_name}(ID:{interaction.author.id}) triggered an exception in check_voice: {e}"
            )

        return True

    return commands.check(predicate)


def is_creator():
    def predicate(interaction: disnake.ApplicationCommandInteraction):
        if interaction.author.id != 329109742742011904:
            logging.warning(
                f"{interaction.author.display_name}(ID:{interaction.author.id}) triggered NotMyCreator error."
            )
            raise errors.NotMyCreator()
        return True

    return commands.check(predicate)
