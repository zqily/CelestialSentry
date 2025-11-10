# Celestial Sentry
A Discord bot by [zqil](https://www.youtube.com/@Zqily) for The Strongest Battlegrounds community.

Tired of getting teamed on in The Strongest Battlegrounds? Celestial Sentry is a specialized Discord bot designed to help you quickly rally support. It provides a streamlined system for requesting backup, notifying allies, and tracking the outcomes of your battles.

## Table of Contents
- [Celestial Sentry](#celestial-sentry)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Quick Start (For Server Owners)](#quick-start-for-server-owners)
    - [Managing the Bot Process](#managing-the-bot-process)
      - [Automating Startup (Recommended)](#automating-startup-recommended)
      - [Shutting Down the Bot](#shutting-down-the-bot)
  - [Command Reference](#command-reference)
      - [Interactive Buttons](#interactive-buttons)
  - [For Developers](#for-developers)
      - [1. Prerequisites](#1-prerequisites)
      - [2. Clone \& Setup](#2-clone--setup)
      - [3. Configure](#3-configure)
      - [4. Run](#4-run)
  - [Building From Source](#building-from-source)

## Features
- **Easy Backup Requests**: Use the `/backup` command to instantly create a request embed.
- **Targeted Pings**: Notifies a specific, configurable role (e.g., `@Backup Squad`) to get the right people's attention without disturbing everyone.
- **Detailed Information**: Embeds include the user needing help, opponent names, region, and an optional server link for quick joins.
- **Interactive Controls**: Conclude engagements with `Win`, `Lose`, or `Truce` buttons. The requestor can also edit the opponent list on the fly.
- **War Statistics**: Automatically tracks server-wide statistics like win/loss ratio, total engagements, and average battle duration with the `/warstats` command.
- **Admin Tools**: Easy server setup (`/setup`), test requests without pings (`/debugbackup`), and data management (`/resetstats`).
- **Persistent & Reliable**: Buttons work even after the bot restarts. All configuration and war data are saved locally to `json` files.
- **Easy Deployment**: Comes pre-packaged as a `.exe` for simple, no-code setup on a Windows machine or server.

## Quick Start (For Server Owners)
This guide is for running the pre-compiled `CelestialSentry.exe` from a release.

1.  **Download the Bot**
    - Go to the [**Releases Page**](https://github.com/zqil/CelestialSentry/releases) on this repository.
    - Download the latest `.zip` file.

2.  **Extract the Files**
    - Create a new, dedicated folder for your bot.
    - Extract the contents of the `.zip` file into this new folder. You will see:
      - `CelestialSentry.exe` (the bot program)
      - `example.env` (an example configuration file)
      - `README.txt` (a quick-start guide)

3.  **Configure the Bot Token**
    - In your folder, **rename** the `example.env` file to just `.env`.
    - Open the `.env` file with a text editor (like Notepad).
    - You need to provide a Discord Bot Token. If you don't have one, follow the official [Discord guide](https://discordpy.readthedocs.io/en/stable/discord.html) to create a bot application and get its token.
    - Paste your token into the file, inside the quotes:
      ```
      DISCORD_TOKEN="YOUR_SECRET_TOKEN_HERE"
      ```
    - Save and close the file.

4.  **Run the Bot**
    - Double-click `CelestialSentry.exe`.
    - The bot will now be running in the background.
    - **Note:** A `bot.log` file will be created in the same folder. If you encounter issues, check this file for details.

5.  **Setup in Your Discord Server**
    - **Invite the bot** to your server. You can generate an invite link from your bot's application page in the Discord Developer Portal (under "OAuth2" -> "URL Generator"). You will need the `bot` and `application.commands` scopes.
    - **Required Permissions**: Grant the bot `Send Messages`, `Embed Links`, `Read Message History`, and `Mention Everyone`.
    - In your server, create a role for people who want to be pinged for backup (e.g., "Backup Squad").
    - Create a dedicated channel where requests will be sent (e.g., `#backup-requests`).
    - As a server administrator, run the `/setup` command in your server. For example:
      `/setup backup_channel: #backup-requests backup_role: @Backup Squad`

The bot is now fully configured and ready to use!

### Managing the Bot Process

#### Automating Startup (Recommended)
If you are running the bot on a personal computer instead of a dedicated server, you can make it start automatically with Windows.

1.  Right-click `CelestialSentry.exe` and select **Create shortcut**.
2.  Press the **Windows Key + R** to open the Run dialog.
3.  Type `shell:startup` and press Enter. A folder will open.
4.  Move the shortcut you created in step 1 into this folder.
The bot will now launch automatically every time you log into your computer.

#### Shutting Down the Bot
Since the bot runs as a background process, you must use the Task Manager to close it.

1.  Press **Ctrl + Shift + Esc** to open the Task Manager.
2.  Go to the "Details" or "Processes" tab.
3.  Find `CelestialSentry.exe` in the list.
4.  Select it and click **End task**.

> On macOS, you can achieve this using the **Activity Monitor**. On Linux, you would use a command like `pkill CelestialSentry`.

## Command Reference

| Command | Parameters | Description | Permissions |
| --- | --- | --- | --- |
| `/backup` | `roblox_user`, `opps`, `region`, `[link]` | Creates a backup request and pings the configured role. | Everyone |
| `/warstats` | *None* | Displays a summary of all concluded battles for the server. | Everyone |
| `/setup` | `backup_channel`, `backup_role` | Configures the bot's request channel and ping role. | Administrator |
| `/debugbackup` | `roblox_user`, `opps`, `region`, `[link]` | Creates a backup request without pinging the role. Ideal for testing. | Administrator |
| `/resetstats` | *None* | **Deletes all recorded war statistics for the server.** This is irreversible. | Administrator |

#### Interactive Buttons
- `Win` / `Lose` / `Truce`: Ends the request and records the result for the server's statistics.
- `Edit Opps`: Opens a pop-up to modify the list of opponents in an active request.
> **Note**: Only the original author of the request or a server administrator can use these buttons.

## For Developers
Want to run the bot from source or contribute?

#### 1. Prerequisites
- Python 3.8+
- Git

#### 2. Clone & Setup
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

#### 3. Configure
- Create a `.env` file in the root directory (see step 3 of the [Quick Start](#quick-start-for-server-owners) for instructions).
- **(Recommended)** Open `bot.py` and change the `DEV_GUILD_ID` variable to your private test server's ID. This will make your slash commands update instantly during development.

#### 4. Run
```bash
python bot.py
```

## Building From Source
This project uses [PyInstaller](https://pyinstaller.org/en/stable/) to create a standalone executable for Windows.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Run the Build Command:**
    (Execute this from the project's root directory)
    ```bash
    pyinstaller --onefile --clean --windowed -n CelestialSentry bot.py
    ```

3.  **Find the Executable:**
    - The final `CelestialSentry.exe` will be located in the newly created `dist` folder.
    - To run it, place the `.exe` in a new folder alongside a configured `.env` file. The `config.json` and `war_data.json` files will be generated automatically in that folder on the first run.