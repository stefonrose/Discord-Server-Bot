import disnake, logging, traceback
from ..error import errors
from disnake.ext import commands


class ErrorHandlerCog(commands.Cog, name="ErrorHandler"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        error: commands.CommandError,
    ):

        match error:
            case errors.NoVoiceConnection():
                message = "You have to be in a voice channel to use that."
                if interaction.response.is_done():
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case errors.DifferentVoiceChannel():
                message = "I'm currently playing music in another channel."
                if interaction.response.is_done():
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case errors.NotMyCreator():
                message = "You are not my creator"
                if interaction.response.is_done():
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case commands.CommandOnCooldown():
                message = f"There is a cooldown associated with this command. Try again in {error.cooldown.get_retry_after()} seconds."
                if interaction.response.is_done():
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            case _:
                message = (
                    "An uncaught exception has occured. This problem has been logged."
                )
                if interaction.response.is_done():
                    await interaction.edit_original_message(content=message)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

                tb = "".join(traceback.format_exception(error))
                user = self.bot.get_user(self.bot.owner_id)

                try:
                    message = (
                        f"User: {interaction.author.display_name}(ID:{interaction.author.id}) caused an exception\n"
                        f"Command: {interaction.application_command.name}-{interaction.filled_options}\n"
                        f"```py\n{tb}\n```"
                    )
                    await user.send(content=message[:2000])
                    logging.error(tb)
                except Exception as e:
                    logging.error("Unable to send error message to bot owner!")
                    tb = "".join(traceback.format_exception(e))
                    logging.error(tb)
                    # raise e


def setup(bot):
    bot.add_cog(ErrorHandlerCog(bot))
