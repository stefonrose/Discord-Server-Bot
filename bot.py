from typing import List
from disnake.ext import commands
from firebase_admin import credentials
import os, config, disnake, logging, firebase_admin


def main():
    logging.basicConfig(level=logging.INFO)
    bot = commands.InteractionBot(
        test_guilds=[int(config.SINFUL_SERVER_ID), int(config.MY_SERVER_ID)],
        intents=disnake.Intents.all(),
    )

    bot.firebase_cred = credentials.Certificate(config.FIREBASE_CONFIG)
    bot.firebase_app = firebase_admin.initialize_app(
        bot.firebase_cred,
        {
            "databaseURL": "https://sinful-server-bot-default-rtdb.firebaseio.com/",
            "databaseAuthVariableOverride": {"uid": "discord_bot"},
        },
    )

    bot.customAttr = "Maple Syrup"

    @bot.event
    async def on_ready():
        logging.info("Bot has established connection to server(s).")

    for folder in os.listdir("cogs"):
        if os.path.exists(os.path.join("cogs", folder, "cog.py")):
            bot.load_extension(f"cogs.{folder}.cog")

    @bot.slash_command()
    async def help(interaction: disnake.ApplicationCommandInteraction):
        """Displays a list of all available commands."""
        embed = disnake.Embed(
            title="Slash Commands List",
        )
        for app_command in bot.slash_commands:
            embed.add_field(
                name=app_command.name, value=app_command.description, inline=False
            )
        await interaction.response.send_message(embed=embed)

    bot.run(config.BOT_TOKEN)


if __name__ == "__main__":
    main()
