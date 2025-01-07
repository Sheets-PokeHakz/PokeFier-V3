import re
import json
from discord.ext import commands
from Main import logger, WEBHOOK_URL, OWNER_ID
from discord_webhook import DiscordEmbed, DiscordWebhook


def send_log(embed, WEBHOOK_URL):
    webhook = DiscordWebhook(url=WEBHOOK_URL, username="Pokefier Log")
    webhook.add_embed(embed)
    webhook.execute()


def extract_pokemon_data(text):
    pattern = r"Level (\d+) ([^(]+) \(([\d.]+)%\)[.!]*"  # Pattern To Extract Level, Name, And IV
    match = re.search(pattern, text)

    if match:
        level = match.group(1)
        name = match.group(2).strip()

        name = re.sub(r"<:[^>]+>", "", name)  # If Emoji, Remove It

        iv = match.group(3)
        return {"level": level, "name": name.strip(), "IV": iv}

    else:
        return None


def load_pokemon_data():
    with open("data/pokemon_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


class MisceleneousHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if "congratulations" in message.content.lower() and self.bot.verified:
            self.bot.pokemons_caught += 1

            is_shiny = False
            if "these colors" in message.content.lower():
                is_shiny = True

            pokemon_data = extract_pokemon_data(message.content)
            pokemon = next(
                (
                    p
                    for p in self.bot.pokemon_data
                    if p["name"].lower() == pokemon_data["name"].lower()
                ),
                None,
            )

            embed1 = DiscordEmbed(title="A Pokemon Was Caught!", color="03b2f8")
            embed1.set_description(
                f"Account Name : {self.bot.user.name}\n\nPokémon Name : {pokemon_data['name']}\n\nPokémon Level : {pokemon_data['level']}\nPokémon IV : {pokemon_data['IV']}%\n\nShiny : {is_shiny}\nRarity : {pokemon['rarity']}\n\nPokémons Caught : {self.bot.pokemons_caught}"
            )
            embed1.set_author(
                name="Pokefier",
                url="https://github.com/sayaarcodes/pokefier",
                icon_url="https://raw.githubusercontent.com/sayaarcodes/pokefier/main/pokefier.png",
            )
            embed1.set_thumbnail(url=pokemon["image"]["url"])
            embed1.set_timestamp()

            await send_log(embed=embed1, WEBHOOK_URL=WEBHOOK_URL)

        if (
            f"https://verify.poketwo.net/captcha/{self.bot.user.id}" in message.content
            and self.bot.verified
        ):
            logger.info("A Captcha Challenge Was Received")
            # Stop Spamming

            self.bot.verified = False
            await message.channel.send("<@716390085896962058> incense pause")
            logger.info("Incense Paused")

            owner_dm = await self.bot.fetch_user(OWNER_ID)
            await owner_dm.send(
                f"Captcha Challenge Received. Please Solve It.\n\n{message.content}"
            )
            logger.info("Captcha Challenge Sent To Owner")


async def setup(bot):
    await bot.add_cog(MisceleneousHandler(bot))
