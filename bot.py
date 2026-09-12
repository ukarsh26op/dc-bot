import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANEL_URL = os.getenv("PANEL_URL", "").rstrip("/")
PTERODACTYL_CLIENT_TOKEN = os.getenv("PTERODACTYL_CLIENT_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")
ALLOWED_ROLE_ID = os.getenv("ALLOWED_ROLE_ID")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")
if not PANEL_URL:
    raise RuntimeError("PANEL_URL is missing")
if not PTERODACTYL_CLIENT_TOKEN:
    raise RuntimeError("PTERODACTYL_CLIENT_TOKEN is missing")
if not SERVER_ID:
    raise RuntimeError("SERVER_ID is missing")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def allowed(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        return False

    # Server administrators can always use the commands.
    if interaction.user.guild_permissions.administrator:
        return True

    # Optional role restriction.
    if ALLOWED_ROLE_ID:
        return any(str(role.id) == ALLOWED_ROLE_ID for role in interaction.user.roles)

    # If no role is configured, allow members to use the commands.
    return True

async def power(action: str):
    url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}/power"
    headers = {
        "Authorization": f"Bearer {PTERODACTYL_CLIENT_TOKEN}",
        "Accept": "Application/vnd.pterodactyl.v1+json",
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, headers=headers, json={"signal": action}) as response:
            text = await response.text()

            if response.status == 204:
                return True, ""

            return False, f"HTTP {response.status}: {text[:500]}"

async def get_status():
    url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}/resources"
    headers = {
        "Authorization": f"Bearer {PTERODACTYL_CLIENT_TOKEN}",
        "Accept": "Application/vnd.pterodactyl.v1+json",
    }

    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            text = await response.text()

            if response.status != 200:
                return None, f"HTTP {response.status}: {text[:500]}"

            data = await response.json()
            state = data.get("attributes", {}).get("current_state", "unknown")
            return state, None

async def check(interaction: discord.Interaction) -> bool:
    if not allowed(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True,
        )
        return False
    return True

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Logged in as {bot.user}")
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Slash-command sync failed: {e}")

@bot.tree.command(name="startserver", description="Start the Minecraft server")
async def startserver(interaction: discord.Interaction):
    if not await check(interaction):
        return

    await interaction.response.defer()
    ok, error = await power("start")

    if ok:
        await interaction.followup.send("🟢 **Start signal sent!** The Minecraft server is starting.")
    else:
        await interaction.followup.send(f"❌ Could not start the server.\n```{error}```")

@bot.tree.command(name="stopserver", description="Stop the Minecraft server")
async def stopserver(interaction: discord.Interaction):
    if not await check(interaction):
        return

    await interaction.response.defer()
    ok, error = await power("stop")

    if ok:
        await interaction.followup.send("🔴 **Stop signal sent!**")
    else:
        await interaction.followup.send(f"❌ Could not stop the server.\n```{error}```")

@bot.tree.command(name="restartserver", description="Restart the Minecraft server")
async def restartserver(interaction: discord.Interaction):
    if not await check(interaction):
        return

    await interaction.response.defer()
    ok, error = await power("restart")

    if ok:
        await interaction.followup.send("🔄 **Restart signal sent!**")
    else:
        await interaction.followup.send(f"❌ Could not restart the server.\n```{error}```")

@bot.tree.command(name="status", description="Check the Minecraft server status")
async def status(interaction: discord.Interaction):
    if not await check(interaction):
        return

    await interaction.response.defer()
    state, error = await get_status()

    if error:
        await interaction.followup.send(f"❌ Could not get status.\n```{error}```")
        return

    emoji = {
        "running": "🟢",
        "starting": "🟡",
        "stopping": "🟠",
        "offline": "🔴",
    }.get(state.lower(), "⚪")

    await interaction.followup.send(f"{emoji} **Minecraft server:** `{state}`")

@bot.tree.command(name="testapi", description="Test the Pterodactyl API connection")
async def testapi(interaction: discord.Interaction):
    if not await check(interaction):
        return

    await interaction.response.defer()
    state, error = await get_status()

    if error:
        await interaction.followup.send(f"❌ API test failed.\n```{error}```")
    else:
        await interaction.followup.send(
            f"✅ **Pterodactyl API is working.**\nCurrent server state: `{state}`"
        )

bot.run(DISCORD_TOKEN)
