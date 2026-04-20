import threading
import time
import sys
from collections import deque

from rich.console import Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class TerminalDashboard:
    def __init__(self):
        self._lock = threading.Lock()
        self._started = False
        self._stop_event = threading.Event()
        self._thread = None

        self.started_at = time.time()
        self.tokens = 0
        self.connected = 0

        self.logs = deque(maxlen=200)
        self.pokemon_logs = deque(maxlen=200)
        self.accounts = {}

        self.captchas_encountered = 0
        self.captchas_solved = 0
        self.captchas_failed = 0
        self.suspensions = 0

        self.catches_total = 0
        self.shiny_total = 0
        self.pokecoins = 0

        self.rares = {
            "leg": 0,
            "myth": 0,
            "ub": 0,
            "ev": 0,
            "reg": 0,
            "norm": 0,
        }

    def _append_log(self, level, message):
        ts = time.strftime("%H:%M:%S", time.localtime())
        self.logs.appendleft((level, ts, str(message)))

    def start(self, tokens):
        with self._lock:
            self.tokens = tokens
            if self._started:
                return
            if not sys.stdout.isatty():
                self._append_log("WARN", "TTY not detected; terminal dashboard disabled")
                return
            self._started = True
            self.started_at = time.time()
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            self._append_log("INFO", "Terminal dashboard started")

    def stop(self):
        if not self._started:
            return
        self._stop_event.set()

    def register_account(self, user_id, tag):
        with self._lock:
            if user_id not in self.accounts:
                self.accounts[user_id] = {
                    "tag": tag,
                    "connected": True,
                    "captcha": False,
                    "verified": False,
                    "spam_enabled": False,
                    "catches": 0,
                    "catches_24h": 0,
                    "max_24h": 0,
                }
                self.connected = len([a for a in self.accounts.values() if a["connected"]])
            else:
                self.accounts[user_id]["tag"] = tag
                self.accounts[user_id]["connected"] = True
            self._append_log("INFO", f"Account online: {tag}")

    def set_account_status(
        self,
        user_id,
        connected=None,
        captcha=None,
        verified=None,
        spam_enabled=None,
    ):
        with self._lock:
            account = self.accounts.get(user_id)
            if not account:
                return
            if connected is not None:
                account["connected"] = connected
            if captcha is not None:
                account["captcha"] = captcha
            if verified is not None:
                account["verified"] = verified
            if spam_enabled is not None:
                account["spam_enabled"] = spam_enabled
            self.connected = len([a for a in self.accounts.values() if a["connected"]])

    def info(self, message):
        with self._lock:
            self._append_log("INFO", message)

    def warn(self, message):
        with self._lock:
            self._append_log("WARN", message)

    def error(self, message):
        with self._lock:
            self._append_log("ERROR", message)

    def record_captcha(self, user_id, result):
        with self._lock:
            account = self.accounts.get(user_id)
            if account:
                account["captcha"] = result == "encountered"
            if result == "encountered":
                self.captchas_encountered += 1
                self._append_log("WARN", f"Captcha encountered on {user_id}")
            elif result == "solved":
                self.captchas_solved += 1
                self._append_log("INFO", f"Captcha solved on {user_id}")
            elif result == "failed":
                self.captchas_failed += 1
                self._append_log("ERROR", f"Captcha failed on {user_id}")

    def record_catch(self, user_id, pokemon_name, level, iv, shiny, rarity, channel_name):
        with self._lock:
            self.catches_total += 1
            if shiny:
                self.shiny_total += 1
            key = (rarity or "norm").lower()
            if key in self.rares:
                self.rares[key] += 1
            else:
                self.rares["norm"] += 1

            account = self.accounts.get(user_id)
            if account:
                account["catches"] += 1

            ts = time.strftime("%H:%M:%S", time.localtime())
            shiny_tag = "✨ " if shiny else ""
            self.pokemon_logs.appendleft(
                f"[{ts}] {shiny_tag}{pokemon_name} | L{level} | IV {iv}% | #{channel_name[-4:] if channel_name else 'N/A'}"
            )

    def record_spam(self, user_id, channel_id, delay_used):
        with self._lock:
            self._append_log(
                "DEBUG", f"Spam sent by {user_id} -> {channel_id} ({delay_used:.1f}s)"
            )

    def update_safety(self, user_id, catches_24h, max_24h):
        with self._lock:
            account = self.accounts.get(user_id)
            if not account:
                return
            account["catches_24h"] = catches_24h
            account["max_24h"] = max_24h

    def _uptime_text(self):
        diff = int(time.time() - self.started_at)
        h = diff // 3600
        m = (diff % 3600) // 60
        s = diff % 60
        return f"{h}h {m}m {s}s"

    def _build_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="top", size=3),
            Layout(name="mid", ratio=2),
            Layout(name="bottom", ratio=2),
            Layout(name="footer", size=3),
        )
        layout["mid"].split_row(
            Layout(name="stats", ratio=2),
            Layout(name="logs", ratio=5),
            Layout(name="captcha", ratio=2),
        )
        layout["bottom"].split_row(
            Layout(name="pokemons", ratio=4),
            Layout(name="accounts", ratio=4),
            Layout(name="safety", ratio=3),
        )

        title = Text("POKEFIER TERMINAL", style="bold magenta")
        layout["top"].update(Panel(title, border_style="magenta"))

        stats_table = Table.grid(padding=(0, 1))
        stats_table.add_row("Accounts", f"{self.connected}/{self.tokens}")
        stats_table.add_row("Uptime", self._uptime_text())
        stats_table.add_row(
            "Captcha T/S/F",
            f"{self.captchas_encountered}/{self.captchas_solved}/{self.captchas_failed}",
        )
        stats_table.add_row("Catches", str(self.catches_total))
        stats_table.add_row("Shiny", str(self.shiny_total))
        stats_table.add_row("Leg/Myth/UB", f"{self.rares['leg']}/{self.rares['myth']}/{self.rares['ub']}")
        stats_table.add_row("Ev/Reg/Norm", f"{self.rares['ev']}/{self.rares['reg']}/{self.rares['norm']}")
        layout["stats"].update(Panel(stats_table, title="Stats", border_style="cyan"))

        log_lines = []
        for level, ts, msg in list(self.logs)[:25]:
            if level == "ERROR":
                style = "red"
            elif level == "WARN":
                style = "yellow"
            elif level == "DEBUG":
                style = "blue"
            else:
                style = "green"
            log_lines.append(Text(f"[{level}] [{ts}] {msg}", style=style))
        layout["logs"].update(
            Panel(Group(*log_lines) if log_lines else "No logs yet", title="Logs", border_style="magenta")
        )

        captcha_lines = []
        for uid, account in self.accounts.items():
            if account["captcha"]:
                captcha_lines.append(f"{account['tag']} / {uid}")
        layout["captcha"].update(
            Panel(
                "\n".join(captcha_lines) if captcha_lines else "Live Captchas: 0",
                title="Captchas",
                border_style="red",
            )
        )

        pokelines = list(self.pokemon_logs)[:25]
        layout["pokemons"].update(
            Panel(
                "\n".join(pokelines) if pokelines else "Waiting for pokemons...",
                title="Pokemons",
                border_style="green",
            )
        )

        acc_table = Table(show_header=True, header_style="bold magenta")
        acc_table.add_column("#", width=3)
        acc_table.add_column("Account", overflow="fold")
        acc_table.add_column("Catches", justify="right")
        acc_table.add_column("Spam", justify="center")
        acc_table.add_column("Captcha", justify="center")

        for i, (uid, account) in enumerate(self.accounts.items(), start=1):
            acc_table.add_row(
                str(i),
                account["tag"],
                f"{account['catches']}",
                "ON" if account["spam_enabled"] else "OFF",
                "YES" if account["captcha"] else "NO",
            )
        layout["accounts"].update(Panel(acc_table, title="Crusers", border_style="purple"))

        safety_lines = []
        for _, account in self.accounts.items():
            if account["max_24h"] > 0:
                safety_lines.append(
                    f"{account['tag']}: {account['catches_24h']}/{account['max_24h']}"
                )
        if not safety_lines:
            safety_lines = ["No safety data yet"]
        layout["safety"].update(
            Panel("\n".join(safety_lines), title="AutoCatcher", border_style="yellow")
        )

        shortcuts = Text()
        shortcuts.append("Shortcuts: ", style="bold cyan")
        shortcuts.append("q", style="bold magenta")
        shortcuts.append(" quit  ", style="white")
        shortcuts.append("p", style="bold magenta")
        shortcuts.append(" pause-spam  ", style="white")
        shortcuts.append("r", style="bold magenta")
        shortcuts.append(" resume-spam  ", style="white")
        shortcuts.append("s", style="bold magenta")
        shortcuts.append(" solve-captcha-flag", style="white")
        layout["footer"].update(Panel(shortcuts, border_style="blue"))

        return layout

    def _run(self):
        with Live(self._build_layout(), refresh_per_second=4, screen=True) as live:
            while not self._stop_event.is_set():
                with self._lock:
                    live.update(self._build_layout())
                time.sleep(0.25)


terminal_dashboard = TerminalDashboard()
