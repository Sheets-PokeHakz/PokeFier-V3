function fmtSeconds(sec) {
  sec = Number(sec || 0);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return `${h}h ${m}m ${s}s`;
}

function line(label, value) {
  return `${label}: ${value}`;
}

function setPanel(id, content) {
  const box = document.querySelector(`#${id} .panel-content`);
  if (box) box.textContent = content;
}

async function fetchStatus() {
  const [statusRes, profileRes] = await Promise.all([
    fetch("/api/status"),
    fetch("/api/profile"),
  ]);
  const status = await statusRes.json();
  const profile = await profileRes.json();

  const statsText = [
    line("User", status.user),
    line("Display", profile.display_name || "N/A"),
    line("ID", profile.id || "N/A"),
    line("Verified", status.verified ? "YES" : "NO"),
    line("Spam", status.spam_enabled ? "ENABLED" : "DISABLED"),
    line("Latency", `${status.latency_ms} ms`),
    line("Uptime", fmtSeconds(status.uptime_seconds)),
    line("Catches", status.pokemons_caught),
    line("Catch 24h", `${status.catches_last_24h}/${status.max_catches_24h}`),
  ].join("\n");
  setPanel("statsPanel", statsText);

  const logsText = [
    line("Last Prediction", status.last_prediction ? `${status.last_prediction.name} (${status.last_prediction.score}%)` : "N/A"),
    line("Prediction At", status.last_prediction_at),
    line("Last Catch", status.last_caught ? `${status.last_caught.name} IV ${status.last_caught.iv}%` : "N/A"),
    line("Caught At", status.last_caught_at),
    line("Last Spam", status.last_spam ? status.last_spam.message : "N/A"),
    line("Spam At", status.last_spam_at),
    line("Next Spam", status.next_spam_at),
  ].join("\n");
  setPanel("logsPanel", logsText);

  const captchaActive = !status.verified ? "Possible captcha/paused state active" : "No active captcha state";
  setPanel(
    "captchaPanel",
    [
      line("State", captchaActive),
      line("Verified", status.verified ? "YES" : "NO"),
      line("24h catches", `${status.catches_last_24h}/${status.max_catches_24h}`),
    ].join("\n")
  );

  const pokemonsText = [
    line("Last caught", status.last_caught ? status.last_caught.name : "N/A"),
    line("Level", status.last_caught ? status.last_caught.level : "N/A"),
    line("IV", status.last_caught ? `${status.last_caught.iv}%` : "N/A"),
    line("Shiny", status.last_caught ? (status.last_caught.is_shiny ? "YES" : "NO") : "N/A"),
    line("Total catches", status.pokemons_caught),
  ].join("\n");
  setPanel("pokemonsPanel", pokemonsText);

  const accountsText = [
    line("Connected", "1 (single runtime instance)"),
    line("Languages", (status.languages || []).join(", ") || "N/A"),
    line("Whitelist", (status.whitelisted_channels || []).join(", ") || "N/A"),
    line("Blacklist", (status.blacklisted_pokemons || []).join(", ") || "N/A"),
  ].join("\n");
  setPanel("accountsPanel", accountsText);

  const autoText = [
    line("Spam Channel", status.spam_id || 0),
    line("Timing", (status.interval || []).join(", ") || "N/A"),
    line("Account Cooldown", `${status.account_spam_cooldown}s`),
    line("Guild Cooldown", `${status.guild_spam_cooldown}s`),
    line("Min Spam Interval", `${status.min_spam_interval}s`),
  ].join("\n");
  setPanel("autocatcherPanel", autoText);
}

async function loadRawConfig() {
  const statusBox = document.getElementById("configStatus");
  statusBox.textContent = "Loading config...";
  const res = await fetch("/api/config/raw");
  const data = await res.json();
  if (!data.success) {
    statusBox.textContent = "Failed to load config";
    return;
  }
  document.getElementById("rawConfigInput").value = JSON.stringify(data.config, null, 2);
  statusBox.textContent = "Config loaded";
}

function formatRawConfig() {
  const input = document.getElementById("rawConfigInput");
  const statusBox = document.getElementById("configStatus");
  try {
    const obj = JSON.parse(input.value);
    input.value = JSON.stringify(obj, null, 2);
    statusBox.textContent = "Formatted JSON";
  } catch (error) {
    statusBox.textContent = `JSON error: ${error.message}`;
  }
}

async function saveRawConfig() {
  const input = document.getElementById("rawConfigInput");
  const statusBox = document.getElementById("configStatus");
  let configObj;
  try {
    configObj = JSON.parse(input.value);
  } catch (error) {
    statusBox.textContent = `JSON error: ${error.message}`;
    return;
  }

  statusBox.textContent = "Saving config...";
  const res = await fetch("/api/config/raw", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config: configObj }),
  });
  const out = await res.json();
  statusBox.textContent = out.success ? "Config saved successfully" : `Save failed: ${out.message}`;
  if (out.success) {
    await fetchStatus();
  }
}

document.getElementById("reloadConfigBtn").addEventListener("click", loadRawConfig);
document.getElementById("formatConfigBtn").addEventListener("click", formatRawConfig);
document.getElementById("saveConfigBtn").addEventListener("click", saveRawConfig);

fetchStatus();
loadRawConfig();
setInterval(fetchStatus, 3000);
