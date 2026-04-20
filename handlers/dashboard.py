import json
import time
from pathlib import Path

from aiohttp import web
from discord.ext import commands

from main import logger


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "data" / "config.json"
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"


def _iso_time(ts):
    if not ts:
        return "N/A"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _parse_number_list(raw_value):
    if isinstance(raw_value, list):
        return [float(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        values = [item.strip() for item in raw_value.split(",") if item.strip()]
        return [float(item) for item in values]
    return []


def _parse_int_list(raw_value):
    if isinstance(raw_value, list):
        return [int(item) for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        values = [item.strip() for item in raw_value.split(",") if item.strip()]
        return [int(item) for item in values]
    return []


def _parse_str_list(raw_value):
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    return []


def _read_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_config(config_data):
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=2)
        file.write("\n")


def _to_json_safe(value):
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_to_json_safe(item) for item in value]
    if hasattr(value, "item") and callable(getattr(value, "item")):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


class DashboardHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_get("/", self.home_page)
        self.app.router.add_get("/system", self.home_page)
        self.app.router.add_get("/activity", self.home_page)
        self.app.router.add_get("/safety", self.home_page)
        self.app.router.add_get("/api/status", self.status)
        self.app.router.add_get("/api/profile", self.profile)
        self.app.router.add_post("/api/config", self.update_config)
        self.app.router.add_get("/api/config/raw", self.get_raw_config)
        self.app.router.add_post("/api/config/raw", self.save_raw_config)
        self.app.router.add_static("/static/", path=str(STATIC_DIR))
        self.runner = None
        self.site = None
        self.bot.loop.create_task(self.start_server())

    async def start_server(self):
        await self.bot.wait_until_ready()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(
            self.runner, host=self.bot.dashboard_host, port=self.bot.dashboard_port
        )
        await self.site.start()
        logger.info(
            f"Dashboard Running On http://{self.bot.dashboard_host}:{self.bot.dashboard_port}"
        )

    def cog_unload(self):
        if self.runner:
            self.bot.loop.create_task(self.runner.cleanup())

    def _status_payload(self):
        uptime = int(time.time() - self.bot.started) if self.bot.started else 0
        catches_last_24h = len(self.bot.catch_timestamps)
        payload = {
            "user": str(self.bot.user) if self.bot.user else "Unknown",
            "verified": self.bot.verified,
            "spam_enabled": self.bot.spam_enabled,
            "spam_id": self.bot.spam_id,
            "interval": self.bot.interval,
            "languages": self.bot.languages,
            "whitelisted_channels": self.bot.whitelisted_channels,
            "blacklisted_pokemons": self.bot.blacklisted_pokemons,
            "pokemons_caught": self.bot.pokemons_caught,
            "latency_ms": round(self.bot.latency * 1000) if self.bot.latency else 0,
            "uptime_seconds": uptime,
            "last_prediction": self.bot.last_spawn_prediction,
            "last_caught": self.bot.last_caught,
            "last_spam": self.bot.last_spam,
            "last_prediction_at": _iso_time(
                self.bot.last_spawn_prediction["timestamp"]
            )
            if self.bot.last_spawn_prediction
            else "N/A",
            "last_caught_at": _iso_time(self.bot.last_caught["timestamp"])
            if self.bot.last_caught
            else "N/A",
            "last_spam_at": _iso_time(self.bot.last_spam["timestamp"])
            if self.bot.last_spam
            else "N/A",
            "catches_last_24h": catches_last_24h,
            "max_catches_24h": self.bot.max_catches_24h,
            "account_spam_cooldown": self.bot.account_spam_cooldown,
            "guild_spam_cooldown": self.bot.guild_spam_cooldown,
            "min_spam_interval": self.bot.min_spam_interval,
            "next_spam_at": _iso_time(self.bot.next_spam_at),
        }
        return _to_json_safe(payload)

    def _profile_payload(self):
        user = self.bot.user
        if not user:
            return {"ready": False}
        avatar_url = str(user.display_avatar.url) if user.display_avatar else ""
        created_at = (
            user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if getattr(user, "created_at", None)
            else "N/A"
        )
        return {
            "ready": True,
            "username": user.name,
            "display_name": getattr(user, "display_name", user.name),
            "id": user.id,
            "created_at": created_at,
            "avatar_url": avatar_url,
        }

    async def status(self, _request):
        return web.json_response(self._status_payload())

    async def profile(self, _request):
        return web.json_response(self._profile_payload())

    async def update_config(self, request):
        try:
            payload = await request.json()
            if "verified" in payload:
                self.bot.verified = bool(payload["verified"])
            if "spam_enabled" in payload:
                self.bot.spam_enabled = bool(payload["spam_enabled"])
                if self.bot.spam_enabled:
                    await self.ensure_spam_handler()
            if "spam_id" in payload:
                self.bot.spam_id = int(payload["spam_id"])
            if "interval" in payload:
                self.bot.interval = _parse_number_list(payload["interval"])
            if "languages" in payload:
                self.bot.languages = _parse_str_list(payload["languages"])
            if "whitelisted_channels" in payload:
                self.bot.whitelisted_channels = _parse_int_list(
                    payload["whitelisted_channels"]
                )
            if "blacklisted_pokemons" in payload:
                self.bot.blacklisted_pokemons = _parse_str_list(
                    payload["blacklisted_pokemons"]
                )
            if "min_spam_interval" in payload:
                self.bot.min_spam_interval = float(payload["min_spam_interval"])

            config = _read_config()
            config["LANGUAGES"] = self.bot.languages
            config["BLACKLISTED_POKEMONS"] = self.bot.blacklisted_pokemons
            config["WHITELISTED_CHANNELS"] = self.bot.whitelisted_channels
            config["SPAM"]["ENABLED"] = self.bot.spam_enabled
            config["SPAM"]["TIMING"] = self.bot.interval
            config["SPAM"]["SPAM_ID"] = self.bot.spam_id
            config.setdefault("SAFETY", {})
            config["SAFETY"]["MIN_SPAM_INTERVAL"] = self.bot.min_spam_interval
            _write_config(config)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            return web.json_response(
                {"success": False, "message": f"Invalid payload: {error}"}, status=400
            )
        return web.json_response({"success": True, "message": "Config updated"})

    async def ensure_spam_handler(self):
        if self.bot.get_cog("SpamHandler"):
            return
        try:
            await self.bot.load_extension("handlers.spam")
        except commands.ExtensionAlreadyLoaded:
            pass

    def _apply_runtime_config(self, config):
        self.bot.languages = config.get("LANGUAGES", self.bot.languages)
        self.bot.blacklisted_pokemons = config.get(
            "BLACKLISTED_POKEMONS", self.bot.blacklisted_pokemons
        )
        self.bot.whitelisted_channels = config.get(
            "WHITELISTED_CHANNELS", self.bot.whitelisted_channels
        )

        spam_cfg = config.get("SPAM", {})
        if "ENABLED" in spam_cfg:
            self.bot.spam_enabled = bool(spam_cfg.get("ENABLED"))
        if "SPAM_ID" in spam_cfg:
            self.bot.spam_id = int(spam_cfg.get("SPAM_ID") or 0)
        if "TIMING" in spam_cfg:
            self.bot.interval = _parse_number_list(spam_cfg.get("TIMING"))

        safety_cfg = config.get("SAFETY", {})
        if "MIN_SPAM_INTERVAL" in safety_cfg:
            self.bot.min_spam_interval = float(safety_cfg.get("MIN_SPAM_INTERVAL"))
        if "ACCOUNT_SPAM_COOLDOWN" in safety_cfg:
            self.bot.account_spam_cooldown = float(
                safety_cfg.get("ACCOUNT_SPAM_COOLDOWN")
            )
        if "GUILD_SPAM_COOLDOWN" in safety_cfg:
            self.bot.guild_spam_cooldown = float(safety_cfg.get("GUILD_SPAM_COOLDOWN"))
        if "MAX_CATCHES_24H" in safety_cfg:
            self.bot.max_catches_24h = int(safety_cfg.get("MAX_CATCHES_24H"))
        if "CATCH_WARNING_THRESHOLD" in safety_cfg:
            self.bot.catch_warning_threshold = int(
                safety_cfg.get("CATCH_WARNING_THRESHOLD")
            )

    async def get_raw_config(self, _request):
        return web.json_response({"success": True, "config": _read_config()})

    async def save_raw_config(self, request):
        try:
            payload = await request.json()
            config = payload.get("config")
            if not isinstance(config, dict):
                raise ValueError("config must be a JSON object")

            _write_config(config)
            self._apply_runtime_config(config)
            if self.bot.spam_enabled:
                await self.ensure_spam_handler()
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            return web.json_response(
                {"success": False, "message": f"Invalid config: {error}"}, status=400
            )

        return web.json_response({"success": True, "message": "Config saved"})

    async def _serve_page(self, filename):
        return web.FileResponse(path=WEB_DIR / filename)

    async def home_page(self, _request):
        return await self._serve_page("index.html")


async def setup(bot):
    await bot.add_cog(DashboardHandler(bot))
