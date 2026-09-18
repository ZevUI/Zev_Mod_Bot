Axonic Hub Discord Bot

A branded Discord moderation, utility, giveaway, and server-management bot built for Axonic Hub.

Commands

General

* /ping — Check Axonic Hub bot latency
* /announce — Create a branded Axonic Hub announcement
* /dm — Send a private message to a server member
* /say — Make Axonic Hub send a message

Moderation

* /kick — Kick a member
* /ban — Ban a member
* /unban — Unban a user by Discord ID
* /timeout — Timeout a member for a specified duration
* /untimeout — Remove a member’s timeout
* /warn — Issue a warning to a member
* /unwarn — Remove a warning from a member
* /clear — Delete up to 100 messages

Warnings are stored persistently in warnings.json and include the warning reason, moderator, timestamp, and warning number.

When a member is warned, the bot also attempts to DM them with the warning details.

Information

* /userinfo — View information about a server member
* /serverinfo — View information about the server
* /avatar — View a member’s avatar

Giveaways

* /giveaway create — Create a giveaway
* /giveaway entries — View the number of giveaway entries
* /giveaway end — End a giveaway early
* /giveaway reroll — Reroll giveaway winner(s)

Giveaways use an interactive Enter Giveaway button.

The giveaway system tracks:

* 🎁 Prize
* 🏆 Number of winners
* 👥 Number of entries
* ⏰ Giveaway end time
* 👤 Giveaway host
* 🎟️ User entries
* 🔄 Winner rerolls

Giveaways can run for up to 30 days and support up to 50 winners.

Ping On Join (POJ)

* /poj add — Configure Ping On Join for a channel
* /poj remove — Remove Ping On Join from a channel
* /poj list — List configured Ping On Join channels
* /poj reset — Remove all Ping On Join configurations

When a member joins, Axonic Hub automatically sends a configurable welcome message in the configured channel.

POJ messages support:

* {user} — Mentions the new member
* {username} — New member’s display name
* {server} — Server name
* {count} — Current server member count

POJ messages can also be configured with a deletion delay of 0–60 seconds.

Reaction Roles

Axonic Hub includes an automatic reaction-role system.

Members can react to the configured reaction-role message to receive or remove roles.

Current reaction roles include:

* 💻 — Technology
* 📢 — Announcements
* 🎥 — Media
* 🎁 — Giveaways

The bot automatically restores the required reactions when it starts.

Features

* 📢 Custom Axonic Hub announcements
* 🎉 Interactive giveaway system
* 🏆 Automatic giveaway winner selection
* 🔄 Giveaway rerolls
* 👋 Configurable Ping On Join system
* 🛡️ Server moderation commands
* ⚠️ Persistent warning system
* 📩 Warning notification DMs
* 👢 Member kicking
* 🔨 Member banning
* 🔓 Member unbanning
* ⏱️ Member timeouts
* 🧹 Message clearing
* 🎭 Reaction roles
* 👤 Member information
* 🏠 Server information
* 🖼️ Avatar viewer
* 💬 Custom bot messages
* 🎨 Axonic Hub branding
* 💾 Persistent JSON configuration

Data Storage

The bot currently uses JSON files for persistent configuration:

warnings.json

Stores member warnings, including:

* Warning ID
* Warning reason
* Moderator ID
* Warning timestamp

poj_config.json

Stores Ping On Join configuration, including:

* Configured channel IDs
* Welcome message templates
* Message deletion delays

These files should be kept with the bot deployment if you want configuration and warning data to persist across restarts or redeployments.

Railway

Axonic Hub can be deployed using Railway.

Create the following environment variable:

DISCORD_TOKEN

Set its value to your Discord bot token.

Never commit your bot token to GitHub or include it directly in your source code.

Required Discord Intents

Make sure the following intents are enabled in the Discord Developer Portal:

* Server Members Intent
* Message Content Intent

The bot also uses Discord’s default intents.

Required Permissions

The bot requires appropriate Discord permissions for the features being used, including:

* Manage Server
* Manage Messages
* Kick Members
* Ban Members
* Moderate Members
* Send Messages
* Embed Links
* Read Message History
* Add Reactions
* Manage Roles
* Mention Everyone (only required when using @everyone announcements/giveaways)

Reaction Roles

For reaction roles to work correctly:

1. The bot must have Manage Roles.
2. The bot’s highest role must be above the reaction roles it needs to assign.
3. The bot must be able to access the configured reaction-role channel and message.

Tech Stack

* Python
* discord.py
* Discord Application Commands
* Discord UI Buttons
* JSON
* Railway

Configuration

The bot is currently configured for the Axonic Hub Discord server using a guild-specific application command setup.

The main configuration includes:

* Axonic Hub branding
* Discord server ID
* Reaction-role message/channel
* Reaction-role mappings
* Giveaway system
* Ping On Join configuration
* Warning storage

Security

Keep your Discord bot token private.

Use an environment variable:

DISCORD_TOKEN=your_bot_token_here

Do not place the actual token inside the Python source code or commit it to a public repository.

If a bot token is ever exposed, regenerate it immediately through the Discord Developer Portal.

Disclaimer

This bot is intended for use within Axonic Hub and its associated Discord server.

Use of moderation, messaging, giveaway, and role-management features should be limited to trusted server staff with the appropriate Discord permissions.
