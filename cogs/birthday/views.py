from typing import Any
from firebase_admin import db
import os, config, discord, datetime, logging


class BirthdaySelectView(discord.ui.View):
    def __init__(self):
        super().__init__()


class MonthSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="January", value="January"),
            discord.SelectOption(label="February", value="February"),
        ]
        super().__init__(
            placeholder="Month",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="month_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You selected {self.values[0]}")


class SetBirthdayModal(discord.ui.Modal, title="Enter Your Birthday"):
    month = discord.ui.TextInput(
        label="Month",
        placeholder="'January' OR 'Jan' OR '1'",
        custom_id="month",
        required=True,
        style=discord.TextStyle.short,
    )
    date = discord.ui.TextInput(
        label="Day",
        placeholder="1 - 31",
        custom_id="day",
        required=True,
        style=discord.TextStyle.short,
    )
    year = discord.ui.TextInput(
        label="Year",
        placeholder="1996",
        custom_id="year",
        required=True,
        min_length=4,
        max_length=4,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        validDate = True

        months = []
        table = {}
        here = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(here, "months.txt")
        with open(filename, "r") as m:
            for line in m:
                (key, val) = line.split()
                months.append(key)
                table[key] = int(val)

        month = self.month.value.lower()
        day = self.date.value
        year = self.year.value

        if month in months and day.isnumeric() and year.isnumeric():
            month = int(table[month])
            day = int(day)
            year = int(year)

            match month:
                case 2:
                    if day < 1 or day > 29:
                        logging.info("Invalid day 1")
                        validDate = False
                case 4 | 6 | 9 | 11:
                    if day < 1 or day > 30:
                        logging.info("Invalid day 2")
                        validDate = False
                case 1 | 3 | 5 | 7 | 8 | 10 | 12:
                    if day < 1 or day > 31:
                        logging.info("Invalid day 3")
                        validDate = False
            yearNow = datetime.date.today().year
            maxYear = yearNow - 13
            minYear = yearNow - 100
            if year < minYear or year > maxYear:
                validDate = False

        else:
            validDate = False

        if validDate:
            birthdayRef = db.reference(f"{config.SINFUL_SERVER_ID}/users")
            birthday = datetime.datetime(year, month, day).date()
            birthdayRef.update(
                {
                    interaction.user.id: {
                        "birth_day": day,
                        "birth_month": month,
                        "birth_year": year,
                    }
                }
            )
            await interaction.response.send_message(
                f"Your birthday has been saved successfully: {birthday}"
            )
        else:
            await interaction.response.send_message(
                "Unable to create a valid date with the information provided."
            )
