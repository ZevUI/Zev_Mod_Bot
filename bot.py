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
    print(f"Logged in as {bot.user}")
    print(f"Clearing ALL slash commands from guild: {GUILD_ID}")

    guild = discord.Object(id=GUILD_ID)

    try:
        # Clear every command currently stored in the local tree
        bot.tree.clear_commands(guild=guild)

        # Sync the EMPTY tree to Discord.
        # This is what actually removes the commands from Discord.
        commands_after = await bot.tree.sync(guild=guild)

        print("========================================")
        print("GUILD COMMAND CLEANUP COMPLETE")
        print("========================================")
        print(f"Commands remaining: {len(commands_after)}")

        if len(commands_after) == 0:
            print("SUCCESS: All guild commands have been removed.")
        else:
            print("WARNING: Some commands are still registered.")

    except Exception as error:
        print("========================================")
        print("COMMAND CLEANUP FAILED")
        print("========================================")
        print(error)

    await bot.close()


bot.run(TOKEN)
