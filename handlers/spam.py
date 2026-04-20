import asyncio
import random
import time
from pathlib import Path

from discord.ext import commands, tasks

from main import logger
from utilities.terminal_dashboard import terminal_dashboard


def load_messages(file_path="messages/Messages.txt"):
    message_file = Path(file_path)

    if not message_file.exists():
        logger.warning(f"Spam Messages File Not Found: {file_path}")
        return []

    with message_file.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


class SpamHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages = load_messages()
        self.last_guild_spam_at = {}
        self.spam_loop.start()

    def cog_unload(self):
        self.spam_loop.cancel()

    def get_target_channel_id(self):
        if self.bot.spam_id:
            return self.bot.spam_id
        if self.bot.whitelisted_channels:
            return self.bot.whitelisted_channels[0]
        return None

    @tasks.loop(seconds=1.0)
    async def spam_loop(self):
        if not self.bot.spam_enabled:
            if self.bot.terminal_dashboard_enabled and self.bot.user:
                terminal_dashboard.set_account_status(
                    self.bot.user.id, spam_enabled=False
                )
            return

        if not self.bot.verified:
            return

        if not self.messages:
            return

        channel_id = self.get_target_channel_id()
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            logger.warning(f"Spam Channel Not Found: {channel_id}")
            return

        now = time.time()
        guild_id = channel.guild.id if channel.guild else 0
        guild_last_spam_at = self.last_guild_spam_at.get(guild_id, 0.0)
        allowed_at = max(
            self.bot.last_spam_at + self.bot.account_spam_cooldown,
            guild_last_spam_at + self.bot.guild_spam_cooldown,
            self.bot.next_spam_at,
        )
        if now < allowed_at:
            return

        message = random.choice(self.messages)
        await channel.send(message)
        sent_at = time.time()
        self.bot.last_spam_at = sent_at
        self.last_guild_spam_at[guild_id] = sent_at

        configured_delay = random.choice(self.bot.interval) if self.bot.interval else 0.0
        adaptive_delay = max(configured_delay, self.bot.min_spam_interval)
        self.bot.next_spam_at = sent_at + adaptive_delay

        self.bot.last_spam = {
            "message": message,
            "channel_id": channel_id,
            "timestamp": sent_at,
            "delay_used": adaptive_delay,
        }
        if self.bot.terminal_dashboard_enabled and self.bot.user:
            terminal_dashboard.set_account_status(self.bot.user.id, spam_enabled=True)
            terminal_dashboard.record_spam(self.bot.user.id, channel_id, adaptive_delay)

        await asyncio.sleep(0.05)

    @spam_loop.before_loop
    async def before_spam_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(SpamHandler(bot))
