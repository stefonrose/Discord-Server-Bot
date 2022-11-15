import os, random, disnake
from firebase_admin import db
from disnake.ext import commands


class RandomCog(commands.Cog, name="Random"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.max_concurrency(1, commands.BucketType.guild, wait=True)
    @commands.slash_command()
    async def balls(self, interaction: disnake.ApplicationCommandInteraction):
        """balls"""
        images = os.listdir("cogs/random/mag")
        names = [os.path.splitext(image)[0] for image in images]
        guildRef = db.reference(f"{interaction.guild_id}")
        ballsRef = db.reference(f"{interaction.guild_id}/balls")
        userInfo = ballsRef.get()
        if userInfo is None:
            name = random.choice(names)
            image = next(i for i in images if name in i)
            guildRef.update({"balls": {name: True}})
        else:
            seen = [k for k, v in userInfo.items() if userInfo[k]]
            available = list(set(names).difference(seen))
            if len(available) == 0:
                ballsRef.delete()
                name = random.choice(names)
                image = next(i for i in images if name in i)
                guildRef.update({"balls": {name: True}})
            else:
                name = random.choice(available)
                image = next(i for i in images if name in i)
                ballsRef.update({name: True})
        file = disnake.File(f"cogs/random/mag/{image}")
        await interaction.response.send_message(file=file)

def setup(bot):
    bot.add_cog(RandomCog(bot))
