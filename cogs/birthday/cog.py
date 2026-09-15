import discord, config
from . import views, model
from typing import List
from firebase_admin import db
from discord import app_commands, Interaction
from discord.ext import commands, tasks
from datetime import datetime, timedelta


class BirthdayCog(commands.Cog, name="Birthday"):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.daily.start()

    @tasks.loop(minutes=60)
    async def daily(self):
        database = db.reference(f"{config.SINFUL_SERVER_ID}")
        stored = datetime.fromisoformat(database.child("birthday/current").get()).date()
        today = datetime.today().date()

        if stored != today:
            dateRef = db.reference(f"{config.SINFUL_SERVER_ID}/birthday")
            dateRef.update({"current": today.isoformat()})

            month, day = today.month, today.day

            query = (
                database.child("users")
                .order_by_child("birth_month")
                .equal_to(month)
                .get()
            )
            users: List[model.User] = UserMapper(query)
            bdays = [user for user in users if user.birth_day == day]

            for user in bdays:
                guild = await self.bot.fetch_guild(config.SINFUL_SERVER_ID)
                channel = await guild.fetch_channel(config.SINFUL_TEST_ID)
                member = await guild.fetch_member(user.discordId)
                message = f"@everyone - Happy Birthday {member.mention} :birthday: :tada: :birthday: :tada:!"
                await channel.send(content=message)

    birthday_group = app_commands.Group(
        name="birthday", description="Commands for managing member birthdays."
    )

    @birthday_group.command()
    async def set(self, interaction: Interaction):
        """Set your birthday"""
        guildRef = db.reference(f"{interaction.guild_id}")
        ballsRef = db.reference(f"{interaction.guild_id}/birthday")
        await interaction.response.send_modal(views.SetBirthdayModal())

    @birthday_group.command()
    async def mine(self, interaction: Interaction):
        """View what birthday the bot currently has saved for you"""
        reference = db.reference(f"{config.SINFUL_SERVER_ID}")
        results = (
            reference.child("users")
            .order_by_key()
            .equal_to(str(interaction.user.id))
            .get()
        )
        users = UserMapper(results=results)
        if not users:
            await interaction.response.send_message(
                content="I don't have a birthday saved for you."
            )
        else:
            user = users.pop()
            await interaction.response.send_message(
                content=f"Your birthday is {user.birth_month}/{user.birth_day}/{user.birth_year}"
            )

    @birthday_group.command()
    async def view(self, interaction: Interaction, member: discord.Member):
        """View the birthday of a specified member"""
        reference = db.reference(f"{config.SINFUL_SERVER_ID}")
        results = reference.child("users").order_by_key().equal_to(str(member.id)).get()
        users = UserMapper(results=results)
        if not users:
            await interaction.response.send_message(
                content=f"I don't have a birthday saved for {member.display_name}."
            )
        else:
            user = users.pop()
            await interaction.response.send_message(
                content=f"{member.display_name}'s birthday is {user.birth_month}/{user.birth_day}/{user.birth_year}"
            )


def UserMapper(results) -> List[model.User]:
    users: List[model.User] = []
    for key, value in results.items():
        discordId = int(key)
        birth_month = int(value["birth_month"])
        birth_day = int(value["birth_day"])
        birth_year = int(value["birth_year"])

        user = model.User(discordId, birth_month, birth_day, birth_year)
        users.append(user)

    return users


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BirthdayCog(bot))
