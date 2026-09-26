import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.none()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Removing all commands from guild: {GUILD_ID}")

    guild = discord.Object(id=GUILD_ID)

    # Get all currently registered guild commands
    commands_list = await bot.tree.fetch_commands(
        guild=guild
    )

    print(f"Found {len(commands_list)} guild commands.")

    # Delete every guild command
    for command in commands_list:
        try:
            await bot.tree.delete_command(
                command.id,
                guild=guild
            )
            print(f"Deleted: /{command.name}")
        except Exception as error:
            print(f"Failed to delete /{command.name}: {error}")

    print("Finished removing guild commands.")
    print("You can now stop this bot and deploy your normal bot.")
    
    await bot.close()


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set.")

if not GUILD_ID:
    raise RuntimeError("GUILD_ID is not set.")

bot.run(TOKEN)
