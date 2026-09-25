import os
import asyncio
import json
import random
import re
import logging
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("ZevHub")


# =========================================================
# ZEV HUB CONFIG
# =========================================================

TOKEN = os.getenv("DISCORD_TOKEN")

BRAND = "ZeHub"
FOOTER = "ZeHub • Moderation"

GUILD_ID = 1539039438976585900
GUILD = discord.Object(id=GUILD_ID)

# Giveaway claim/ticket channel
CLAIM_TICKET_URL = "https://discord.com/channels/1424741330315378700/1544028216027521034"
GIVEAWAY_IMAGE_FILE = "ZeHub-giveaways.jpeg"
GIVEAWAY_IMAGE_NAME = "ZeHub-giveaways.jpeg"


def parse_duration(value: str):
    """Convert 1h, 2d, 1w or combined values such as 1d6h to minutes."""
    value = value.strip().lower().replace(" ", "")
    if not value:
        raise ValueError("Duration cannot be empty.")

    matches = re.findall(r"(\d+)([mhdw])", value)
    if not matches or "".join(f"{n}{u}" for n, u in matches) != value:
        raise ValueError("Use formats like 30m, 1h, 1d, 2d, 1w or 1d6h.")

    multipliers = {"m": 1, "h": 60, "d": 1440, "w": 10080}
    minutes = sum(int(number) * multipliers[unit] for number, unit in matches)

    if minutes < 1:
        raise ValueError("Duration must be at least 1 minute.")
    if minutes > 43200:
        raise ValueError("Maximum giveaway duration is 30 days.")

    return minutes


def format_duration(minutes: int):
    """Display minutes as a clean human-readable duration."""
    parts = []
    remaining = int(minutes)

    for unit_minutes, suffix in ((10080, "w"), (1440, "d"), (60, "h"), (1, "m")):
        amount, remaining = divmod(remaining, unit_minutes)
        if amount:
            parts.append(f"{amount}{suffix}")

    return " ".join(parts) or "0m"


# =========================================================
# BOT SETUP
# =========================================================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# GIVEAWAY STORAGE
# =========================================================

giveaways = {}
giveaway_counter = 0


# =========================================================
# WARNING STORAGE
# =========================================================

WARNINGS_FILE = "warnings.json"


def load_warnings():

    try:

        with open(
            WARNINGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            return (
                data
                if isinstance(data, dict)
                else {}
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


warnings = load_warnings()


def save_warnings():

    with open(
        WARNINGS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            warnings,
            file,
            indent=2
        )


def get_user_warnings(
    guild_id,
    user_id
):

    guild_warnings = warnings.get(
        str(guild_id),
        {}
    )

    return guild_warnings.get(
        str(user_id),
        []
    )


# =========================================================
# PING ON JOIN STORAGE
# =========================================================

POJ_FILE = "poj_config.json"

POJ_DEFAULT_MESSAGE = "👋 Welcome {user} to {server}!\n\n🔐 **Verify now** to access the scripts & keys.\n✅ Complete the verification to unlock access."
POJ_DEFAULT_DELAY = 0.1


def load_poj_config():

    try:

        with open(
            POJ_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            return (
                data
                if isinstance(data, dict)
                else {}
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


poj_channels = load_poj_config()


# =========================================================
# AUTO ROLE STORAGE
# =========================================================

AUTOROLE_FILE = "autorole_config.json"


def load_autorole_config():
    try:
        with open(
            AUTOROLE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

            return (
                data
                if isinstance(data, dict)
                else {}
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):
        return {}


def save_autorole_config():
    with open(
        AUTOROLE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            autorole_config,
            file,
            indent=2
        )


autorole_config = load_autorole_config()


def save_poj_config():

    with open(
        POJ_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            poj_channels,
            file,
            indent=2
        )


def format_poj_message(
    template,
    member
):

    return (
        template
        .replace(
            "{user}",
            member.mention
        )
        .replace(
            "{username}",
            member.display_name
        )
        .replace(
            "{server}",
            member.guild.name
        )
        .replace(
            "{count}",
            str(member.guild.member_count or 0)
        )
    )


# =========================================================
# DISCORD LOG CHANNEL CONFIG
# =========================================================

LOGS_FILE = "logs_config.json"


LOG_TYPES = {
    "member_join": "Member Joins",
    "member_leave": "Member Leaves",
    "moderation": "Moderation",
    "messages": "Messages",
    "commands": "Commands",
    "giveaways": "Giveaways",
    "reaction_roles": "Reaction Roles",
    "announcements": "Announcements",
    "dm": "DMs",
    "poj": "Ping On Join"
}


def load_log_config():

    try:

        with open(
            LOGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            return (
                data
                if isinstance(data, dict)
                else {}
            )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


log_channels = load_log_config()


def save_log_config():

    with open(
        LOGS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            log_channels,
            file,
            indent=2
        )


def get_log_channel_id(
    guild_id,
    log_type
):

    guild_config = log_channels.get(
        str(guild_id),
        {}
    )

    return guild_config.get(
        log_type
    )


def get_log_channel(
    guild,
    log_type
):

    channel_id = get_log_channel_id(
        guild.id,
        log_type
    )

    if channel_id is None:
        return None

    return guild.get_channel(
        int(channel_id)
    )


async def send_log(
    guild,
    log_type,
    title,
    description,
    color=discord.Color.blurple(),
    fields=None
):

    if guild is None:
        return

    channel = get_log_channel(
        guild,
        log_type
    )

    if channel is None:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )

    if fields:

        for field_name, field_value, inline in fields:

            embed.add_field(
                name=field_name,
                value=str(field_value),
                inline=inline
            )

    embed.set_footer(
        text=(
            f"{BRAND} • "
            f"{LOG_TYPES.get(log_type, log_type)}"
        )
    )

    try:

        await channel.send(
            embed=embed
        )

    except discord.Forbidden:

        logger.error(
            "Cannot send %s logs to #%s (%s).",
            log_type,
            channel.name,
            channel.id
        )

    except discord.HTTPException as error:

        logger.error(
            "Failed to send %s log: %s",
            log_type,
            error
        )


# =========================================================
# LOG TYPE CHOICES
# =========================================================

LOG_CHOICES = [
    app_commands.Choice(
        name="Member Joins",
        value="member_join"
    ),
    app_commands.Choice(
        name="Member Leaves",
        value="member_leave"
    ),
    app_commands.Choice(
        name="Moderation",
        value="moderation"
    ),
    app_commands.Choice(
        name="Messages",
        value="messages"
    ),
    app_commands.Choice(
        name="Commands",
        value="commands"
    ),
    app_commands.Choice(
        name="Giveaways",
        value="giveaways"
    ),
    app_commands.Choice(
        name="Reaction Roles",
        value="reaction_roles"
    ),
    app_commands.Choice(
        name="Announcements",
        value="announcements"
    ),
    app_commands.Choice(
        name="DMs",
        value="dm"
    ),
    app_commands.Choice(
        name="Ping On Join",
        value="poj"
    )
]


# =========================================================
# /LOGS GROUP
# =========================================================

logs_group = app_commands.Group(
    name="logs",
    description="Configure Zev Hub logging"
)


# =========================================================
# /LOGS SET
# =========================================================

@logs_group.command(
    name="set",
    description="Set the channel for a type of log"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    log_type="Type of log",
    channel="Channel where the logs should be sent"
)
@app_commands.choices(
    log_type=LOG_CHOICES
)
async def logs_set(
    interaction: discord.Interaction,
    log_type: str,
    channel: discord.TextChannel
):

    guild_key = str(
        interaction.guild.id
    )

    guild_config = log_channels.setdefault(
        guild_key,
        {}
    )

    guild_config[log_type] = channel.id

    save_log_config()

    logger.info(
        "Log channel set by %s (%s): %s -> #%s (%s)",
        interaction.user,
        interaction.user.id,
        log_type,
        channel.name,
        channel.id
    )

    await interaction.response.send_message(
        f"✅ **{LOG_TYPES[log_type]}** logs will now "
        f"be sent to {channel.mention}.",
        ephemeral=True
    )


# =========================================================
# /LOGS DISABLE
# =========================================================

@logs_group.command(
    name="disable",
    description="Disable a type of logging"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    log_type="Type of log to disable"
)
@app_commands.choices(
    log_type=LOG_CHOICES
)
async def logs_disable(
    interaction: discord.Interaction,
    log_type: str
):

    guild_key = str(
        interaction.guild.id
    )

    guild_config = log_channels.get(
        guild_key,
        {}
    )

    if log_type not in guild_config:

        await interaction.response.send_message(
            f"ℹ️ **{LOG_TYPES[log_type]}** logging "
            f"is already disabled.",
            ephemeral=True
        )

        return

    del guild_config[log_type]

    if not guild_config:

        log_channels.pop(
            guild_key,
            None
        )

    save_log_config()

    logger.info(
        "Log type disabled by %s (%s): %s",
        interaction.user,
        interaction.user.id,
        log_type
    )

    await interaction.response.send_message(
        f"✅ **{LOG_TYPES[log_type]}** logging "
        f"has been disabled.",
        ephemeral=True
    )


# =========================================================
# /LOGS LIST
# =========================================================

@logs_group.command(
    name="list",
    description="Show all configured log channels"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def logs_list(
    interaction: discord.Interaction
):

    guild_config = log_channels.get(
        str(interaction.guild.id),
        {}
    )

    embed = discord.Embed(
        title="📋 Zev Hub Logging",
        description="Current logging configuration.",
        color=discord.Color.blurple()
    )

    for log_type, display_name in LOG_TYPES.items():

        channel_id = guild_config.get(
            log_type
        )

        if channel_id:

            channel = interaction.guild.get_channel(
                int(channel_id)
            )

            if channel:

                value = channel.mention

            else:

                value = (
                    f"Unknown channel "
                    f"`{channel_id}`"
                )

        else:

            value = "❌ Disabled"

        embed.add_field(
            name=display_name,
            value=value,
            inline=False
        )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# /LOGS RESET
# =========================================================

@logs_group.command(
    name="reset",
    description="Disable all logging for this server"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def logs_reset(
    interaction: discord.Interaction
):

    guild_key = str(
        interaction.guild.id
    )

    if guild_key not in log_channels:

        await interaction.response.send_message(
            "ℹ️ Logging is already completely disabled.",
            ephemeral=True
        )

        return

    log_channels.pop(
        guild_key,
        None
    )

    save_log_config()

    logger.info(
        "All logging disabled by %s (%s).",
        interaction.user,
        interaction.user.id
    )

    await interaction.response.send_message(
        "✅ All Zev Hub logging has been disabled "
        "for this server.",
        ephemeral=True
    )


bot.tree.add_command(
    logs_group,
    guild=GUILD
)


# =========================================================
# REACTION ROLES
# =========================================================

REACTION_ROLE_MESSAGE_ID = 1548082945573650444

REACTION_ROLE_CHANNEL_ID = 1548075290423595099


REACTION_ROLES = {
    "💻": 1548086296977604648,
    "📢": 1548086430633431061,
    "🎥": 1548086556273942538,
    "🎁": 1548086141427650561
}


async def setup_reaction_roles():

    channel = bot.get_channel(
        REACTION_ROLE_CHANNEL_ID
    )

    if channel is None:

        try:

            channel = await bot.fetch_channel(
                REACTION_ROLE_CHANNEL_ID
            )

        except Exception as error:

            logger.error(
                "Reaction role channel could not be found: %s",
                error
            )

            return

    try:

        message = await channel.fetch_message(
            REACTION_ROLE_MESSAGE_ID
        )

        for emoji in REACTION_ROLES:

            try:

                await message.add_reaction(
                    emoji
                )

            except discord.HTTPException as error:

                logger.error(
                    "Could not add %s reaction: %s",
                    emoji,
                    error
                )

        logger.info(
            "Reaction role reactions are ready."
        )

    except discord.NotFound:

        logger.error(
            "Reaction role message could not be found."
        )

    except discord.Forbidden:

        logger.error(
            "I don't have permission to access "
            "the reaction role message."
        )

    except Exception as error:

        logger.exception(
            "Reaction role setup error: %s",
            error
        )


async def handle_reaction_role(
    payload,
    adding
):

    if payload.guild_id != GUILD_ID:
        return

    if payload.message_id != REACTION_ROLE_MESSAGE_ID:
        return

    if (
        bot.user is not None
        and payload.user_id == bot.user.id
    ):
        return

    emoji = str(
        payload.emoji
    )

    role_id = REACTION_ROLES.get(
        emoji
    )

    if role_id is None:
        return

    guild = bot.get_guild(
        payload.guild_id
    )

    if guild is None:
        return

    member = guild.get_member(
        payload.user_id
    )

    if member is None:

        try:

            member = await guild.fetch_member(
                payload.user_id
            )

        except discord.HTTPException:

            return

    if member.bot:
        return

    role = guild.get_role(
        role_id
    )

    if role is None:

        logger.error(
            "Reaction role %s was not found.",
            role_id
        )

        return

    try:

        if adding:

            await member.add_roles(
                role,
                reason=f"{BRAND} Reaction Role"
            )

            logger.info(
                "Gave role '%s' to %s (%s)",
                role.name,
                member,
                member.id
            )

            await send_log(
                guild,
                "reaction_roles",
                "🎭 Reaction Role Added",
                f"{member.mention} received a reaction role.",
                discord.Color.green(),
                [
                    (
                        "Member",
                        f"{member} (`{member.id}`)",
                        True
                    ),
                    (
                        "Role",
                        role.mention,
                        True
                    ),
                    (
                        "Emoji",
                        emoji,
                        True
                    )
                ]
            )

        else:

            await member.remove_roles(
                role,
                reason=f"{BRAND} Reaction Role"
            )

            logger.info(
                "Removed role '%s' from %s (%s)",
                role.name,
                member,
                member.id
            )

            await send_log(
                guild,
                "reaction_roles",
                "🎭 Reaction Role Removed",
                f"{member.mention} lost a reaction role.",
                discord.Color.orange(),
                [
                    (
                        "Member",
                        f"{member} (`{member.id}`)",
                        True
                    ),
                    (
                        "Role",
                        role.mention,
                        True
                    ),
                    (
                        "Emoji",
                        emoji,
                        True
                    )
                ]
            )

    except discord.Forbidden:

        logger.error(
            "Cannot manage role '%s'. "
            "Make sure the bot's role is above it.",
            role.name
        )

    except discord.HTTPException as error:

        logger.error(
            "Reaction role error: %s",
            error
        )


@bot.event
async def on_raw_reaction_add(
    payload
):

    await handle_reaction_role(
        payload,
        True
    )


@bot.event
async def on_raw_reaction_remove(
    payload
):

    await handle_reaction_role(
        payload,
        False
    )


# =========================================================
# GIVEAWAY BUTTONS
# =========================================================

class GiveawayView(discord.ui.View):

    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="🎟️ Enter Giveaway",
        style=discord.ButtonStyle.blurple
    )
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):

        giveaway = giveaways.get(self.giveaway_id)

        if giveaway is None:
            await interaction.response.send_message(
                "❌ This giveaway no longer exists.",
                ephemeral=True
            )
            return

        if giveaway["ended"]:
            await interaction.response.send_message(
                "❌ This giveaway has already ended.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id

        if user_id in giveaway["entries"]:
            giveaway["entries"].remove(user_id)
            message = "❌ You have left the giveaway."
            logger.info(
                "User %s (%s) left giveaway #%s",
                interaction.user, user_id, self.giveaway_id
            )
        else:
            giveaway["entries"].add(user_id)
            message = "✅ You have entered the giveaway!"
            logger.info(
                "User %s (%s) entered giveaway #%s",
                interaction.user, user_id, self.giveaway_id
            )

        await interaction.response.send_message(message, ephemeral=True)
        await update_giveaway_message(self.giveaway_id)

        await send_log(
            interaction.guild,
            "giveaways",
            "🎟️ Giveaway Entry Updated",
            f"{interaction.user.mention} updated their giveaway entry.",
            discord.Color.blurple(),
            [
                ("Giveaway", f"#{self.giveaway_id}", True),
                ("Prize", giveaway["prize"], True),
                ("Entries", len(giveaway["entries"]), True)
            ]
        )


class GiveawayClaimView(discord.ui.View):
    """Link button for winners to reach the separate ticket system."""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="🎟️ Claim Giveaway",
                style=discord.ButtonStyle.link,
                url=CLAIM_TICKET_URL
            )
        )


class GiveawayEndedView(GiveawayClaimView):
    pass


# =========================================================
# UPDATE GIVEAWAY MESSAGE
# =========================================================

async def update_giveaway_message(
    giveaway_id
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:
        return

    channel = bot.get_channel(
        giveaway["channel_id"]
    )

    if channel is None:
        return

    try:

        message = await channel.fetch_message(
            giveaway["message_id"]
        )

        embed = discord.Embed(
            title="🎉 ZEV HUB GIVEAWAY",
            description=(
                f"{giveaway['description']}\n\n"
                "🎟️ **Click the button below to enter.**"
            ),
            color=discord.Color.from_rgb(30, 100, 255)
        )

        embed.add_field(
            name="🎁 Prize",
            value=f"**{giveaway['prize']}**",
            inline=False
        )
        embed.add_field(
            name="🏆 Winners",
            value=f"`{giveaway['winners']}`",
            inline=True
        )
        embed.add_field(
            name="👥 Entries",
            value=f"`{len(giveaway['entries'])}`",
            inline=True
        )
        embed.add_field(
            name="⏰ Ends",
            value=(
                f"{discord.utils.format_dt(giveaway['end_time'], style='R')}\n"
                f"{discord.utils.format_dt(giveaway['end_time'], style='f')}"
            ),
            inline=False
        )
        embed.add_field(
            name="📋 Duration",
            value=f"`{format_duration(giveaway['duration'])}`",
            inline=True
        )
        embed.add_field(
            name="🎟️ How to enter",
            value="Press **Enter Giveaway** below. Press it again to leave.",
            inline=True
        )
        embed.set_image(url=f"attachment://{GIVEAWAY_IMAGE_NAME}")
        embed.set_footer(
            text=f"{BRAND} • Giveaway #{giveaway_id} • Hosted by <@{giveaway['host']}>"
        )

        await message.edit(
            embed=embed,
            view=GiveawayView(
                giveaway_id
            )
        )

    except discord.NotFound:
        pass

    except discord.Forbidden:

        logger.error(
            "No permission to update giveaway #%s",
            giveaway_id
        )

    except Exception as error:

        logger.exception(
            "Giveaway update error for #%s: %s",
            giveaway_id,
            error
        )


# =========================================================
# FINISH GIVEAWAY
# =========================================================

async def finish_giveaway(
    giveaway_id,
    manual=False
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:
        return

    if giveaway["ended"]:
        return

    giveaway["ended"] = True

    logger.info(
        "Ending giveaway #%s (%s)",
        giveaway_id,
        "manual" if manual else "automatic"
    )

    channel = bot.get_channel(
        giveaway["channel_id"]
    )

    if channel is None:
        return

    entries = list(
        giveaway["entries"]
    )

    winner_count = min(
        giveaway["winners"],
        len(entries)
    )

    if winner_count > 0:

        winners = random.sample(
            entries,
            winner_count
        )

        mentions = " ".join(
            f"<@{user_id}>"
            for user_id in winners
        )

    else:

        winners = []

        mentions = (
            "Nobody entered the giveaway."
        )

    embed = discord.Embed(
        title="🏆 ZEV HUB GIVEAWAY ENDED",
        description=(
            f"🎁 **Prize**\n{giveaway['prize']}\n\n"
            f"🏆 **Winner(s)**\n{mentions}\n\n"
            f"👥 **Entries**\n`{len(entries)}`\n\n"
            "🎟️ **Winners:** click **Claim Giveaway** below, "
            "open a ticket, and say **Giveaway Winner**."
        ),
        color=discord.Color.green()
    )
    embed.set_image(url=f"attachment://{GIVEAWAY_IMAGE_NAME}")
    embed.set_footer(text=f"{BRAND} • Giveaway #{giveaway_id}")

    try:

        message = await channel.fetch_message(
            giveaway["message_id"]
        )

        await message.edit(
            embed=embed,
            view=GiveawayEndedView()
        )

    except discord.NotFound:
        pass

    except Exception as error:

        logger.exception(
            "Giveaway message error for #%s: %s",
            giveaway_id,
            error
        )

    await channel.send(
        content=(
            f"🏆 **GIVEAWAY WINNER{'S' if len(winners) != 1 else ''}!**\n\n"
            f"{mentions}\n\n"
            f"🎁 **Prize:** {giveaway['prize']}\n"
            "🎟️ **Claim your prize:** Click **Claim Giveaway**, "
            "open a ticket, and say **Giveaway Winner**."
        ),
        view=GiveawayClaimView(),
        allowed_mentions=discord.AllowedMentions(users=True)
    )

    giveaway["winners_selected"] = winners

    logger.info(
        "Giveaway #%s finished with %s entries and %s winner(s).",
        giveaway_id,
        len(entries),
        len(winners)
    )

    await send_log(
        channel.guild,
        "giveaways",
        "🎉 Giveaway Ended",
        f"Giveaway **#{giveaway_id}** has ended.",
        discord.Color.green(),
        [
            (
                "Prize",
                giveaway["prize"],
                True
            ),
            (
                "Entries",
                len(entries),
                True
            ),
            (
                "Winners",
                mentions,
                False
            ),
            (
                "Ended",
                "Manually" if manual else "Automatically",
                True
            )
        ]
    )


# =========================================================
# GIVEAWAY TIMER
# =========================================================

async def giveaway_timer(
    giveaway_id
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:
        return

    seconds = (
        giveaway["end_time"]
        - discord.utils.utcnow()
    ).total_seconds()

    if seconds > 0:

        await asyncio.sleep(
            seconds
        )

    await finish_giveaway(
        giveaway_id
    )


# =========================================================
# GIVEAWAY COMMAND GROUP
# =========================================================

giveaway_group = app_commands.Group(
    name="giveaway",
    description="Zev Hub giveaway commands"
)


# =========================================================
# /GIVEAWAY CREATE
# =========================================================

@giveaway_group.command(
    name="create",
    description="Create a giveaway"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    prize="What people can win",
    duration="Duration: 30m, 1h, 1d, 2d, 1w...",
    winners="Number of winners",
    channel="Channel to host the giveaway in",
    description="Giveaway description",
    ping_everyone="Ping @everyone when the giveaway starts"
)
async def giveaway_create(
    interaction: discord.Interaction,
    prize: str,
    duration: str,
    winners: int,
    channel: discord.TextChannel = None,
    description: str = "Click the button below to enter!",
    ping_everyone: bool = False
):

    global giveaway_counter

    try:
        duration_minutes = parse_duration(duration)
    except ValueError as error:
        await interaction.response.send_message(
            f"❌ {error}",
            ephemeral=True
        )
        return

    if winners < 1:

        await interaction.response.send_message(
            "❌ You need at least 1 winner.",
            ephemeral=True
        )

        return

    if winners > 50:

        await interaction.response.send_message(
            "❌ Maximum of 50 winners.",
            ephemeral=True
        )

        return

    if channel is None:
        channel = interaction.channel

    giveaway_counter += 1

    giveaway_id = giveaway_counter

    end_time = (
        discord.utils.utcnow()
        + timedelta(minutes=duration_minutes)
    )

    giveaways[giveaway_id] = {
        "prize": prize,
        "description": description,
        "winners": winners,
        "channel_id": channel.id,
        "message_id": None,
        "end_time": end_time,
        "duration": duration_minutes,
        "entries": set(),
        "ended": False,
        "host": interaction.user.id,
        "winners_selected": []
    }

    embed = discord.Embed(
        title="🎉 ZEV HUB GIVEAWAY",
        description=(
            f"{description}\n\n"
            "🎟️ **Click the button below to enter.**"
        ),
        color=discord.Color.from_rgb(30, 100, 255)
    )
    embed.add_field(name="🎁 Prize", value=f"**{prize}**", inline=False)
    embed.add_field(name="🏆 Winners", value=f"`{winners}`", inline=True)
    embed.add_field(name="👥 Entries", value="`0`", inline=True)
    embed.add_field(
        name="⏰ Ends",
        value=(
            f"{discord.utils.format_dt(end_time, style='R')}\n"
            f"{discord.utils.format_dt(end_time, style='f')}"
        ),
        inline=False
    )
    embed.add_field(
        name="📋 Duration",
        value=f"`{format_duration(duration_minutes)}`",
        inline=True
    )
    embed.add_field(
        name="🎟️ How to enter",
        value="Press **Enter Giveaway** below. Press it again to leave.",
        inline=True
    )
    embed.set_image(url=f"attachment://{GIVEAWAY_IMAGE_NAME}")
    embed.set_footer(
        text=f"{BRAND} • Giveaway #{giveaway_id} • Hosted by {interaction.user}"
    )

    content = (
        "@everyone"
        if ping_everyone
        else None
    )

    try:

        message = await channel.send(
            content=content,
            embed=embed,
            file=discord.File(
                GIVEAWAY_IMAGE_FILE,
                filename=GIVEAWAY_IMAGE_NAME
            ),
            view=GiveawayView(
                giveaway_id
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=ping_everyone
            )
        )

    except discord.Forbidden:

        del giveaways[giveaway_id]

        logger.error(
            "No permission to create giveaway #%s in channel %s (%s).",
            giveaway_id,
            channel.name,
            channel.id
        )

        await interaction.response.send_message(
            "❌ I don't have permission to send messages "
            "or embeds in that channel.",
            ephemeral=True
        )

        return

    giveaways[giveaway_id]["message_id"] = message.id

    logger.info(
        "Giveaway #%s created by %s (%s) in #%s | Prize: %s | Duration: %s | Winners: %s",
        giveaway_id,
        interaction.user,
        interaction.user.id,
        channel.id,
        prize,
        format_duration(duration_minutes),
        winners
    )

    await send_log(
        interaction.guild,
        "giveaways",
        "🎉 Giveaway Created",
        f"Giveaway **#{giveaway_id}** was created.",
        discord.Color.blurple(),
        [
            (
                "Host",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Prize",
                prize,
                True
            ),
            (
                "Duration",
                format_duration(duration_minutes),
                True
            ),
            (
                "Winners",
                winners,
                True
            ),
            (
                "Channel",
                channel.mention,
                True
            )
        ]
    )

    await interaction.response.send_message(
        f"✅ Giveaway **#{giveaway_id}** created in "
        f"{channel.mention}!",
        ephemeral=True
    )

    asyncio.create_task(
        giveaway_timer(
            giveaway_id
        )
    )


# =========================================================
# /GIVEAWAY ENTRIES
# =========================================================

@giveaway_group.command(
    name="entries",
    description="See how many people entered"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    giveaway_id="The giveaway ID"
)
async def giveaway_entries(
    interaction: discord.Interaction,
    giveaway_id: int
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:

        await interaction.response.send_message(
            "❌ Giveaway not found.",
            ephemeral=True
        )

        return

    entries = len(
        giveaway["entries"]
    )

    status = (
        "Ended"
        if giveaway["ended"]
        else "Active"
    )

    embed = discord.Embed(
        title="🎟️ Giveaway Entries",
        description=(
            f"**Giveaway:** #{giveaway_id}\n"
            f"**Prize:** {giveaway['prize']}\n"
            f"**Entries:** `{entries}`\n"
            f"**Winners:** `{giveaway['winners']}`\n"
            f"**Status:** `{status}`"
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# /GIVEAWAY END
# =========================================================

@giveaway_group.command(
    name="end",
    description="End a giveaway early"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    giveaway_id="The giveaway ID"
)
async def giveaway_end(
    interaction: discord.Interaction,
    giveaway_id: int
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:

        await interaction.response.send_message(
            "❌ Giveaway not found.",
            ephemeral=True
        )

        return

    if giveaway["ended"]:

        await interaction.response.send_message(
            "❌ That giveaway has already ended.",
            ephemeral=True
        )

        return

    await finish_giveaway(
        giveaway_id,
        manual=True
    )

    logger.info(
        "Giveaway #%s manually ended by %s (%s).",
        giveaway_id,
        interaction.user,
        interaction.user.id
    )

    await interaction.response.send_message(
        f"✅ Giveaway **#{giveaway_id}** ended.",
        ephemeral=True
    )


# =========================================================
# /GIVEAWAY REROLL
# =========================================================

@giveaway_group.command(
    name="reroll",
    description="Reroll giveaway winner(s)"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    giveaway_id="The giveaway ID"
)
async def giveaway_reroll(
    interaction: discord.Interaction,
    giveaway_id: int
):

    giveaway = giveaways.get(
        giveaway_id
    )

    if giveaway is None:

        await interaction.response.send_message(
            "❌ Giveaway not found.",
            ephemeral=True
        )

        return

    if not giveaway["ended"]:

        await interaction.response.send_message(
            "❌ You can only reroll an ended giveaway.",
            ephemeral=True
        )

        return

    entries = list(
        giveaway["entries"]
    )

    if not entries:

        await interaction.response.send_message(
            "❌ There are no entries.",
            ephemeral=True
        )

        return

    winner_count = min(
        giveaway["winners"],
        len(entries)
    )

    winners = random.sample(
        entries,
        winner_count
    )

    mentions = " ".join(
        f"<@{user_id}>"
        for user_id in winners
    )

    giveaway["winners_selected"] = winners

    logger.info(
        "Giveaway #%s rerolled by %s (%s). New winner count: %s.",
        giveaway_id,
        interaction.user,
        interaction.user.id,
        len(winners)
    )

    await send_log(
        interaction.guild,
        "giveaways",
        "🔄 Giveaway Rerolled",
        f"Giveaway **#{giveaway_id}** was rerolled.",
        discord.Color.orange(),
        [
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Prize",
                giveaway["prize"],
                True
            ),
            (
                "New Winner(s)",
                mentions,
                False
            )
        ]
    )

    await interaction.response.send_message(
        f"🔄 **Giveaway #{giveaway_id} Rerolled!**\n\n"
        f"🏆 New winner(s): {mentions}\n\n"
        "🎟️ Winners can click **Claim Giveaway** on the giveaway message, "
        "then open a ticket and say **Giveaway Winner**.",
        view=GiveawayClaimView(),
        allowed_mentions=discord.AllowedMentions(users=True)
    )


bot.tree.add_command(
    giveaway_group,
    guild=GUILD
)


# =========================================================
# /AUTOROLE
# =========================================================

autorole_group = app_commands.Group(
    name="autorole",
    description="Configure the automatic join role"
)


@autorole_group.command(
    name="set",
    description="Set the role automatically given to new members"
)
@app_commands.checks.has_permissions(
    manage_roles=True
)
@app_commands.describe(
    role="The role new members should automatically receive"
)
async def autorole_set(
    interaction: discord.Interaction,
    role: discord.Role
):
    if role.is_default():
        await interaction.response.send_message(
            "❌ You cannot use @everyone as the auto role.",
            ephemeral=True
        )
        return

    bot_member = interaction.guild.me

    if bot_member is None:
        await interaction.response.send_message(
            "❌ I couldn't verify my role position.",
            ephemeral=True
        )
        return

    if role >= bot_member.top_role:
        await interaction.response.send_message(
            "❌ I can't give that role because it is higher than "
            "or equal to my highest role. Move my bot role above it.",
            ephemeral=True
        )
        return

    if role.managed:
        await interaction.response.send_message(
            "❌ That role is managed by an integration and cannot "
            "be assigned by the bot.",
            ephemeral=True
        )
        return

    autorole_config[str(interaction.guild.id)] = role.id
    save_autorole_config()

    logger.info(
        "Auto role set by %s (%s): %s (%s) in %s (%s)",
        interaction.user,
        interaction.user.id,
        role.name,
        role.id,
        interaction.guild.name,
        interaction.guild.id
    )

    await interaction.response.send_message(
        f"✅ Auto role set to {role.mention}.\n"
        f"Every new member will automatically receive this role."
    )


@autorole_group.command(
    name="disable",
    description="Disable the automatic join role"
)
@app_commands.checks.has_permissions(
    manage_roles=True
)
async def autorole_disable(
    interaction: discord.Interaction
):
    guild_key = str(interaction.guild.id)

    if guild_key not in autorole_config:
        await interaction.response.send_message(
            "ℹ️ Auto role is already disabled.",
            ephemeral=True
        )
        return

    del autorole_config[guild_key]
    save_autorole_config()

    logger.info(
        "Auto role disabled by %s (%s) in %s (%s)",
        interaction.user,
        interaction.user.id,
        interaction.guild.name,
        interaction.guild.id
    )

    await interaction.response.send_message(
        "✅ Auto role has been disabled."
    )


@autorole_group.command(
    name="status",
    description="Show the current automatic join role"
)
@app_commands.checks.has_permissions(
    manage_roles=True
)
async def autorole_status(
    interaction: discord.Interaction
):
    role_id = autorole_config.get(
        str(interaction.guild.id)
    )

    if not role_id:
        await interaction.response.send_message(
            "ℹ️ Auto role is currently disabled.",
            ephemeral=True
        )
        return

    role = interaction.guild.get_role(
        int(role_id)
    )

    if role is None:
        await interaction.response.send_message(
            "⚠️ An auto role is configured, but that role no longer exists.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"⚙️ Current auto role: {role.mention}",
        ephemeral=True
    )


# =========================================================
# /POJ
# =========================================================

poj_group = app_commands.Group(
    name="poj",
    description="Ping new members when they join"
)


@poj_group.command(
    name="add",
    description="Add a channel to Ping On Join"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    channel="Channel where new members will be pinged",
    message="Message to send. Use {user}, {username}, {server}, or {count}",
    delay="Seconds before the ping message is deleted"
)
async def poj_add(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str = POJ_DEFAULT_MESSAGE,
    delay: float = POJ_DEFAULT_DELAY
):

    if delay < 0 or delay > 60:

        await interaction.response.send_message(
            "❌ Delay must be between 0 and 60 seconds.",
            ephemeral=True
        )

        return

    if not message.strip():

        await interaction.response.send_message(
            "❌ The POJ message cannot be empty.",
            ephemeral=True
        )

        return

    guild_key = str(
        interaction.guild.id
    )

    guild_config = poj_channels.setdefault(
        guild_key,
        {}
    )

    guild_config[str(channel.id)] = {
        "message": message,
        "delay": delay
    }

    save_poj_config()

    logger.info(
        "POJ enabled by %s (%s) in #%s (%s) | Delay: %ss",
        interaction.user,
        interaction.user.id,
        channel.name,
        channel.id,
        delay
    )

    await send_log(
        interaction.guild,
        "poj",
        "📢 Ping On Join Configured",
        f"Ping On Join was enabled in {channel.mention}.",
        discord.Color.green(),
        [
            (
                "Moderator",
                interaction.user.mention,
                True
            ),
            (
                "Channel",
                channel.mention,
                True
            ),
            (
                "Delay",
                f"{delay}s",
                True
            ),
            (
                "Message",
                message,
                False
            )
        ]
    )

    await interaction.response.send_message(
        f"✅ Ping On Join enabled in {channel.mention}.\n"
        f"📝 Message: `{message}`\n"
        f"⏱️ Delete delay: `{delay}s`",
        ephemeral=True
    )


@poj_group.command(
    name="remove",
    description="Remove a channel from Ping On Join"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    channel="Channel to remove"
)
async def poj_remove(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    guild_key = str(
        interaction.guild.id
    )

    guild_config = poj_channels.get(
        guild_key,
        {}
    )

    if str(channel.id) not in guild_config:

        await interaction.response.send_message(
            f"❌ {channel.mention} is not configured.",
            ephemeral=True
        )

        return

    del guild_config[
        str(channel.id)
    ]

    if not guild_config:

        poj_channels.pop(
            guild_key,
            None
        )

    save_poj_config()

    logger.info(
        "POJ removed by %s (%s) from #%s (%s).",
        interaction.user,
        interaction.user.id,
        channel.name,
        channel.id
    )

    await send_log(
        interaction.guild,
        "poj",
        "📢 Ping On Join Removed",
        f"Ping On Join was removed from {channel.mention}.",
        discord.Color.orange(),
        [
            (
                "Moderator",
                interaction.user.mention,
                True
            ),
            (
                "Channel",
                channel.mention,
                True
            )
        ]
    )

    await interaction.response.send_message(
        f"✅ Ping On Join removed from {channel.mention}.",
        ephemeral=True
    )


@poj_group.command(
    name="list",
    description="List Ping On Join channels"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def poj_list(
    interaction: discord.Interaction
):

    guild_config = poj_channels.get(
        str(interaction.guild.id),
        {}
    )

    if not guild_config:

        await interaction.response.send_message(
            "ℹ️ Ping On Join is not configured.",
            ephemeral=True
        )

        return

    lines = []

    for channel_id, config in guild_config.items():

        channel = interaction.guild.get_channel(
            int(channel_id)
        )

        channel_name = (
            channel.mention
            if channel
            else f"<#{channel_id}>"
        )

        lines.append(
            f"**{channel_name}** — "
            f"⏱️ `{config.get('delay', POJ_DEFAULT_DELAY)}s` — "
            f"📝 {config.get('message', POJ_DEFAULT_MESSAGE)}"
        )

    embed = discord.Embed(
        title="📢 Ping On Join",
        description="\n".join(lines),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


@poj_group.command(
    name="reset",
    description="Remove all Ping On Join channels"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def poj_reset(
    interaction: discord.Interaction
):

    guild_key = str(
        interaction.guild.id
    )

    if guild_key not in poj_channels:

        await interaction.response.send_message(
            "ℹ️ Ping On Join is already reset.",
            ephemeral=True
        )

        return

    poj_channels.pop(
        guild_key,
        None
    )

    save_poj_config()

    logger.info(
        "POJ configuration reset by %s (%s).",
        interaction.user,
        interaction.user.id
    )

    await send_log(
        interaction.guild,
        "poj",
        "📢 Ping On Join Reset",
        "All Ping On Join channels were removed.",
        discord.Color.red(),
        [
            (
                "Moderator",
                interaction.user.mention,
                False
            )
        ]
    )

    await interaction.response.send_message(
        "✅ All Ping On Join channels have been removed.",
        ephemeral=True
    )


@bot.event
async def on_member_join(
    member: discord.Member
):

    guild_config = poj_channels.get(
        str(member.guild.id),
        {}
    )

    logger.info(
        "Member joined: %s (%s) in %s (%s).",
        member,
        member.id,
        member.guild.name,
        member.guild.id
    )

    # Give the configured auto role to the new member.
    auto_role_id = autorole_config.get(
        str(member.guild.id)
    )

    if auto_role_id:
        auto_role = member.guild.get_role(
            int(auto_role_id)
        )

        if auto_role is not None:
            try:
                bot_member = member.guild.me

                if (
                    not auto_role.is_default()
                    and not auto_role.managed
                    and bot_member is not None
                    and auto_role < bot_member.top_role
                ):
                    await member.add_roles(
                        auto_role,
                        reason="Automatic join role"
                    )

                    logger.info(
                        "Auto role %s (%s) given to %s (%s).",
                        auto_role.name,
                        auto_role.id,
                        member,
                        member.id
                    )

                else:
                    logger.error(
                        "Cannot give auto role %s (%s): "
                        "role is above/equal to bot, managed, or bot role unavailable.",
                        auto_role.name,
                        auto_role.id
                    )

            except discord.Forbidden:
                logger.error(
                    "No permission to give auto role %s (%s) to %s (%s).",
                    auto_role.name,
                    auto_role.id,
                    member,
                    member.id
                )

            except discord.HTTPException as error:
                logger.error(
                    "Failed to give auto role to %s (%s): %s",
                    member,
                    member.id,
                    error
                )


    await send_log(
        member.guild,
        "member_join",
        "📥 Member Joined",
        f"{member.mention} joined the server.",
        discord.Color.green(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Account Created",
                discord.utils.format_dt(
                    member.created_at,
                    style="F"
                ),
                False
            )
        ]
    )

    if not guild_config:
        return

    for channel_id, config in list(
        guild_config.items()
    ):

        channel = member.guild.get_channel(
            int(channel_id)
        )

        if channel is None:
            continue

        template = config.get(
            "message",
            POJ_DEFAULT_MESSAGE
        )

        delay = config.get(
            "delay",
            POJ_DEFAULT_DELAY
        )

        content = format_poj_message(
            template,
            member
        )

        try:

            ping_message = await channel.send(
                content=content,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )

            logger.info(
                "POJ message sent for %s (%s) in #%s (%s).",
                member,
                member.id,
                channel.name,
                channel.id
            )

            await send_log(
                member.guild,
                "poj",
                "👋 Ping On Join Sent",
                f"Ping On Join message sent for {member.mention}.",
                discord.Color.blurple(),
                [
                    (
                        "Member",
                        f"{member} (`{member.id}`)",
                        True
                    ),
                    (
                        "Channel",
                        channel.mention,
                        True
                    )
                ]
            )

            if delay > 0:

                await asyncio.sleep(
                    delay
                )

            await ping_message.delete()

        except discord.NotFound:
            pass

        except discord.Forbidden:

            logger.error(
                "No permission to send/delete POJ message "
                "in #%s (%s)",
                channel.name,
                channel.id
            )

        except Exception as error:

            logger.exception(
                "POJ error in #%s: %s",
                channel.name,
                error
            )


# =========================================================
# MEMBER LEAVE LOG
# =========================================================

@bot.event
async def on_member_remove(
    member: discord.Member
):

    logger.info(
        "Member left: %s (%s) from %s (%s).",
        member,
        member.id,
        member.guild.name,
        member.guild.id
    )

    await send_log(
        member.guild,
        "member_leave",
        "📤 Member Left",
        f"**{member}** left the server.",
        discord.Color.red(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Joined Server",
                (
                    discord.utils.format_dt(
                        member.joined_at,
                        style="F"
                    )
                    if member.joined_at
                    else "Unknown"
                ),
                False
            )
        ]
    )


# =========================================================
# =========================================================
# REGISTER AUTOROLE COMMAND GROUP
# =========================================================

bot.tree.add_command(
    autorole_group,
    guild=GUILD
)

# REGISTER POJ COMMAND GROUP
# =========================================================

# This must be registered before the guild command sync.
bot.tree.add_command(
    poj_group,
    guild=GUILD
)


# =========================================================
# /PING
# =========================================================

@bot.tree.command(
    name="ping",
    description="Check Zev Hub bot latency",
    guild=GUILD
)
async def ping(
    interaction: discord.Interaction
):

    latency = round(
        bot.latency * 1000
    )

    embed = discord.Embed(
        title="🏓 Zev Hub",
        description=(
            f"**Pong!**\n\n"
            f"🤖 Bot latency: `{latency}ms`\n"
            f"📡 Status: `Online`"
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /ANNOUNCE
# =========================================================

@bot.tree.command(
    name="announce",
    description="Create an Zev Hub announcement",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    message="Announcement message",
    title="Announcement title",
    role="Role to ping",
    image="Optional banner image URL"
)
async def announce(
    interaction: discord.Interaction,
    message: str,
    title: str = "📢 Zev Hub Announcement",
    role: discord.Role = None,
    image: str = None
):

    if role is not None:

        if role.is_default():

            await interaction.response.send_message(
                "❌ You cannot select the @everyone role.",
                ephemeral=True
            )

            return

        if (
            interaction.guild.me is not None
            and role >= interaction.guild.me.top_role
        ):

            await interaction.response.send_message(
                "❌ I cannot ping that role because it is "
                "equal to or higher than my highest role.",
                ephemeral=True
            )

            return

    embed = discord.Embed(
        title=title,
        description=f"```text\n{message}\n```",
        color=discord.Color.from_rgb(
            139,
            92,
            246
        )
    )

    if interaction.client.user:

        embed.set_author(
            name="Zev Hub",
            icon_url=interaction.client.user.display_avatar.url
        )

    if image:

        image = image.strip()

        if not (
            image.startswith("http://")
            or image.startswith("https://")
        ):

            await interaction.response.send_message(
                "❌ The image must be a valid image URL.",
                ephemeral=True
            )

            return

        embed.set_image(
            url=image
        )

    embed.set_footer(
        text="Zev Hub • Announcements"
    )

    content = (
        role.mention
        if role is not None
        else None
    )

    allowed_mentions = discord.AllowedMentions(
        roles=True
    )

    await interaction.response.send_message(
        content=content,
        embed=embed,
        allowed_mentions=allowed_mentions
    )

    logger.info(
        "Announcement created by %s (%s) | Channel: %s (%s) | Role: %s",
        interaction.user,
        interaction.user.id,
        interaction.channel.name if interaction.channel else "Unknown",
        interaction.channel.id if interaction.channel else "Unknown",
        role.name if role else "None"
    )

    await send_log(
        interaction.guild,
        "announcements",
        "📢 Announcement Created",
        "A new Zev Hub announcement was created.",
        discord.Color.blurple(),
        [
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Channel",
                interaction.channel.mention
                if interaction.channel
                else "Unknown",
                True
            ),
            (
                "Role",
                role.mention if role else "None",
                True
            ),
            (
                "Title",
                title,
                False
            ),
            (
                "Message",
                message[:1000],
                False
            )
        ]
    )


# =========================================================
# /DM
# =========================================================

@bot.tree.command(
    name="dm",
    description="Send a private message to a member",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
@app_commands.describe(
    member="Member to DM",
    message="Message to send",
    title="Optional DM title"
)
async def dm(
    interaction: discord.Interaction,
    member: discord.Member,
    message: str,
    title: str = "✉️ Message from Zev Hub"
):

    try:

        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text=BRAND
        )

        await member.send(
            embed=embed
        )

        logger.info(
            "DM sent by %s (%s) to %s (%s).",
            interaction.user,
            interaction.user.id,
            member,
            member.id
        )

        await send_log(
            interaction.guild,
            "dm",
            "✉️ DM Sent",
            "A moderator sent a DM through Zev Hub.",
            discord.Color.blurple(),
            [
                (
                    "Moderator",
                    f"{interaction.user.mention} (`{interaction.user.id}`)",
                    False
                ),
                (
                    "Recipient",
                    f"{member} (`{member.id}`)",
                    False
                ),
                (
                    "Title",
                    title,
                    False
                )
            ]
        )

        await interaction.response.send_message(
            f"✅ Message sent to {member.mention}.",
            ephemeral=True
        )

    except discord.Forbidden:

        logger.warning(
            "Could not DM %s (%s); DMs may be disabled.",
            member,
            member.id
        )

        await interaction.response.send_message(
            "❌ I couldn't DM that member. "
            "Their DMs may be disabled.",
            ephemeral=True
        )


# =========================================================
# /KICK
# =========================================================

@bot.tree.command(
    name="kick",
    description="Kick a member",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    kick_members=True
)
@app_commands.describe(
    member="Member to kick",
    reason="Reason for the kick"
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    await member.kick(
        reason=f"{BRAND}: {reason}"
    )

    logger.info(
        "Member kicked: %s (%s) by %s (%s) | Reason: %s",
        member,
        member.id,
        interaction.user,
        interaction.user.id,
        reason
    )

    await send_log(
        interaction.guild,
        "moderation",
        "👢 Member Kicked",
        f"{member.mention} was kicked.",
        discord.Color.orange(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Reason",
                reason,
                False
            )
        ]
    )

    embed = discord.Embed(
        title="👢 Member Kicked",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Moderator:** {interaction.user.mention}\n"
            f"**Reason:** {reason}"
        ),
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /BAN
# =========================================================

@bot.tree.command(
    name="ban",
    description="Ban a member",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    ban_members=True
)
@app_commands.describe(
    member="Member to ban",
    reason="Reason for the ban",
    delete_days="Delete messages from last 0-7 days"
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided",
    delete_days: int = 0
):

    if delete_days < 0 or delete_days > 7:

        await interaction.response.send_message(
            "❌ Delete days must be between 0 and 7.",
            ephemeral=True
        )

        return

    await member.ban(
        reason=f"{BRAND}: {reason}",
        delete_message_days=delete_days
    )

    logger.info(
        "Member banned: %s (%s) by %s (%s) | Reason: %s | Delete days: %s",
        member,
        member.id,
        interaction.user,
        interaction.user.id,
        reason,
        delete_days
    )

    await send_log(
        interaction.guild,
        "moderation",
        "🔨 Member Banned",
        f"{member.mention} was banned.",
        discord.Color.red(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Reason",
                reason,
                False
            ),
            (
                "Messages Deleted",
                f"{delete_days} day(s)",
                True
            )
        ]
    )

    embed = discord.Embed(
        title="🔨 Member Banned",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Moderator:** {interaction.user.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Messages deleted:** {delete_days} day(s)"
        ),
        color=discord.Color.red()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /UNBAN
# =========================================================

@bot.tree.command(
    name="unban",
    description="Unban a user",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    ban_members=True
)
@app_commands.describe(
    user_id="Discord ID of the user",
    reason="Reason for the unban"
)
async def unban(
    interaction: discord.Interaction,
    user_id: str,
    reason: str = "No reason provided"
):

    try:

        user_id_int = int(
            user_id
        )

    except ValueError:

        await interaction.response.send_message(
            "❌ That is not a valid Discord user ID.",
            ephemeral=True
        )

        return

    try:

        user = await bot.fetch_user(
            user_id_int
        )

    except discord.NotFound:

        await interaction.response.send_message(
            "❌ I couldn't find that Discord user.",
            ephemeral=True
        )

        return

    except discord.HTTPException:

        await interaction.response.send_message(
            "❌ I couldn't retrieve that user.",
            ephemeral=True
        )

        return

    try:

        await interaction.guild.unban(
            user,
            reason=f"{BRAND}: {reason}"
        )

        logger.info(
            "Member unbanned: %s (%s) by %s (%s) | Reason: %s",
            user,
            user.id,
            interaction.user,
            interaction.user.id,
            reason
        )

        await send_log(
            interaction.guild,
            "moderation",
            "🔓 Member Unbanned",
            f"{user.mention} was unbanned.",
            discord.Color.green(),
            [
                (
                    "User",
                    f"{user} (`{user.id}`)",
                    False
                ),
                (
                    "Moderator",
                    f"{interaction.user.mention} (`{interaction.user.id}`)",
                    False
                ),
                (
                    "Reason",
                    reason,
                    False
                )
            ]
        )

        embed = discord.Embed(
            title="🔓 Member Unbanned",
            description=(
                f"**User:** {user.mention}\n"
                f"**User ID:** `{user.id}`\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Reason:** {reason}"
            ),
            color=discord.Color.green()
        )

        embed.set_footer(
            text=FOOTER
        )

        await interaction.response.send_message(
            embed=embed
        )

    except discord.NotFound:

        await interaction.response.send_message(
            "❌ That user is not currently banned.",
            ephemeral=True
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to unban users.",
            ephemeral=True
        )

    except discord.HTTPException as error:

        logger.error(
            "Failed to unban user %s: %s",
            user_id_int,
            error
        )

        await interaction.response.send_message(
            f"❌ Failed to unban the user: `{error}`",
            ephemeral=True
        )


# =========================================================
# /TIMEOUT
# =========================================================

@bot.tree.command(
    name="timeout",
    description="Timeout a member",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
@app_commands.describe(
    member="Member to timeout",
    minutes="Duration in minutes",
    reason="Reason"
)
async def timeout(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    if minutes < 1 or minutes > 40320:

        await interaction.response.send_message(
            "❌ Duration must be between 1 minute and 28 days.",
            ephemeral=True
        )

        return

    until = (
        discord.utils.utcnow()
        + timedelta(minutes=minutes)
    )

    await member.timeout(
        until,
        reason=f"{BRAND}: {reason}"
    )

    logger.info(
        "Member timed out: %s (%s) by %s (%s) | Duration: %s minute(s) | Reason: %s",
        member,
        member.id,
        interaction.user,
        interaction.user.id,
        minutes,
        reason
    )

    await send_log(
        interaction.guild,
        "moderation",
        "⏱️ Member Timed Out",
        f"{member.mention} was timed out.",
        discord.Color.orange(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Duration",
                f"{minutes} minute(s)",
                True
            ),
            (
                "Reason",
                reason,
                False
            )
        ]
    )

    embed = discord.Embed(
        title="⏱️ Member Timed Out",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Duration:** {minutes} minute(s)\n"
            f"**Moderator:** {interaction.user.mention}\n"
            f"**Reason:** {reason}"
        ),
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /UNTIMEOUT
# =========================================================

@bot.tree.command(
    name="untimeout",
    description="Remove a timeout",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
@app_commands.describe(
    member="Member",
    reason="Reason"
)
async def untimeout(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if (
        member.top_role >= interaction.user.top_role
        and interaction.user.id != interaction.guild.owner_id
    ):

        await interaction.response.send_message(
            "❌ You cannot remove a timeout from a member "
            "with an equal or higher role.",
            ephemeral=True
        )

        return

    if member.timed_out_until is None:

        await interaction.response.send_message(
            "❌ That member is not currently timed out.",
            ephemeral=True
        )

        return

    try:

        await member.timeout(
            None,
            reason=f"{BRAND}: {reason}"
        )

        logger.info(
            "Timeout removed from %s (%s) by %s (%s) | Reason: %s",
            member,
            member.id,
            interaction.user,
            interaction.user.id,
            reason
        )

        await send_log(
            interaction.guild,
            "moderation",
            "🔓 Timeout Removed",
            f"The timeout was removed from {member.mention}.",
            discord.Color.green(),
            [
                (
                    "Member",
                    f"{member} (`{member.id}`)",
                    False
                ),
                (
                    "Moderator",
                    f"{interaction.user.mention} (`{interaction.user.id}`)",
                    False
                ),
                (
                    "Reason",
                    reason,
                    False
                )
            ]
        )

        embed = discord.Embed(
            title="🔓 Timeout Removed",
            description=(
                f"**Member:** {member.mention}\n"
                f"**Moderator:** {interaction.user.mention}\n"
                f"**Reason:** {reason}"
            ),
            color=discord.Color.green()
        )

        embed.set_footer(
            text=FOOTER
        )

        await interaction.response.send_message(
            embed=embed
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ I don't have permission to remove this timeout.",
            ephemeral=True
        )

    except discord.HTTPException as error:

        logger.error(
            "Failed to remove timeout: %s",
            error
        )

        await interaction.response.send_message(
            f"❌ Failed to remove timeout: `{error}`",
            ephemeral=True
        )


# =========================================================
# /WARN
# =========================================================

@bot.tree.command(
    name="warn",
    description="Warn a member",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
@app_commands.describe(
    member="Member to warn",
    reason="Reason"
)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member.bot:

        await interaction.response.send_message(
            "❌ You cannot warn a bot.",
            ephemeral=True
        )

        return

    if member.id == interaction.user.id:

        await interaction.response.send_message(
            "❌ You cannot warn yourself.",
            ephemeral=True
        )

        return

    if (
        member.top_role >= interaction.user.top_role
        and interaction.user.id != interaction.guild.owner_id
    ):

        await interaction.response.send_message(
            "❌ You cannot warn a member with an equal "
            "or higher role.",
            ephemeral=True
        )

        return

    guild_id = str(
        interaction.guild.id
    )

    user_id = str(
        member.id
    )

    guild_warnings = warnings.setdefault(
        guild_id,
        {}
    )

    user_warnings = guild_warnings.setdefault(
        user_id,
        []
    )

    warning_id = len(
        user_warnings
    ) + 1

    warning = {
        "id": warning_id,
        "reason": reason,
        "moderator_id": interaction.user.id,
        "timestamp": discord.utils.utcnow().isoformat()
    }

    user_warnings.append(
        warning
    )

    save_warnings()

    logger.info(
        "Warning #%s issued to %s (%s) by %s (%s) | Reason: %s",
        warning_id,
        member,
        member.id,
        interaction.user,
        interaction.user.id,
        reason
    )

    await send_log(
        interaction.guild,
        "moderation",
        "⚠️ Member Warned",
        f"{member.mention} received warning **#{warning_id}**.",
        discord.Color.orange(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Warning",
                f"#{warning_id}",
                True
            ),
            (
                "Total Warnings",
                len(user_warnings),
                True
            ),
            (
                "Reason",
                reason,
                False
            )
        ]
    )

    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Warning:** `#{warning_id}`\n"
            f"**Moderator:** {interaction.user.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Total warnings:** `{len(user_warnings)}`"
        ),
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )

    try:

        dm_embed = discord.Embed(
            title=f"⚠️ Warning — {interaction.guild.name}",
            description=(
                f"You have received a warning in "
                f"**{interaction.guild.name}**.\n\n"
                f"**Reason:** {reason}\n"
                f"**Total warnings:** `{len(user_warnings)}`"
            ),
            color=discord.Color.orange()
        )

        dm_embed.set_footer(
            text=FOOTER
        )

        await member.send(
            embed=dm_embed
        )

    except discord.Forbidden:

        logger.warning(
            "Could not DM warned member %s (%s).",
            member,
            member.id
        )


# =========================================================
# /UNWARN
# =========================================================

@bot.tree.command(
    name="unwarn",
    description="Remove a warning",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
@app_commands.describe(
    member="Member",
    warning_id="Warning number"
)
async def unwarn(
    interaction: discord.Interaction,
    member: discord.Member,
    warning_id: int
):

    if warning_id < 1:

        await interaction.response.send_message(
            "❌ Warning ID must be 1 or higher.",
            ephemeral=True
        )

        return

    user_warnings = get_user_warnings(
        interaction.guild.id,
        member.id
    )

    if not user_warnings:

        await interaction.response.send_message(
            f"❌ {member.mention} has no warnings.",
            ephemeral=True
        )

        return

    warning = next(
        (
            warning
            for warning in user_warnings
            if warning["id"] == warning_id
        ),
        None
    )

    if warning is None:

        await interaction.response.send_message(
            f"❌ Warning `#{warning_id}` was not found.",
            ephemeral=True
        )

        return

    user_warnings.remove(
        warning
    )

    for index, remaining_warning in enumerate(
        user_warnings,
        start=1
    ):

        remaining_warning["id"] = index

    guild_warnings = warnings.get(
        str(interaction.guild.id),
        {}
    )

    if user_warnings:

        guild_warnings[str(member.id)] = (
            user_warnings
        )

    else:

        guild_warnings.pop(
            str(member.id),
            None
        )

    save_warnings()

    logger.info(
        "Warning #%s removed from %s (%s) by %s (%s).",
        warning_id,
        member,
        member.id,
        interaction.user,
        interaction.user.id
    )

    await send_log(
        interaction.guild,
        "moderation",
        "✅ Warning Removed",
        f"Warning **#{warning_id}** was removed from {member.mention}.",
        discord.Color.green(),
        [
            (
                "Member",
                f"{member} (`{member.id}`)",
                False
            ),
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Remaining Warnings",
                len(user_warnings),
                True
            )
        ]
    )

    embed = discord.Embed(
        title="✅ Warning Removed",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Removed warning:** `#{warning_id}`\n"
            f"**Moderator:** {interaction.user.mention}\n"
            f"**Remaining warnings:** `{len(user_warnings)}`"
        ),
        color=discord.Color.green()
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /CLEAR
# =========================================================

@bot.tree.command(
    name="clear",
    description="Delete messages",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
@app_commands.describe(
    amount="Number of messages to delete (1-100)"
)
async def clear(
    interaction: discord.Interaction,
    amount: int
):

    if amount < 1 or amount > 100:

        await interaction.response.send_message(
            "❌ Choose between 1 and 100 messages.",
            ephemeral=True
        )

        return

    await interaction.response.defer(
        ephemeral=True
    )

    deleted = await interaction.channel.purge(
        limit=amount
    )

    logger.info(
        "Cleared %s message(s) in #%s (%s) by %s (%s).",
        len(deleted),
        interaction.channel.name,
        interaction.channel.id,
        interaction.user,
        interaction.user.id
    )

    await send_log(
        interaction.guild,
        "moderation",
        "🧹 Messages Cleared",
        f"{interaction.user.mention} cleared messages.",
        discord.Color.orange(),
        [
            (
                "Moderator",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Channel",
                interaction.channel.mention,
                True
            ),
            (
                "Messages Deleted",
                len(deleted),
                True
            )
        ]
    )

    await interaction.followup.send(
        f"🧹 **Zev Hub Moderation**\n"
        f"Deleted **{len(deleted)}** messages.",
        ephemeral=True
    )


# =========================================================
# /USERINFO
# =========================================================

@bot.tree.command(
    name="userinfo",
    description="View information about a member",
    guild=GUILD
)
@app_commands.describe(
    member="Member to inspect"
)
async def userinfo(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title="👤 User Information",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="Username",
        value=str(member),
        inline=True
    )

    embed.add_field(
        name="User ID",
        value=str(member.id),
        inline=True
    )

    embed.add_field(
        name="Joined Server",
        value=(
            discord.utils.format_dt(
                member.joined_at,
                style="F"
            )
            if member.joined_at
            else "Unknown"
        ),
        inline=False
    )

    embed.add_field(
        name="Account Created",
        value=discord.utils.format_dt(
            member.created_at,
            style="F"
        ),
        inline=False
    )

    embed.add_field(
        name="Top Role",
        value=member.top_role.mention,
        inline=True
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /SERVERINFO
# =========================================================

@bot.tree.command(
    name="serverinfo",
    description="View server information",
    guild=GUILD
)
async def serverinfo(
    interaction: discord.Interaction
):

    guild = interaction.guild

    if guild is None:

        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title=f"🏠 {guild.name}",
        color=discord.Color.blurple()
    )

    if guild.icon:

        embed.set_thumbnail(
            url=guild.icon.url
        )

    embed.add_field(
        name="👥 Members",
        value=str(guild.member_count),
        inline=True
    )

    embed.add_field(
        name="💬 Channels",
        value=str(len(guild.channels)),
        inline=True
    )

    embed.add_field(
        name="🎭 Roles",
        value=str(len(guild.roles)),
        inline=True
    )

    embed.add_field(
        name="🆔 Server ID",
        value=str(guild.id),
        inline=False
    )

    embed.add_field(
        name="📅 Created",
        value=discord.utils.format_dt(
            guild.created_at,
            style="F"
        ),
        inline=False
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /AVATAR
# =========================================================

@bot.tree.command(
    name="avatar",
    description="View a member's avatar",
    guild=GUILD
)
@app_commands.describe(
    member="Member whose avatar you want to see"
)
async def avatar(
    interaction: discord.Interaction,
    member: discord.Member
):

    embed = discord.Embed(
        title=f"🖼️ {member.display_name}'s Avatar",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text=FOOTER
    )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /SAY
# =========================================================

@bot.tree.command(
    name="say",
    description="Make Zev Hub send a message",
    guild=GUILD
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
@app_commands.describe(
    message="Message for the bot to send"
)
async def say(
    interaction: discord.Interaction,
    message: str
):

    await interaction.response.send_message(
        "✅ Message sent.",
        ephemeral=True
    )

    await interaction.channel.send(
        message
    )

    logger.info(
        "Say command used by %s (%s) in #%s (%s).",
        interaction.user,
        interaction.user.id,
        interaction.channel.name,
        interaction.channel.id
    )

    await send_log(
        interaction.guild,
        "commands",
        "💬 Say Command Used",
        "The `/say` command was used.",
        discord.Color.blurple(),
        [
            (
                "User",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Channel",
                interaction.channel.mention,
                True
            ),
            (
                "Message",
                message[:1000],
                False
            )
        ]
    )


# =========================================================
# COMMAND LOGGING
# =========================================================

@bot.listen("on_interaction")
async def command_logger(
    interaction: discord.Interaction
):

    if interaction.guild_id != GUILD_ID:
        return

    if interaction.type != discord.InteractionType.application_command:
        return

    command_name = (
        interaction.data.get("name")
        if interaction.data
        else "Unknown"
    )

    logger.info(
        "Application command used: /%s by %s (%s)",
        command_name,
        interaction.user,
        interaction.user.id
    )

    await send_log(
        interaction.guild,
        "commands",
        "⚡ Command Used",
        f"An application command was used.",
        discord.Color.blurple(),
        [
            (
                "Command",
                f"/{command_name}",
                True
            ),
            (
                "User",
                f"{interaction.user.mention} (`{interaction.user.id}`)",
                False
            ),
            (
                "Channel",
                interaction.channel.mention
                if interaction.channel
                else "Unknown",
                True
            )
        ]
    )


# =========================================================
# MESSAGE LOGGING
# =========================================================

@bot.event
async def on_message_delete(
    message: discord.Message
):

    if message.author.bot:
        return

    if message.guild is None:
        return

    logger.info(
        "Message deleted by %s (%s) in #%s (%s).",
        message.author,
        message.author.id,
        message.channel.name,
        message.channel.id
    )

    content = message.content

    if not content:
        content = "*No text content*"

    await send_log(
        message.guild,
        "messages",
        "🗑️ Message Deleted",
        f"A message was deleted in {message.channel.mention}.",
        discord.Color.red(),
        [
            (
                "Author",
                f"{message.author.mention} (`{message.author.id}`)",
                False
            ),
            (
                "Channel",
                message.channel.mention,
                True
            ),
            (
                "Content",
                content[:1000],
                False
            )
        ]
    )


@bot.event
async def on_message_edit(
    before: discord.Message,
    after: discord.Message
):

    if before.author.bot:
        return

    if before.guild is None:
        return

    if before.content == after.content:
        return

    logger.info(
        "Message edited by %s (%s) in #%s (%s).",
        before.author,
        before.author.id,
        before.channel.name,
        before.channel.id
    )

    await send_log(
        before.guild,
        "messages",
        "✏️ Message Edited",
        f"A message was edited in {before.channel.mention}.",
        discord.Color.orange(),
        [
            (
                "Author",
                f"{before.author.mention} (`{before.author.id}`)",
                False
            ),
            (
                "Channel",
                before.channel.mention,
                True
            ),
            (
                "Before",
                before.content[:1000] or "*Empty*",
                False
            ),
            (
                "After",
                after.content[:1000] or "*Empty*",
                False
            )
        ]
    )



# =========================================================
# /HELP
# =========================================================

# Fixed categories. The commands shown on each page are read from
# the commands actually registered on the bot, so the help menu
# cannot list made-up commands or duplicate group/subcommand entries.

HELP_CATEGORIES = {
    "🎉 Giveaways": {"giveaway"},
    "🛡️ Moderation": {
        "kick",
        "ban",
        "unban",
        "timeout",
        "untimeout",
        "warn",
        "unwarn",
        "clear",
    },
    "⚙️ Server Management": {
        "announce",
        "dm",
        "say",
    },
    "👤 Members & Utilities": {
        "userinfo",
        "serverinfo",
        "avatar",
        "ping",
        "help",
    },
    "🔧 Configuration": {
        "logs",
        "autorole",
        "poj",
    },
}


def get_help_command_pages():
    """Build help pages from commands actually registered on the bot."""
    registered = bot.tree.get_commands(guild=GUILD)

    registered_map = {
        command.name: command
        for command in registered
    }

    pages = []

    for category_name, command_names in HELP_CATEGORIES.items():
        category_commands = []

        for command_name in command_names:
            command = registered_map.get(command_name)

            if command is None:
                continue

            if isinstance(command, app_commands.Group):
                for subcommand in command.commands:
                    category_commands.append(
                        (
                            f"/{command.name} {subcommand.name}",
                            subcommand.description
                            or "No description provided."
                        )
                    )
            else:
                category_commands.append(
                    (
                        f"/{command.name}",
                        command.description
                        or "No description provided."
                    )
                )

        if category_commands:
            category_commands.sort(
                key=lambda item: item[0].lower()
            )
            pages.append(
                (category_name, category_commands)
            )

    return pages


class HelpView(discord.ui.View):
    def __init__(self, pages, author_id):
        super().__init__(timeout=180)
        self.pages = pages
        self.author_id = author_id
        self.page = 0
        self.update_buttons()

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the person who opened this help menu can use these buttons.",
                ephemeral=True
            )
            return False

        return True

    def update_buttons(self):
        self.previous_button.disabled = self.page <= 0
        self.next_button.disabled = (
            self.page >= len(self.pages) - 1
        )

    def build_embed(self, bot_user=None):
        category_name, commands = self.pages[self.page]

        embed = discord.Embed(
            title="🛠️ Zev Hub • Help",
            description=(
                f"**{category_name}**\n"
                "Commands currently available in this category."
            ),
            color=discord.Color.from_rgb(139, 92, 246)
        )

        for command_name, description in commands:
            embed.add_field(
                name=f"`{command_name}`",
                value=description,
                inline=False
            )

        embed.set_footer(
            text=(
                f"{BRAND} • Page {self.page + 1}/{len(self.pages)}"
                " • Browse categories with the buttons"
            )
        )

        if bot_user:
            embed.set_thumbnail(
                url=bot_user.display_avatar.url
            )

        return embed

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.page > 0:
            self.page -= 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.build_embed(interaction.client.user),
            view=self
        )

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.page < len(self.pages) - 1:
            self.page += 1

        self.update_buttons()

        await interaction.response.edit_message(
            embed=self.build_embed(interaction.client.user),
            view=self
        )

    @discord.ui.button(
        label="Close",
        emoji="✖️",
        style=discord.ButtonStyle.danger
    )
    async def close_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="",
            embed=None,
            view=None
        )
        self.stop()


@bot.tree.command(
    name="help",
    description="Show all Zev Hub commands",
    guild=GUILD
)
async def help_command(
    interaction: discord.Interaction
):
    pages = get_help_command_pages()

    if not pages:
        await interaction.response.send_message(
            "❌ No commands are currently registered.",
            ephemeral=True
        )
        return

    view = HelpView(
        pages,
        interaction.user.id
    )

    await interaction.response.send_message(
        embed=view.build_embed(interaction.client.user),
        view=view
    )

# =========================================================
# ERROR HANDLING
# =========================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        message = (
            "❌ You don't have permission "
            "to use this Zev Hub command."
        )

        logger.warning(
            "Permission denied for %s (%s) using an application command.",
            interaction.user,
            interaction.user.id
        )

    elif isinstance(
        error,
        app_commands.errors.CommandOnCooldown
    ):

        message = (
            "❌ That command is currently on cooldown."
        )

        logger.warning(
            "Command cooldown triggered for %s (%s).",
            interaction.user,
            interaction.user.id
        )

    else:

        logger.exception(
            "Command error: %r",
            error
        )

        message = (
            "❌ Something went wrong while "
            "running this command."
        )

    if interaction.response.is_done():

        await interaction.followup.send(
            message,
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            message,
            ephemeral=True
        )


# =========================================================
# BOT READY / COMMAND SYNC
# =========================================================

@bot.event
async def on_ready():

    logger.info("=" * 60)

    logger.info(
        "%s is online!",
        BRAND
    )

    logger.info(
        "Logged in as: %s",
        bot.user
    )

    logger.info(
        "Bot user ID: %s",
        bot.user.id
        if bot.user
        else "Unknown"
    )

    logger.info(
        "Syncing slash commands..."
    )

    try:

        synced = await bot.tree.sync(
            guild=GUILD
        )

        logger.info(
            "Successfully synced %s commands to guild %s.",
            len(synced),
            GUILD_ID
        )

        logger.info(
            "Registered commands:"
        )

        for command in synced:

            if isinstance(
                command,
                app_commands.Group
            ):

                logger.info(
                    "  /%s",
                    command.name
                )

                for subcommand in command.commands:

                    logger.info(
                        "      └─ %s",
                        subcommand.name
                    )

            else:

                logger.info(
                    "  /%s",
                    command.name
                )

        await setup_reaction_roles()

    except Exception as error:

        logger.exception(
            "Failed to sync commands: %r",
            error
        )

    logger.info("=" * 60)


# =========================================================
# START BOT
# =========================================================

if not TOKEN:

    logger.critical(
        "DISCORD_TOKEN is not set."
    )

    raise RuntimeError(
        "DISCORD_TOKEN is not set."
    )


logger.info(
    "Starting %s...",
    BRAND
)

bot.run(
    TOKEN
)
