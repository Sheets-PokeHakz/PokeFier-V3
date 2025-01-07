# Discord Modules
from discord.ext import commands

class SelfCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def pinguu(self, ctx):
        await ctx.send("Pong!")

async def setup(bot):
    await bot.add_cog(SelfCommands(bot))
