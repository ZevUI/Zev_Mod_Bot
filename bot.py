import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")

if not GUILD_ID:
    raise RuntimeError("GUILD_ID is not set.")

bot = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.none()
)


@bot.event
async def on_ready():
    print("========================================")
    print("ZEHUB COMMAND INSPECTOR")
    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Guild ID: {GUILD_ID}")
    print()

    guild = discord.Object(id=GUILD_ID)

    # ----------------------------------------
    # GUILD COMMANDS
    # ----------------------------------------

    try:
        guild_commands = await bot.tree.fetch_commands(guild=guild)

        print("========== GUILD COMMANDS ==========")
        print(f"Total: {len(guild_commands)}")
        print()

        for command in guild_commands:
            print(
                f"/{command.name} | "
                f"ID: {command.id} | "
                f"Description: {command.description}"
            )

    except Exception as error:
        print(f"Guild command error: {error}")

    print()

    # ----------------------------------------
    # GLOBAL COMMANDS
    # ----------------------------------------

    try:
        global_commands = await bot.tree.fetch_commands()

        print("========== GLOBAL COMMANDS ==========")
        print(f"Total: {len(global_commands)}")
        print()

        for command in global_commands:
            print(
                f"/{command.name} | "
                f"ID: {command.id} | "
                f"Description: {command.description}"
            )

    except Exception as error:
        print(f"Global command error: {error}")

    print()
    print("========================================")
    print("INSPECTION COMPLETE")
    print("========================================")

    await bot.close()


bot.run(TOKEN)
