from typing import List
from pkgutil import iter_modules
from discord import app_commands, CustomActivity, PartialEmoji
from discord.ext import commands
from firebase_admin import credentials
import config, discord, logging, firebase_admin


def main():
    logging.basicConfig(level=logging.INFO)

    bot = commands.Bot(command_prefix="!*!", intents=discord.Intents.all())
    bot.firebase_cred = credentials.Certificate(config.FIREBASE_CONFIG)
    bot.firebase_app = firebase_admin.initialize_app(
        bot.firebase_cred,
        {
            "databaseURL": "https://sinful-server-bot-default-rtdb.firebaseio.com/",
            "databaseAuthVariableOverride": {"uid": "discord_bot"},
        },
    )

    @bot.event
    async def setup_hook():
        logging.info("Bot is starting.")
        for module in iter_modules(["cogs"], prefix="cogs."):
            await bot.load_extension(f"{module.name}.cog")

    @bot.event
    async def on_ready():
        logging.info("Bot has established connection to server(s).")
        guild = discord.Object(id=config.SINFUL_SERVER_ID)
        emoji = PartialEmoji.from_str(":crazyeyes:908023063621296170")
        activity = CustomActivity(name="Watching over the realms.", emoji=emoji)
        await bot.change_presence(activity=activity)
        await bot.tree.sync()

    @bot.tree.command()
    async def help(interaction: discord.Interaction):
        """Displays a list of all available commands."""
        results = await bot.tree.fetch_commands()
        commands = []
        for item in results:
            if not item.options:
                commands.append((item.mention, item.description))
            else:
                for option in item.options:
                    if type(option) is discord.app_commands.models.AppCommandGroup:
                        commands.append((option.mention, option.description))
                    else:
                        commands.append((item.mention, item.description))

        safe_commands = [commands[i : i + 25] for i in range(0, len(commands), 25)]

        embeds = []
        for sub_commands in safe_commands:
            embed = discord.Embed(
                title="Slash Commands List",
            )
            for app_command in sub_commands:
                embed.add_field(name=app_command[0], value=app_command[1], inline=False)
            embeds.append(embed)
        await interaction.response.send_message(embeds=embeds)

    bot.run(config.BOT_TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
