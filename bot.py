import os
from urllib import response
import disnake
import logging
from typing import List
from disnake.ext import commands
import resources.config as config


def main():
    logging.basicConfig(level=logging.INFO)
    bot = commands.InteractionBot(
        test_guilds=[int(config.SINFUL_SERVER_ID), int(config.MY_SERVER_ID)],
        intents=disnake.Intents.all(),
    )

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(config.SINFUL_SERVER_ID))
        print(guild.name)

    @bot.slash_command()
    async def joinchannel(interaction: disnake.ApplicationCommandInteraction):
        """Request the bot join your current voice channel"""
        voiceState = interaction.author.voice
        if voiceState != None:
            if voiceState.channel != None:
                voiceClient = await voiceState.channel.connect()
                voiceClient.guild.change_voice_state(self_deaf=True)
                await interaction.response.send_message(
                    "Connecting to the channel now."
                )

        else:
            await interaction.response.send_message(
                "You have to be in a voice channel to use that."
            )

    bot.run(config.BOT_TOKEN)


if __name__ == "__main__":
    main()
