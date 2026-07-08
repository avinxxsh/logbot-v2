"""
LogBot 2.0 — modernized for discord.py 2.x
Same soul as the original: per-server message logging + utility commands,
now with slash commands, DM-safe events, and no Replit keep_alive hack.

Requires: pip install -U discord.py python-dotenv
Privileged intents needed in the Developer Portal:
  - MESSAGE CONTENT (for logging message text)
  - SERVER MEMBERS (for /members export)
"""

import os
import random
import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

intents = discord.Intents.default()
intents.members = True          # privileged: needed for /members
intents.message_content = True  # privileged: needed to log message text

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def log_path(guild_id: int) -> Path:
    return LOG_DIR / f"{guild_id}.txt"


# ---------------- Events ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} slash command(s)")


@bot.event
async def on_message(message: discord.Message):
    # Ignore DMs and the bot's own messages (the old version crashed on DMs!)
    if message.guild is None or message.author == bot.user:
        return

    ts = datetime.datetime.now(IST).strftime("%d/%m/%Y %H:%M:%S IST")
    line = f"\n{ts}: message from {message.author}: {message.content} (in channel: {message.channel.name})"
    with open(log_path(message.guild.id), "a", encoding="utf-8") as f:
        f.write(line)

    # Reply to mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.channel.send("```yaml\ntype \"/help\" for more information```")

    await bot.process_commands(message)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    # Delete logs when kicked/removed from a server
    log_path(guild.id).unlink(missing_ok=True)
    print(f"Log file removed for guild {guild.id}")


# ---------------- Utility commands ----------------

@bot.tree.command(name="help", description="What LogBot does and how to use it")
async def help_cmd(interaction: discord.Interaction):
    text = (
        "```yaml\n"
        "LogBot maintains text logs of a server.\n\n"
        "Utility:\n"
        "- /test: Check if the bot is online\n"
        "- /ping: Check latency\n"
        "- /printlog: Get this server's log file (Manage Server required)\n"
        "- /clearlog: Clear this server's logs (Administrator required)\n"
        "- /members: Export all members + IDs as a text file (Manage Server required)\n"
        "- /serverid: Get this server's ID\n"
        "- /update: Info on the latest LogBot update\n\n"
        "Misc:\n"
        "- /rp: Make LogBot repeat what you say\n"
        "- /crystalball: Ask a yes/no question\n"
        "```"
    )
    await interaction.response.send_message(text, ephemeral=True)


@bot.tree.command(name="update", description="Latest LogBot changes")
async def update(interaction: discord.Interaction):
    await interaction.response.send_message(
        "```yaml\nLogBot Version: 2.0\n\n"
        "Changes:\n"
        "- Migrated to discord.py 2.x\n"
        "- All commands are now slash commands\n"
        "- Timestamps now in IST\n"
        "- DM-safe logging, logs stored under logs/\n"
        "- Replit keep_alive removed — runs as a proper 24/7 process```",
        ephemeral=True,
    )


@bot.tree.command(name="test", description="Check if LogBot is functioning")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("LogBot is functioning normally")


@bot.tree.command(name="ping", description="Check LogBot's latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! **{round(bot.latency * 1000, 1)}ms**")


@bot.tree.command(name="serverid", description="Get this server's ID")
@app_commands.guild_only()
async def serverid(interaction: discord.Interaction):
    await interaction.response.send_message(str(interaction.guild_id))


# ---------------- Log commands ----------------

@bot.tree.command(name="printlog", description="Get this server's log file")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_guild=True)
async def printlog(interaction: discord.Interaction):
    path = log_path(interaction.guild_id)
    if not path.exists() or path.stat().st_size == 0:
        await interaction.response.send_message("```No logs recorded yet.```", ephemeral=True)
        return
    if path.stat().st_size > 24_000_000:  # Discord upload limit safety
        await interaction.response.send_message(
            "```Log file too large to upload — consider /clearlog.```", ephemeral=True
        )
        return
    await interaction.response.send_message(file=discord.File(path))


@bot.tree.command(name="clearlog", description="Clear this server's logs")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def clearlog(interaction: discord.Interaction):
    open(log_path(interaction.guild_id), "w").close()
    await interaction.response.send_message("```SUCCESS: Log Cleared```")


@bot.tree.command(name="members", description="Export all members and their IDs")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_guild=True)
async def members(interaction: discord.Interaction):
    # Fetching every member can take a while on big servers → defer first
    await interaction.response.defer()
    out = LOG_DIR / f"users_{interaction.guild_id}.txt"
    with open(out, "w", encoding="utf-8") as f:
        async for member in interaction.guild.fetch_members(limit=None):
            f.write(f"{member}, User ID: {member.id}\n")
    await interaction.followup.send(file=discord.File(out))
    out.unlink(missing_ok=True)


# ---------------- Misc commands ----------------

@bot.tree.command(name="rp", description="Make LogBot repeat what you say")
@app_commands.describe(text="What should I say?")
async def rp(interaction: discord.Interaction, text: str):
    # allowed_mentions guard: stops people using the bot to ping @everyone
    await interaction.response.send_message(
        text, allowed_mentions=discord.AllowedMentions.none()
    )


@bot.tree.command(name="crystalball", description="Ask a yes/no question")
@app_commands.describe(question="Your question")
async def crystalball(interaction: discord.Interaction, question: str):
    choice = ["yes", "no", "maybe", "for sure", "um.. no?"]
    await interaction.response.send_message(
        f"> {question}\n🔮 {random.choice(choice)}",
        allowed_mentions=discord.AllowedMentions.none(),
    )


# ---------------- Error handling ----------------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = f"```ERROR: {error}```"
    else:
        msg = "```Unexpected error encountered!```"
        print(f"Error in /{interaction.command.name if interaction.command else '?'}: {error!r}")
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
