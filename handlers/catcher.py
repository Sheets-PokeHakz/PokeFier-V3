import time
import random
from discord.ext import commands
from utilities.poke_identify import pokefier, solve, remove_diacritics
from main import logger, POKETWO_ID, WHITELISTED_CHANNELS, LANGUAGES, DELAY


class CatcherHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pokefier = pokefier()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.embeds:
            if (
                message.author.id == POKETWO_ID
                and len(message.embeds) > 0
                and message.channel.id in WHITELISTED_CHANNELS
                and "wild pokémon has appeared".lower()
                in message.embeds[0].title.lower()
                and self.bot.verified
            ):  # Checking If Pokémon Spawned And Bot Is Verified
                logger.info("A Pokémon Spawned - Attemping To Predict")

                pokemon_image = message.embeds[
                    0
                ].image.url  # Get The Image URL Of The Pokémon
                predicted_pokemons = await self.pokefier.predict_pokemon_from_url(
                    image_url=pokemon_image
                )  # Predict The Pokémon Using Pokefier

                predicted_pokemon = max(
                    predicted_pokemons, key=lambda x: x[1]
                )  # Get The Pokémon With Highest Score

                name = predicted_pokemon[0]  # Get The Name Of The Pokémon
                score = predicted_pokemon[1]  # Get The Score Of The Pokémon

                self.bot.blacklisted_pokemons = [
                    pokemon_name.lower()
                    for pokemon_name in self.bot.blacklisted_pokemons
                ]  # Get The Blacklisted Pokemons

                if name.lower() in self.bot.blacklisted_pokemons:
                    logger.info(
                        f"Pokémon : {name} Was Not Caught Because It Is Blacklisted"
                    )
                    return

                if score > 30.0:  # 30 Is The Threshold Score
                    alt_name = await self.pokefier.get_alternate_pokemon_name(
                        name, languages=LANGUAGES
                    )
                    alt_name = remove_diacritics(alt_name)

                    time.sleep(random.choice(DELAY))
                    await message.channel.send(f"<@716390085896962058> c {alt_name}")
                    logger.info(f"Predicted Pokémon : {name} With Score : {score}")

                else:
                    logger.info(f"Predicted Pokémon : {name} With Score : {score}")

                    time.sleep(random.choice(DELAY))
                    await message.channel.send("<@716390085896962058> h")

        if (
            "that is the wrong pokémon" in message.content.lower()
            and self.bot.verified
            and message.channel.id in WHITELISTED_CHANNELS
        ):
            logger.info("Wrong Pokémon Detected")
            await message.channel.send("<@716390085896962058> h")

            logger.info("Requested Hint For Wrong Pokémon")

        if (
            "the pokémon is" in message.content.lower()
            and self.bot.verified
            and message.channel.id in WHITELISTED_CHANNELS
        ):
            logger.info("Solving The Hint")
            await message.channel.send(
                "<@716390085896962058> c {}".format(solve(message.content)[0])
            )

            logger.info("Hint Solved")


async def setup(bot):
    await bot.add_cog(CatcherHandler(bot))
