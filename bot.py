import os
import disnake
import logging
from typing import List
from urllib import response
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
        guilds: List[disnake.Guild] = bot.guilds
        for guild in guilds:
            # await guild.change_voice_state(None, self_deaf=True)
            print(f"Bot is now connected to {guild.name}")

    for folder in os.listdir("cogs"):
        if os.path.exists(os.path.join("cogs", folder, "cog.py")):
            # print(f"cogs.{folder}.cog")
            bot.load_extension(f"cogs.{folder}.cog")

    bot.run(config.BOT_TOKEN)


if __name__ == "__main__":
    main()
