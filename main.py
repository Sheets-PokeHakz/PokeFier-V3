import asyncio
import json
import logging
import os
import time
from collections import deque

import dotenv
from discord.ext import commands
from utilities.terminal_dashboard import terminal_dashboard

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


def normalize_tokens(raw_tokens):
    if raw_tokens is None:
        return []

    if isinstance(raw_tokens, str):
        token_sources = raw_tokens.split(",")
    elif isinstance(raw_tokens, list):
        token_sources = []
        for token in raw_tokens:
            if isinstance(token, str):
                token_sources.extend(token.split(","))
            elif token is not None:
                token_sources.append(str(token))
    else:
        token_sources = [str(raw_tokens)]

    return [token.strip() for token in token_sources if token.strip()]


TOKENS = normalize_tokens(config.get("TOKENS"))
if not TOKENS:
    TOKENS = normalize_tokens(os.getenv("TOKENS"))

if not TOKENS:
    raise ValueError(
        "No valid TOKENS configured. Add non-empty TOKENS in data/config.json "
        "or set TOKENS as a comma-separated env var."
    )

# Defining The Config Variables
DELAY = config["DELAY"]

LOGGING = config["LOGGING"]
OWNER_ID = config["OWNER_ID"]
LANGUAGES = config["LANGUAGES"]
POKETWO_ID = config["POKETWO_ID"]


def to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


SPAM = to_bool(config["SPAM"]["ENABLED"])
INTERVAL = config["SPAM"]["TIMING"]
SPAM_ID = config["SPAM"]["SPAM_ID"]
WEBHOOK_URL = config["WEBHOOK_URL"]
DASHBOARD_CONFIG = config.get("DASHBOARD", {})
DASHBOARD_ENABLED = to_bool(DASHBOARD_CONFIG.get("ENABLED", True))
DASHBOARD_HOST = DASHBOARD_CONFIG.get("HOST", "127.0.0.1")
DASHBOARD_PORT = int(DASHBOARD_CONFIG.get("PORT", 8080))
TERMINAL_CONFIG = config.get("TERMINAL_DASHBOARD", {})
TERMINAL_DASHBOARD_ENABLED = to_bool(TERMINAL_CONFIG.get("ENABLED", True))
SAFETY_CONFIG = config.get("SAFETY", {})
ACCOUNT_SPAM_COOLDOWN = float(SAFETY_CONFIG.get("ACCOUNT_SPAM_COOLDOWN", 1.5))
GUILD_SPAM_COOLDOWN = float(SAFETY_CONFIG.get("GUILD_SPAM_COOLDOWN", 1.0))
MIN_SPAM_INTERVAL = float(SAFETY_CONFIG.get("MIN_SPAM_INTERVAL", 3.6))
MAX_CATCHES_24H = int(SAFETY_CONFIG.get("MAX_CATCHES_24H", 1000))
CATCH_WARNING_THRESHOLD = int(SAFETY_CONFIG.get("CATCH_WARNING_THRESHOLD", 900))

BLACKLISTED_POKEMONS = config["BLACKLISTED_POKEMONS"]
WHITELISTED_CHANNELS = config["WHITELISTED_CHANNELS"]

# ========================================== AUTOCATCHER CLASS ========================================== #


class Autocatcher(commands.Bot):
    def __init__(self, account_index=0, dashboard_enabled=False):
        super().__init__(command_prefix=None, self_bot=False)

        self.account_index = account_index
        self.spam_id = SPAM_ID
        self.interval = INTERVAL
        self.spam_enabled = SPAM
        self.incense_mode = False
        self.languages = LANGUAGES

        self.whitelisted_channels = WHITELISTED_CHANNELS
        self.blacklisted_pokemons = BLACKLISTED_POKEMONS
        self.dashboard_host = DASHBOARD_HOST
        self.dashboard_port = DASHBOARD_PORT
        self.started = None
        self.verified = False
        self.pokemons_caught = 0
        self.last_spawn_prediction = None
        self.last_caught = None
        self.last_spam = None
        self.last_spam_at = 0.0
        self.next_spam_at = 0.0
        self.pokecoins = 0
        self.account_spam_cooldown = ACCOUNT_SPAM_COOLDOWN
        self.guild_spam_cooldown = GUILD_SPAM_COOLDOWN
        self.min_spam_interval = MIN_SPAM_INTERVAL
        self.max_catches_24h = MAX_CATCHES_24H
        self.catch_warning_threshold = CATCH_WARNING_THRESHOLD
        self.catch_timestamps = deque()
        self.terminal_dashboard_enabled = TERMINAL_DASHBOARD_ENABLED
        self.dashboard_enabled = dashboard_enabled


# ========================================== MAIN FUNCTIONS ========================================== #


async def run_autocatcher(token, account_index=0):
    bot = Autocatcher(
        account_index=account_index,
        dashboard_enabled=DASHBOARD_ENABLED and account_index == 0,
    )  # Initialize Bot

    bot.remove_command("help")  # Remove Default Help Command

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

        if bot.spam_enabled:
            await bot.load_extension("handlers.spam")
            logger.info("+ Loaded Spam Handler")
        else:
            logger.info("+ Spam Handler Disabled In Config")

        if bot.dashboard_enabled:
            await bot.load_extension("handlers.dashboard")
            logger.info(
                f"+ Loaded Dashboard Handler (http://{bot.dashboard_host}:{bot.dashboard_port})"
            )
        elif DASHBOARD_ENABLED:
            logger.info("+ Dashboard Handler Skipped For Secondary Account")
        else:
            logger.info("+ Dashboard Disabled In Config")

        bot.started = time.time()  # Stats The Time
        bot.command_prefix = f"<@{bot.user.id}> "  # Set Command Prefix

        logger.info(f"+ Bot Prefix: {bot.command_prefix}")

        bot.verified = True  # Set Verified ( If False Bot Will Not Catch Pokemon)

        if bot.terminal_dashboard_enabled and bot.user:
            terminal_dashboard.start(len(TOKENS))
            terminal_dashboard.register_account(bot.user.id, str(bot.user))
            terminal_dashboard.set_account_status(
                bot.user.id,
                connected=True,
                verified=bot.verified,
                spam_enabled=bot.spam_enabled,
            )

    await bot.start(token)


async def stop_autocatcher():
    for task in asyncio.all_tasks():
        task.cancel()
        await task


async def main(tokens):
    ac_tasks = [run_autocatcher(token, index) for index, token in enumerate(tokens)]
    await asyncio.gather(*ac_tasks)


if __name__ == "__main__":
    asyncio.run(main(TOKENS))
