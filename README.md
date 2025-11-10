# Celestial Sentry
A specialized Discord bot by [zqil](https://www.youtube.com/@Zqily) for The Strongest Battlegrounds community.

Tired of getting teamed on in The Strongest Battlegrounds? Celestial Sentry is designed to help you quickly rally support. It provides a streamlined system for requesting backup, notifying allies, and tracking the outcomes of your battles.

## Table of Contents
- [Celestial Sentry](#celestial-sentry)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Quick Start (For Server Owners)](#quick-start-for-server-owners)
    - [Prerequisite: Creating a Discord Bot](#prerequisite-creating-a-discord-bot)
    - [Managing the Bot Process](#managing-the-bot-process)
  - [Command Reference](#command-reference)
  - [For Developers](#for-developers)
  - [Building From Source](#building-from-source)

## Features
- **Rapid Backup Requests**: Use the `/backup` command (with a 60-second cooldown per user) to instantly create a clear, detailed request embed.
- **Targeted Pings**: Pings a specific, configurable role (e.g., `@Backup Squad`) to notify allies effectively.
- **Detailed War Info**: Embeds display the user in need, opponent names, region, and an optional join link. Embed color and thumbnail are customizable via `/setup`.
- **Interactive Battle Controls**: Users can conclude active engagements with `Win`, `Lose`, or `Truce` buttons, and the request author or an admin can use `Edit Opps` to update the opponent list.
- **Persistent War Statistics**: Automatically tracks server-wide statistics (win/loss ratio, total engagements, average duration) using the `/warstats` command. Data is saved persistently in `war_data.json`.
- **Comprehensive Admin Tools**: Includes easy server setup (`/setup`), testing functionality (`/debugbackup`), and data management (`/resetstats`).
- **Reliable Operation**: Built-in error handling, permissions checks, and persistent data management ensure the bot operates reliably even after restarts.

## Quick Start (For Server Owners)
This guide explains how to get the pre-compiled `CelestialSentry.exe` running on a Windows system.

### Prerequisite: Creating a Discord Bot

If you already have a token and the bot is invited, skip to Step 4.

1.  **Go to the Discord Developer Portal**: Navigate to [Discord Developers](https://discord.com/developers/applications).
2.  **Create a New Application**: Click "New Application" and give your bot a name.
3.  **Get the Token & Configure Intents**:
    *   In the Application menu, go to the **Bot** tab.
    *   Click **Add Bot**, then confirm.
    *   Under "Token", click **Copy**. This is your secret `DISCORD_TOKEN`. **Keep this private.**
    *   **Crucial Step:** Under "Privileged Gateway Intents", enable **PRESENCE INTENT** and **SERVER MEMBERS INTENT**. These are required for the bot to check member permissions and manage roles effectively.
4.  **Generate Invite Link**:
    *   Go to the **OAuth2** -> **URL Generator** tab.
    *   Under "SCOPES", select **`bot`** and **`application.commands`**.
    *   Under "BOT PERMISSIONS", select `Send Messages`, `Embed Links`, `Read Message History`, and `Mention Everyone`.
    *   Copy the generated URL and use it to invite the bot to your server.

---

5.  **Download and Extract**
    - Download the latest release `.zip` file from the [Releases Page](https://github.com/zqil/CelestialSentry/releases).
    - Create a new, dedicated folder (e.g., `C:/CelestialSentry`).
    - Extract the contents (`CelestialSentry.exe`, `example.env`, etc.) into this folder.

6.  **Configure `.env`**
    - In your folder, **rename** `example.env` to `.env`.
    - Open the `.env` file with a text editor.
    - Paste your Discord Token (obtained in Step 3) inside the quotes:
      ```
      DISCORD_TOKEN="YOUR_SECRET_TOKEN_HERE"
      ```
    - Save and close the file.

7.  **Run the Bot**
    - Double-click `CelestialSentry.exe`.
    - The bot will now be running. A `bot.log` file will be created in the same folder for logging activity and errors.

8.  **Server Setup**
    - Create a role for people who want to be notified for backup (e.g., `@Backup Squad`).
    - Create a dedicated channel for requests (e.g., `#backup-requests`).
    - As a server administrator, run the `/setup` command in *any* channel. Example usage:
      ```
      /setup backup_channel:#backup-requests backup_role:@Backup Squad embed_color:#FF5733 thumbnail_url:https://myimage.com/logo.png
      ```
    - The `embed_color` and `thumbnail_url` parameters are optional for visual customization.

The bot is now fully configured and ready for action!

### Managing the Bot Process
Since the compiled bot runs without a command line window (`console=False`), use these methods to manage it:

#### Automating Startup (Recommended)
1.  Right-click `CelestialSentry.exe` and select **Create shortcut**.
2.  Press the **Windows Key + R**, type `shell:startup`, and press Enter.
3.  Move the shortcut into the opened "Startup" folder.
The bot will now launch automatically when the user logs into Windows.

#### Shutting Down the Bot
1.  Press **Ctrl + Shift + Esc** to open the Task Manager.
2.  Go to the "Details" or "Processes" tab.
3.  Find and select `CelestialSentry.exe`.
4.  Click **End task**.

> On macOS, use the **Activity Monitor**.

## Command Reference

| Command | Parameters | Description | Cooldown | Permissions |
| :--- | :--- | :--- | :--- | :--- |
| `/help` | *None* | Shows a list of all available commands. | N/A | Everyone |
| `/backup` | `roblox_user`, `opps`, `region`, `[link]` | Creates a backup request, pings the configured role, and records war data upon conclusion. | 60 seconds per user | Everyone |
| `/warstats` | *None* | Displays a summary of all concluded battles for the server (W/L/T ratio, average duration). | N/A | Everyone |
| `/setup` | `backup_channel`, `backup_role`, `[embed_color]`, `[thumbnail_url]` | Configures the primary channel and role. Optional parameters allow customization of embed appearance. | N/A | Administrator |
| `/debugbackup` | `roblox_user`, `opps`, `region`, `[link]` | Creates a backup request **without** pinging the role or recording statistics. Ideal for testing configurations. | N/A | Administrator |
| `/resetstats` | *None* | **WARNING:** Prompts for confirmation to **delete all recorded war statistics for the server.** This is irreversible. | N/A | Administrator |

#### Interactive Buttons
These buttons appear on the backup request embed. Only the original author of the request or a server administrator can use them.
- `Win` / `Lose` / `Truce`: Ends the request, updates the embed, and records the result for `/warstats`.
- `Edit Opps`: Opens a pop-up modal allowing the user to modify the list of opponents in an active request.

## For Developers
Want to run the bot from source or contribute?

### 1. Prerequisites
- Python 3.8+
- Git

### 2. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/zqil/CelestialSentry.git
cd CelestialSentry

# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure
- Create a `.env` file in the root directory following the instructions in the [Quick Start](#prerequisite-creating-a-discord-bot).
- **(Recommended)** If developing, open `celestialsentry.py` and change the `DEV_GUILD_ID` variable (around line 287) to your private test server's ID. This will force slash command synchronization instantly during development.

### 4. Run
```bash
python celestialsentry.py
```

## Building From Source
This project uses [PyInstaller](https://pyinstaller.org/en/stable/) to create a standalone executable for Windows based on the `bot.spec` configuration file.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Run the Build Command:**
    The `bot.spec` file contains all necessary configuration, including hidden imports and the icon path.
    (Execute this from the project's root directory)
    ```bash
    pyinstaller bot.spec
    ```

3.  **Find the Executable:**
    - The final `CelestialSentry.exe` will be located in the newly created `dist` folder.
    - To run it, place the `.exe` in a new folder alongside a configured `.env` file. The data files (`config.json`, `war_data.json`, and `bot.log`) will be generated automatically in that folder on the first run.