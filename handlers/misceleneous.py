import json
import re
import time
from pathlib import Path

from discord.ext import commands
from discord_webhook import DiscordEmbed, DiscordWebhook

from main import OWNER_ID, WEBHOOK_URL, logger
from utilities.terminal_dashboard import terminal_dashboard


async def send_log(embed, WEBHOOK_URL):
    webhook = DiscordWebhook(url=WEBHOOK_URL, username="Pokefier Log")
    webhook.add_embed(embed)
    webhook.execute()


def load_pokemon_data():
    data_path = Path(__file__).resolve().parents[1] / "data" / "pokemon_data.json"
    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_pokemon_entry(name):
    pokemon = load_pokemon_data()
    pokemon = next((p for p in pokemon if p["name"].lower() == name.lower()), None)
    return pokemon


def get_pokemon_image(name):
    pokemon = get_pokemon_entry(name)
    if pokemon:
        image = pokemon.get("image", None).get("url", None)

        if image:
            return image


def to_rarity_bucket(pokemon_rarity):
    if not pokemon_rarity:
        return "norm"
    rarity = pokemon_rarity.lower()
    if "legendary" in rarity:
        return "leg"
    if "mythic" in rarity:
        return "myth"
    if "ultra beast" in rarity:
        return "ub"
    if "event" in rarity:
        return "ev"
    if "regional" in rarity:
        return "reg"
    return "norm"


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


class MisceleneousHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _update_24h_catch_window(self, now_ts):
        cutoff = now_ts - 86400
        while self.bot.catch_timestamps and self.bot.catch_timestamps[0] < cutoff:
            self.bot.catch_timestamps.popleft()

    @commands.command()
    async def solved(self, ctx):
        self.bot.verified = True
        await ctx.send("Thanks Dude! I Will Continue The Grind")
        if self.bot.terminal_dashboard_enabled and self.bot.user:
            terminal_dashboard.record_captcha(self.bot.user.id, "solved")
            terminal_dashboard.set_account_status(
                self.bot.user.id, captcha=False, verified=True
            )

        logger.info("Captcha Solved - Self Bot Booted")

    @commands.Cog.listener()
    async def on_message(self, message):
        if "congratulations" in message.content.lower() and self.bot.verified:
            self.bot.pokemons_caught += 1
            now_ts = time.time()
            self.bot.catch_timestamps.append(now_ts)
            self._update_24h_catch_window(now_ts)
            catches_last_24h = len(self.bot.catch_timestamps)

            is_shiny = False
            if "these colors" in message.content.lower():
                is_shiny = True

            pokemon_data = extract_pokemon_data(message.content)
            pokemon_url = get_pokemon_image(pokemon_data["name"])
            pokemon_entry = get_pokemon_entry(pokemon_data["name"])
            self.bot.last_caught = {
                "name": pokemon_data["name"],
                "level": pokemon_data["level"],
                "iv": pokemon_data["IV"],
                "is_shiny": is_shiny,
                "timestamp": now_ts,
                "channel_id": message.channel.id,
            }
            if self.bot.terminal_dashboard_enabled and self.bot.user:
                rarity_bucket = to_rarity_bucket(
                    pokemon_entry.get("rarity") if pokemon_entry else None
                )
                terminal_dashboard.record_catch(
                    self.bot.user.id,
                    pokemon_data["name"],
                    pokemon_data["level"],
                    pokemon_data["IV"],
                    is_shiny,
                    rarity_bucket,
                    message.channel.name if hasattr(message.channel, "name") else "N/A",
                )
                terminal_dashboard.update_safety(
                    self.bot.user.id, catches_last_24h, self.bot.max_catches_24h
                )

            if catches_last_24h >= self.bot.max_catches_24h:
                logger.warning(
                    f"24h Catch Limit Reached ({catches_last_24h}/{self.bot.max_catches_24h}) - Pausing Automation"
                )
                self.bot.verified = False
                self.bot.spam_enabled = False
                await message.channel.send("<@716390085896962058> incense pause")

                owner_dm = self.bot.get_user(OWNER_ID)
                if owner_dm:
                    await owner_dm.send(
                        f"Safety pause enabled.\n24h catches: {catches_last_24h}/{self.bot.max_catches_24h}"
                    )
                return

            if catches_last_24h >= self.bot.catch_warning_threshold:
                logger.warning(
                    f"24h Catch Warning ({catches_last_24h}/{self.bot.max_catches_24h})"
                )

            embed1 = DiscordEmbed(title="A Pokemon Was Caught!", color="03b2f8")
            embed1.set_description(
                f"Account Name : {self.bot.user.name}\n\nPokémon Name : {pokemon_data['name']}\n\nPokémon Level : {pokemon_data['level']}\nPokémon IV : {pokemon_data['IV']}%\n\nShiny : {is_shiny}\n\nPokemons Caught : {self.bot.pokemons_caught}"
            )
            embed1.set_author(
                name="Pokefier",
                url="https://github.com/sayaarcodes/pokefier",
                icon_url="https://raw.githubusercontent.com/sayaarcodes/pokefier/main/pokefier.png",
            )
            embed1.set_timestamp()

            if pokemon_url:
                embed1.set_thumbnail(url=pokemon_url)

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
            if self.bot.terminal_dashboard_enabled and self.bot.user:
                terminal_dashboard.record_captcha(self.bot.user.id, "encountered")
                terminal_dashboard.set_account_status(
                    self.bot.user.id, captcha=True, verified=False
                )

            owner_dm = self.bot.get_user(OWNER_ID)
            await owner_dm.send(
                f"Captcha Challenge Received. Please Solve It.\n\n{message.content}"
            )
            logger.info("Captcha Challenge Sent To Owner")


async def setup(bot):
    await bot.add_cog(MisceleneousHandler(bot))
