import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")

bot = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.none()
)


@bot.event
async def on_ready():
    print("========================================")
    print("ZEHUB GLOBAL COMMAND CLEANUP")
    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print()

    try:
        # Fetch currently registered GLOBAL commands
        global_commands = await bot.tree.fetch_commands()

        print(f"Found {len(global_commands)} global commands.")
        print()

        for command in global_commands:
            print(f"Removing /{command.name} (ID: {command.id})")

        # Clear the local global command tree
        bot.tree.clear_commands(guild=None)

        # Sync the empty global tree to Discord
        await bot.tree.sync()

        # Verify
        remaining = await bot.tree.fetch_commands()

        print()
        print("========================================")
        print("GLOBAL COMMAND CLEANUP COMPLETE")
        print("========================================")
        print(f"Global commands remaining: {len(remaining)}")

        if len(remaining) == 0:
            print("SUCCESS: All global commands have been removed.")
        else:
            print("WARNING: Some global commands are still present.")

    except Exception as error:
        print("========================================")
        print("CLEANUP FAILED")
        print("========================================")
        print(error)

    await bot.close()


bot.run(TOKEN)
