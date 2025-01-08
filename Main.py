import json
import time

import random
import asyncio
import logging

from discord.ext import commands

import dotenv

dotenv.load_dotenv()

# ========================================== LOGGING ========================================= #

# Defining The Basic logger.info Message For logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Defining The Logger
logger = logging.getLogger(__name__)


# Defining The Log Message Function
def log_message(level, message):
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)


logger.info("Initialized Logging")

# ========================================== CONFIG ========================================== #


# Reading The Config File
def read_config(filename="data/config.json"):
    with open(filename, "r") as f:
        return json.load(f)


config = read_config()
logger.info("Initialized Config")

# Defining The Bot Token
TOKENS = ["LIST OF TOKENS"]

# Defining The Config Variables
DELAY = config["DELAY"]

LOGGING = config["LOGGING"]
OWNER_ID = config["OWNER_ID"]
LANGUAGES = config["LANGUAGES"]
POKETWO_ID = config["POKETWO_ID"]

SPAM = config["SPAM"]["ENABLED"]
INTERVAL = config["SPAM"]["TIMING"]
SPAM_ID = config["SPAM"]["SPAM_ID"]
WEBHOOK_URL = config["WEBHOOK_URL"]

BLACKLISTED_POKEMONS = config["BLACKLISTED_POKEMONS"]
WHITELISTED_CHANNELS = config["WHITELISTED_CHANNELS"]

# ========================================== SPAM ========================================== #


def spam():
    with open("Messages/Messages.txt", "r", encoding="utf-8", errors="ignore") as file:
        messages = file.readlines()

    spam_message = random.choice(messages).strip()

    return spam_message


# ========================================== AUTOCATCHER CLASS ========================================== #


class Autocatcher(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, self_bot=False)

        self.spam_id = SPAM_ID
        self.interval = INTERVAL
        self.languages = LANGUAGES

        self.whitelisted_channels = WHITELISTED_CHANNELS
        self.blacklisted_pokemons = BLACKLISTED_POKEMONS


# ========================================== MAIN FUNCTIONS ========================================== #


async def run_autocatcher(token):
    bot = Autocatcher()  # Initialize Bot

    @bot.event
    async def on_ready():
        logger.info("+ ============== Pokefier ============== +")
        logger.info(f"+ Logged In : {bot.user} (ID: {bot.user.id})")
        logger.info("+ ============== Config ================ +")
        logger.info(f"+ Languages: {bot.languages}")
        logger.info(f"+ Whitelisted Channels: {bot.whitelisted_channels}")
        logger.info(f"+ Blacklisted Pokemons: {bot.blacklisted_pokemons}")
        logger.info("+ ====================================== +")

        await bot.load_extension("handlers.catcher")
        logger.info("+ Loaded Catcher Handler")

        await bot.load_extension("handlers.commands")
        logger.info("+ Loaded Commands Handler")

        await bot.load_extension("handlers.misceleneous")
        logger.info("+ Loaded Misceleneous Handler")

        await bot.load_extension("handlers.shards")
        logger.info("+ Loaded Shards Handler")

        await bot.load_extension("handlers.trades")
        logger.info("+ Loaded Trades Handler")

        bot.started = time.time()  # Stats The Time
        bot.command_prefix = f"<@{bot.user.id}> "  # Set Command Prefix

        logger.info(f"+ Bot Prefix: {bot.command_prefix}")

        bot.verified = True  # Set Verified ( If False Bot Will Not Catch Pokemon)
        bot.pokemons_caught = 0  # Set Global Pokemon Counter To 0

    await bot.start(token)


async def main(tokens):
    ac_tasks = [run_autocatcher(token) for token in tokens]
    await asyncio.gather(*ac_tasks)


if __name__ == "__main__":
    asyncio.run(main(TOKENS))
