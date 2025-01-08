import time
import random
from main import logger, DELAY
from discord.ext import commands


class ShardsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "are you sure you want to exchange" in message.content.lower():
            # Stop Spamming

            logger.info("A Shard Buy Message Received")

            if (
                message.components[0].children[0].label.lower() == "confirm"
            ):  # Checking If Confirm Button Is Present
                await time.sleep(
                    random.choice(DELAY)
                )  # Delay Before Confirming Trade For Human Replication
                await (
                    message.components[0].children[0].click()
                )  # Clicking The Confirm Button

            logger.info("Shard Bought")
            # Start Spamming

        if "you don't have enough shards" in message.content.lower():
            # Stop Spamming

            logger.info("Not Enough Shards To Buy Incense")

            await message.channel.send("Not Enough Shards To Buy Incense")
            await message.channel.send(
                f"To Buy Shards Use `{self.bot.command_prefix}shardbuy <amount>`"
            )


async def setup(bot):
    await bot.add_cog(ShardsHandler(bot))
