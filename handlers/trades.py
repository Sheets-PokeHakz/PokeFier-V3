import time
import random
from discord.ext import commands
from Main import logger, DELAY, POKETWO_ID


class TradesHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.author.id == POKETWO_ID
            and message.channel.id in self.bot.whitelisted_channels
        ):
            # Stop Spamming

            logger.info("Message Received From POKETWO")
            logger.info("Attempting To Process Message")

            # Trade Accept
            if "requesting a trade with" in message.content.lower():
                logger.info("Trade Request Received")

                if (
                    message.components[0].children[0].label.lower() == "accept"
                ):  # Checking If Accept Button Is Present
                    await time.sleep(
                        random.choice(DELAY)
                    )  # Delay Before Accepting Trade For Human Replication
                    await (
                        message.components[0].children[0].click()
                    )  # Clicking The Accept Button

                logger.info("Trade Accepted")
                # Start Spamming

            # Trade Confirmation
            if message.embeds:
                if (
                    "are you sure you want to confirm this trade? please make sure that you are trading what you intended to."
                    in message.embeds[0].description.lower()
                ):
                    logger.info("Trade Confirmation Received")

                    if (
                        message.components[0].children[0].label.lower() == "confirm"
                    ):  # Checking If Confirm Button Is Present
                        await time.sleep(
                            random.choice(DELAY)
                        )  # Delay Before Confirming Trade For Human Replication
                        await (
                            message.components[0].children[0].click()
                        )  # Clicking The Confirm Button

                    logger.info("Trade Completed")
                    # Start Spamming


async def setup(bot):
    await bot.add_cog(TradesHandler(bot))
