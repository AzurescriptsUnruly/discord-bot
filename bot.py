import discord
import os
import time
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Your user ID - only you and the server owner can use /givetempac
OWNER_ID = 1408302737812099203

# Stores temp access: {user_id: expiry_timestamp}
temp_access = {}

def has_temp_access(user_id):
    if user_id in temp_access:
        if time.time() < temp_access[user_id]:
            return True
        else:
            del temp_access[user_id]
    return False

def can_grant_access(interaction: discord.Interaction):
    return (
        interaction.user.id == OWNER_ID or
        interaction.user.id == interaction.guild.owner_id
    )

# ── READY ──────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online! Logged in as {bot.user}")

# ── GRANT TEMP ACCESS ───────────────────────────────────────────────────────
@bot.tree.command(name="givetempac", description="Grant temporary mod access to a user (owner only)")
@app_commands.describe(user="The user to grant access to", days="Number of days (max 14)")
async def givetempac(interaction: discord.Interaction, user: discord.Member, days: int):
    if not can_grant_access(interaction):
        await interaction.response.send_message("⛔ Only the server owner or bot owner can use this command.", ephemeral=True)
        return

    if days < 1 or days > 14:
        await interaction.response.send_message("⛔ Duration must be between 1 and 14 days.", ephemeral=True)
        return

    expiry = time.time() + (days * 86400)
    temp_access[user.id] = expiry
    await interaction.response.send_message(f"✅ {user.mention} has been granted mod access for **{days} day(s)**!")

# ── REVOKE ACCESS ───────────────────────────────────────────────────────────
@bot.tree.command(name="revokeac", description="Revoke a user's temporary mod access (owner only)")
@app_commands.describe(user="The user to revoke access from")
async def revokeac(interaction: discord.Interaction, user: discord.Member):
    if not can_grant_access(interaction):
        await interaction.response.send_message("⛔ Only the server owner or bot owner can use this command.", ephemeral=True)
        return

    if user.id in temp_access:
        del temp_access[user.id]
        await interaction.response.send_message(f"✅ {user.mention}'s mod access has been revoked!")
    else:
        await interaction.response.send_message(f"⚠️ {user.mention} doesn't have any active access.", ephemeral=True)

# ── CHECK ACCESS ────────────────────────────────────────────────────────────
@bot.tree.command(name="checkac", description="Check if a user has temporary mod access")
@app_commands.describe(user="The user to check")
async def checkac(interaction: discord.Interaction, user: discord.Member):
    if not can_grant_access(interaction):
        await interaction.response.send_message("⛔ Only the server owner or bot owner can use this command.", ephemeral=True)
        return

    if has_temp_access(user.id):
        remaining = temp_access[user.id] - time.time()
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await interaction.response.send_message(f"✅ {user.mention} has active mod access! Expires in **{hours}h {minutes}m**.")
    else:
        await interaction.response.send_message(f"❌ {user.mention} does not have mod access.")

# ── BAN ─────────────────────────────────────────────────────────────────────
@bot.tree.command(name="ban", description="Ban a member")
@app_commands.describe(member="The member to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_temp_access(interaction.user.id) and not can_grant_access(interaction):
        await interaction.response.send_message("⛔ You don't have permission! Ask the owner for temporary access.", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been banned. Reason: {reason}")

# ── KICK ────────────────────────────────────────────────────────────────────
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.describe(member="The member to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_temp_access(interaction.user.id) and not can_grant_access(interaction):
        await interaction.response.send_message("⛔ You don't have permission! Ask the owner for temporary access.", ephemeral=True)
        return

    # Alert owner if someone tries to kick a bot
    if member.bot:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            await owner.send(f"⚠️ **Bot Kick Alert!**\n{interaction.user} (`{interaction.user.id}`) tried to kick the bot **{member}** in server **{interaction.guild.name}**!")
        await interaction.response.send_message("⛔ You cannot kick a bot!", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"✅ **{member}** has been kicked. Reason: {reason}")

# ── MUTE (TIMEOUT) ──────────────────────────────────────────────────────────
@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.describe(member="The member to mute", minutes="How many minutes to mute")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int):
    if not has_temp_access(interaction.user.id) and not can_grant_access(interaction):
        await interaction.response.send_message("⛔ You don't have permission! Ask the owner for temporary access.", ephemeral=True)
        return
    duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
    await member.timeout(duration)
    await interaction.response.send_message(f"✅ **{member}** has been muted for **{minutes} minute(s)**.")

# ── WARN ────────────────────────────────────────────────────────────────────
warnings = {}

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="The member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not has_temp_access(interaction.user.id) and not can_grant_access(interaction):
        await interaction.response.send_message("⛔ You don't have permission! Ask the owner for temporary access.", ephemeral=True)
        return
    if member.id not in warnings:
        warnings[member.id] = []
    warnings[member.id].append(reason)
    await interaction.response.send_message(f"⚠️ **{member}** has been warned. Reason: {reason} (Total warnings: {len(warnings[member.id])})")

# ── CLEAR ───────────────────────────────────────────────────────────────────
@bot.tree.command(name="clear", description="Delete messages in bulk")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if not has_temp_access(interaction.user.id) and not can_grant_access(interaction):
        await interaction.response.send_message("⛔ You don't have permission! Ask the owner for temporary access.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"✅ Deleted **{len(deleted)}** messages.", ephemeral=True)

# ── PING (TEST) ─────────────────────────────────────────────────────────────
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Bot is online! Latency: **{round(bot.latency * 1000)}ms**")

# ── TEST ACCESS (TEST) ───────────────────────────────────────────────────────
@bot.tree.command(name="testaccess", description="Test if you have temporary mod access")
async def testaccess(interaction: discord.Interaction):
    if has_temp_access(interaction.user.id):
        remaining = temp_access[interaction.user.id] - time.time()
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await interaction.response.send_message(f"✅ You have mod access! Expires in **{hours}h {minutes}m**.", ephemeral=True)
    elif can_grant_access(interaction):
        await interaction.response.send_message("✅ You have full access as the server/bot owner!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You do NOT have mod access. Ask the owner for access.", ephemeral=True)

bot.run(os.getenv("TOKEN"))