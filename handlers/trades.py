import asyncio
import random

from discord import components
from discord.ext import commands

from main import DELAY, POKETWO_ID, logger


class TradesHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Current pokecoin balance
        self.pokecoins = 0

        # Waiting Untill Balance Is Updated!
        self.balance_event = asyncio.Event()

    @commands.command()
    async def bal(self, ctx):
        await ctx.send(f"<@{POKETWO_ID}> bal")
        logger.info("Sent Balance Check")

    @commands.command()
    async def trade(self, ctx, user: str):
        await ctx.send(f"<@{POKETWO_ID}> trade {user}")
        logger.info(f"Trade Request Sent To {user}")

    @commands.command()
    async def confirm(self, ctx):
        await ctx.send(f"<@{POKETWO_ID}> trade c")
        logger.info("Trade Confirmed")

    @commands.command()
    async def add(self, ctx, type: str = ""):
        message = ""

        if type.lower() == "all":
            logger.info("Fetching Latest Balance")

            # Reset Event Before Requesting Balance
            self.balance_event.clear()

            await ctx.send(f"<@{POKETWO_ID}> bal")

            try:
                # Wait Until on_message Updates Balance
                await asyncio.wait_for(self.balance_event.wait(), timeout=10)

            except asyncio.TimeoutError:
                logger.error("Failed To Fetch Balance")
                await ctx.send("Failed To Fetch Balance")
                return

            logger.info(f"Using Balance : {self.pokecoins}")

            await ctx.send(f"<@{POKETWO_ID}> t a pc {self.pokecoins}")
            await asyncio.sleep(2)

            await ctx.send(f"<@{POKETWO_ID}> t aa --limit 3000")

            logger.info("Added All Pokemons And Pokecoins")
            return

        elif type.lower() == "bal":
            logger.info("Fetching Latest Balance")

            self.balance_event.clear()

            await ctx.send(f"<@{POKETWO_ID}> bal")

            try:
                await asyncio.wait_for(self.balance_event.wait(), timeout=10)

            except asyncio.TimeoutError:
                logger.error("Failed To Fetch Balance")
                await ctx.send("Failed To Fetch Balance")
                return

            message = f"t a pc {self.pokecoins}"

        elif type.lower() == "poke":
            message = "t aa --limit 3000"

        elif type == "":
            await ctx.send(
                "Add All Pokemons - poke\n" "Add All Balance - bal\n\n" "All - all"
            )
            return

        else:
            message = type

        await ctx.send(f"<@{POKETWO_ID}> {message}")
        logger.info("Command Sent")

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.author.id == POKETWO_ID
            and message.channel.id in self.bot.whitelisted_channels
        ):
            logger.info("Message Received From POKETWO")

            # Trade Accept
            if "requesting a trade with" in message.content.lower():
                logger.info("Trade Request Received")

                if (
                    message.components
                    and message.components[0].children[0].label.lower() == "accept"
                ):
                    await asyncio.sleep(random.choice(DELAY))

                    await message.components[0].children[0].click()

                    logger.info("Trade Accepted")

            if "Are you sure you want to trade".lower() in message.content.lower():
                logger.info("Trade Confirmation Received")

                if (
                    message.components
                    and message.components[0].children[0].label.lower() == "confirm"
                ):
                    await asyncio.sleep(random.choice(DELAY))

                    await message.components[0].children[0].click()

                    logger.info("Trade Confirmed")

            # Embed Processing
            if message.embeds:
                embed = message.embeds[0]

                # Trade Confirmation
                if (
                    embed.author.name is not None
                    and "are you sure you want to confirm this trade?"
                    in embed.author.name.lower()
                ):
                    logger.info("Trade Confirmation Received")

                    if (
                        message.components
                        and message.components[0].children[0].label is not None
                        and message.components[0].children[0].label.lower() == "confirm"
                    ):
                        await asyncio.sleep(random.choice(DELAY))

                        await message.components[0].children[0].click()

                        logger.info("Trade Completed")

                    if (
                        message.components
                        and message.components[1].children[0].label is not None
                        and message.components[1].children[0].label.lower() == "confirm"
                    ):
                        await asyncio.sleep(random.choice(DELAY))

                        await message.components[1].children[0].click()

                        logger.info("Trade Completed")

                # Balance Extraction
                elif embed.fields and "pokécoins" in str(embed.fields[0].name).lower():
                    logger.info("Got Balance Message")

                    try:
                        self.pokecoins = int(embed.fields[0].value.replace(",", ""))

                        logger.info(f"Updated Pokecoins Count : {self.pokecoins}")

                        # Notify Waiting Commands
                        self.balance_event.set()

                        await message.channel.send(
                            f"My Pokecoins Amount : {self.pokecoins}"
                        )

                    except Exception as e:
                        logger.error(f"Failed To Parse Balance : {e}")


async def setup(bot):
    await bot.add_cog(TradesHandler(bot))
