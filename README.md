# LogBot 2.0

Per-server message logging + utility commands, rebuilt for discord.py 2.x
with slash commands. Successor to the original LogBot (Stable.v6.1).

## Setup

1. **Discord Developer Portal** (discord.com/developers/applications)
   - Create an application → Bot tab → Reset Token, copy it
   - Enable **Message Content Intent** and **Server Members Intent**
   - OAuth2 → URL Generator → scopes: `bot` + `applications.commands`,
     permissions: Send Messages, Attach Files → invite via generated URL

2. **Local setup** (in VS Code's terminal)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # Mac/Linux
   pip install -r requirements.txt
   ```
   Then `Ctrl+Shift+P` → "Python: Select Interpreter" → pick `.venv`.

3. **Token**
   - Copy `.env.example` to `.env` and paste your bot token in.
   - `.env` is gitignored — never commit it.

4. **Run**
   - Press **F5** (uses `.vscode/launch.json`), or `python main.py`.
   - First global slash-command sync can take up to ~1 hour to appear
     in Discord. For instant testing, use guild-specific sync (see
     comments in `main.py`'s `on_ready`).

## Commands

| Command | Description | Permission |
|---|---|---|
| /help | Command list | — |
| /test | Health check | — |
| /ping | Latency | — |
| /serverid | Current server ID | — |
| /printlog | Upload this server's log file | Manage Server |
| /clearlog | Wipe this server's logs | Administrator |
| /members | Export members + IDs as a file | Manage Server |
| /rp | Repeat your text (mention-safe) | — |
| /crystalball | Yes/no oracle | — |
| /update | Changelog | — |

## Deployment (24/7 hosting)

No keep_alive hacks needed — run it as a persistent process:

- **Linux VPS / Oracle Cloud free tier**: use `deploy/logbot.service`
  (instructions in the file). systemd auto-restarts on crash and boot.
- **Docker / PaaS (Railway, Fly.io)**: build with `deploy/Dockerfile`.
  Deploy as a background worker, not a web service. Note: logs/ is
  ephemeral on most PaaS — use a volume or migrate to a database.
