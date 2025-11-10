import discord
import os
import sys
import re
import json
import logging
import datetime
from discord.ui import View, Button, Modal, TextInput
from dotenv import load_dotenv

# --- COMPILE-READY SETUP: Determine application's base directory ---
# This is crucial for finding data files (config, .env) when run as a compiled executable.
# The executable's working directory might be different from the directory it's stored in.
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle/executable (e.g., by PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If the application is run as a normal python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Setup logging to both console and a file ---
# For an executable, logging to a file is essential for debugging.
log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
log_file_path = os.path.join(BASE_DIR, 'bot.log')

# Get the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# Get a logger instance for our bot
logger = logging.getLogger('discord')


class BackupBot(discord.Client):
    """
    A Discord bot for requesting backup in-game, refactored into a class-based structure.
    This encapsulates the bot's state and logic, such as configuration and command tree.
    """
    def __init__(self, *, intents: discord.Intents, guild_id: int):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        
        # MODIFIED: Use absolute paths based on the script/executable location.
        self.config_file = os.path.join(BASE_DIR, "config.json")
        self.war_data_file = os.path.join(BASE_DIR, "war_data.json")

        self.configs = {}
        self.war_data = {}
        # Store the development guild ID for faster command syncing
        self.dev_guild = discord.Object(id=guild_id)

    async def setup_hook(self) -> None:
        """
        This is called once the bot logs in. We use it to load configuration,
        register persistent views, and sync our application commands.
        """
        self.load_config()
        self.load_war_data()
        # Register the persistent view. This is crucial for buttons to work after a restart.
        self.add_view(self.BackupControlsView(bot=self))
        # Sync the commands to our development guild.
        self.tree.copy_global_to(guild=self.dev_guild)
        await self.tree.sync(guild=self.dev_guild)
        logger.info(f"Commands synced for guild: {self.dev_guild.id}")

    # --- Configuration Management ---
    def load_config(self):
        """Loads the config.json file into the bot's 'configs' attribute."""
        try:
            with open(self.config_file, 'r') as f:
                self.configs = json.load(f)
                logger.info(f"Configuration loaded successfully from {self.config_file}")
        except FileNotFoundError:
            logger.warning(f"{self.config_file} not found. Creating it...")
            with open(self.config_file, 'w') as f:
                json.dump({}, f)
            self.configs = {}
        except json.JSONDecodeError:
            logger.error(f"Could not decode {self.config_file}. Starting with empty config.")
            self.configs = {}

    async def save_config(self):
        """Saves the current 'configs' dictionary to the config.json file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.configs, f, indent=4)
        logger.info(f"Configuration saved to {self.config_file}")

    # --- War Data Management ---
    def load_war_data(self):
        """Loads the war_data.json file into the bot's 'war_data' attribute."""
        try:
            with open(self.war_data_file, 'r') as f:
                self.war_data = json.load(f)
                logger.info(f"War data loaded successfully from {self.war_data_file}")
        except FileNotFoundError:
            logger.warning(f"{self.war_data_file} not found. Creating it...")
            with open(self.war_data_file, 'w') as f:
                json.dump({}, f)
            self.war_data = {}
        except json.JSONDecodeError:
            logger.error(f"Could not decode {self.war_data_file}. Starting with empty data.")
            self.war_data = {}

    async def save_war_data(self):
        """Saves the current 'war_data' dictionary to the war_data.json file."""
        with open(self.war_data_file, 'w') as f:
            json.dump(self.war_data, f, indent=4)
        logger.info(f"War data saved to {self.war_data_file}")

    # --- Utility Functions ---
    @staticmethod
    def is_author_or_admin(interaction: discord.Interaction, author_id: int) -> bool:
        """Checks if the interacting user is the original author or has admin permissions."""
        return interaction.user.id == author_id or interaction.user.guild_permissions.administrator

    # --- UI Elements (Modals & Views) ---
    class EditOppsModal(Modal, title="Edit Opponent List"):
        def __init__(self, current_opps: str):
            super().__init__()
            self.opps_input = TextInput(
                label="New list of opponents",
                style=discord.TextStyle.paragraph,
                default=current_opps,
                required=True,
                max_length=1000,
                placeholder="Enter the Roblox usernames of the opponents."
            )
            self.add_item(self.opps_input)

        async def on_submit(self, interaction: discord.Interaction):
            new_opps = self.opps_input.value
            original_embed = interaction.message.embeds[0]

            for i, field in enumerate(original_embed.fields):
                if field.name == "💀 Opponents":
                    original_embed.set_field_at(i, name="💀 Opponents", value=f"`{new_opps}`", inline=False)
                    break
            
            await interaction.response.edit_message(embed=original_embed)
            logger.info(f"Opponents list edited by {interaction.user} in guild {interaction.guild.id}")

    class BackupControlsView(View):
        def __init__(self, *, bot: 'BackupBot'):
            super().__init__(timeout=None)
            self.bot = bot

        @staticmethod
        def get_author_id_from_embed(embed: discord.Embed) -> int:
            """
            Robustly gets the author's ID from the embed footer.
            The footer text is expected to be 'Author ID: 123456789...'.
            """
            match = re.search(r"Author ID: (\d+)", embed.footer.text)
            return int(match.group(1)) if match else 0

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            """
            A global check for all buttons in this view.
            It checks for author/admin permissions before any button callback is run.
            """
            author_id = self.get_author_id_from_embed(interaction.message.embeds[0])
            if not self.bot.is_author_or_admin(interaction, author_id):
                await interaction.response.send_message(
                    "Only the person who started the request or an admin can use these controls.",
                    ephemeral=True
                )
                return False
            return True

        @discord.ui.button(label="Edit Opps", style=discord.ButtonStyle.secondary, custom_id="backup_view:edit_opps")
        async def edit_opps(self, interaction: discord.Interaction, button: Button):
            current_opps = ""
            for field in interaction.message.embeds[0].fields:
                if field.name == "💀 Opponents":
                    current_opps = field.value.strip('`')
                    break
            await interaction.response.send_modal(self.bot.EditOppsModal(current_opps=current_opps))

        async def end_war(self, interaction: discord.Interaction, status: str, color: discord.Color, title: str):
            """A generic function to handle ending the war."""
            # Check if this is a debug war. If so, do not record stats.
            if "DEBUG MODE" not in interaction.message.content:
                guild_id = str(interaction.guild.id)
                original_embed = interaction.message.embeds[0]

                if guild_id not in self.bot.war_data:
                    self.bot.war_data[guild_id] = []

                start_time = interaction.message.created_at
                end_time = interaction.created_at
                duration = end_time - start_time
                initiator_id = self.get_author_id_from_embed(original_embed)
                
                roblox_user, opponents_str, region = "Unknown", "Unknown", "Unknown"
                for field in original_embed.fields:
                    if field.name == "🛡️ User in Need":
                        match = re.search(r"\*\*Roblox:\*\* `(.+?)`", field.value)
                        if match: roblox_user = match.group(1)
                    elif field.name == "💀 Opponents":
                        opponents_str = field.value.strip('`')
                    elif field.name == "🌍 Region":
                        region = field.value.strip('`')
                
                num_opponents = len([opp.strip() for opp in opponents_str.split(',') if opp.strip()])

                war_record = {
                    "war_id": interaction.message.id,
                    "initiator_id": initiator_id,
                    "initiator_roblox_user": roblox_user,
                    "opponents": opponents_str,
                    "num_opponents": num_opponents,
                    "region": region,
                    "start_time_utc": start_time.isoformat(),
                    "end_time_utc": end_time.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "status": status,
                    "concluded_by_id": interaction.user.id
                }
                
                self.bot.war_data[guild_id].append(war_record)
                await self.bot.save_war_data()
                logger.info(f"War record {interaction.message.id} saved for guild {guild_id}.")

            original_embed = interaction.message.embeds[0]
            original_embed.title = title
            original_embed.color = color
            original_embed.description = "This engagement has concluded."
            original_embed.add_field(name="Status", value=f"Concluded as a **{status}** by {interaction.user.mention}", inline=False)

            for item in self.children:
                item.disabled = True

            await interaction.response.edit_message(content=f"*This backup request has concluded.*", embed=original_embed, view=self)
            logger.info(f"Backup request concluded as '{status}' by {interaction.user} in guild {interaction.guild.id}")

        @discord.ui.button(label="Win", style=discord.ButtonStyle.success, custom_id="backup_view:win")
        async def win(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Win", discord.Color.green(), "✔️ Backup Concluded (VICTORY!) ✔️")

        @discord.ui.button(label="Lose", style=discord.ButtonStyle.danger, custom_id="backup_view:lose")
        async def lose(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Loss", discord.Color.red(), "❌ Backup Concluded (DEFEAT) ❌")

        @discord.ui.button(label="Truce", style=discord.ButtonStyle.primary, custom_id="backup_view:truce")
        async def truce(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Truce", discord.Color.light_grey(), "🤝 Backup Concluded (TRUCE) 🤝")

# --- Bot instance and event listeners are setup here ---
# MODIFIED: Load .env file from the application's base directory.
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv('DISCORD_TOKEN')
# Replace with your Guild ID to make command syncing nearly instant during development
DEV_GUILD_ID = 1167835890228416623

# Define the bot's intents (permissions)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create the bot instance
bot = BackupBot(intents=intents, guild_id=DEV_GUILD_ID)

@bot.event
async def on_ready():
    """This function runs when the bot connects to Discord."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('Bot is ready and listening for commands.')
    logger.info('------')

# --- Shared Command Logic ---
async def _send_backup_request(
    interaction: discord.Interaction,
    roblox_user: str,
    opps: str,
    region: str,
    link: str,
    is_debug: bool
):
    """Internal function to handle both regular and debug backup requests."""
    bot_instance = interaction.client
    guild_id = str(interaction.guild.id)

    if guild_id not in bot_instance.configs:
        await interaction.response.send_message(
            "**Bot Not Configured!** An administrator must run the `/setup` command first.",
            ephemeral=True
        )
        return

    server_config = bot_instance.configs[guild_id]
    allowed_channel_id = server_config.get('allowed_channel_id')
    backup_role_id = server_config.get('backup_role_id')

    if interaction.channel.id != allowed_channel_id:
        await interaction.response.send_message(
            f"You can only use this command in the <#{allowed_channel_id}> channel.",
            ephemeral=True
        )
        return

    backup_role = interaction.guild.get_role(backup_role_id)
    if not backup_role and not is_debug:
        await interaction.response.send_message(
            f"Configuration Error: The backup role with ID `{backup_role_id}` was not found. "
            "An admin should re-run `/setup`.",
            ephemeral=True
        )
        return

    if link and not (link.startswith("http://") or link.startswith("https://")):
        await interaction.response.send_message(
            "**Invalid Link:** Please provide a valid URL starting with `http://` or `https://`.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚔️ Backup Request! ⚔️",
        description="A warrior requires aid! The status of this engagement is **Ongoing**.",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.imgur.com/P5LJ02a.png")
    user_info = f"**Discord:** {interaction.user.mention}\n**Roblox:** `{roblox_user}`"
    embed.add_field(name="🛡️ User in Need", value=user_info, inline=False)
    embed.add_field(name="💀 Opponents", value=f"`{opps}`", inline=False)
    embed.add_field(name="🌍 Region", value=f"`{region}`", inline=False)

    if link:
        embed.add_field(name="🔗 Join Link", value=f"[Click Here to Join]({link})", inline=False)
    else:
        embed.add_field(name="🔗 Join Link", value="*No link provided. Join via user's Roblox profile.*", inline=False)

    embed.set_footer(text=f"Celestial Sentry | The Supreme Manager | Author ID: {interaction.user.id}")

    message_content = f"**DEBUG MODE:** No roles pinged." if is_debug else backup_role.mention
    allowed_mentions = discord.AllowedMentions.none() if is_debug else discord.AllowedMentions(roles=True)

    await interaction.response.send_message(
        content=message_content,
        embed=embed,
        allowed_mentions=allowed_mentions,
        view=bot.BackupControlsView(bot=bot)
    )

    if not link:
        await interaction.followup.send(
            content="**Friendly Reminder:** You didn't provide a server link. "
                    "Make sure your **Roblox joins are on** so people can help!",
            ephemeral=True
        )

# --- Slash Command Definitions ---
@bot.tree.command(name="setup", description="[ADMIN] Configure the bot for this server.")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.describe(
    backup_channel="The channel where backup requests are sent.",
    backup_role="The role to be pinged for backup requests."
)
async def setup_command(interaction: discord.Interaction, backup_channel: discord.TextChannel, backup_role: discord.Role):
    """Sets the backup channel and role for the server."""
    bot_instance = interaction.client
    guild_id = str(interaction.guild.id)
    
    bot_instance.configs[guild_id] = {
        "backup_role_id": backup_role.id,
        "allowed_channel_id": backup_channel.id
    }
    
    await bot_instance.save_config()
    
    embed = discord.Embed(
        title="✅ Configuration Saved!",
        description="The bot has been successfully configured.",
        color=discord.Color.green()
    )
    embed.add_field(name="Backup Channel", value=backup_channel.mention, inline=False)
    embed.add_field(name="Backup Role", value=backup_role.mention, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="backup", description="Request backup from your allies.")
@discord.app_commands.describe(
    roblox_user="Your Roblox username or profile link.",
    opps="The usernames of the players teaming on you.",
    link="Optional: A private server link for easy joining."
)
@discord.app_commands.choices(region=[
    discord.app_commands.Choice(name="🇺🇸 US East", value="US East"),
    discord.app_commands.Choice(name="🇺🇸 US West", value="US West"),
    discord.app_commands.Choice(name="🇪🇺 Europe", value="Europe"),
    discord.app_commands.Choice(name="🇦🇺 Australia", value="Australia"),
    discord.app_commands.Choice(name="🇸🇬 Asia", value="Asia"),
    discord.app_commands.Choice(name="❓ Unknown", value="Unknown"),
])
async def backup_command(interaction: discord.Interaction, roblox_user: str, opps: str, region: discord.app_commands.Choice[str], link: str = None):
    """The main command to call for backup."""
    await _send_backup_request(interaction, roblox_user, opps, region.value, link, is_debug=False)

@bot.tree.command(name="debugbackup", description="[ADMIN] Create a backup request without pinging roles.")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.choices(region=[
    discord.app_commands.Choice(name="🇺🇸 US East", value="US East"),
    discord.app_commands.Choice(name="🇺🇸 US West", value="US West"),
    discord.app_commands.Choice(name="🇪🇺 Europe", value="Europe"),
    discord.app_commands.Choice(name="🇦🇺 Australia", value="Australia"),
    discord.app_commands.Choice(name="🇸🇬 Asia", value="Asia"),
    discord.app_commands.Choice(name="❓ Unknown", value="Unknown"),
])
async def debugbackup_command(interaction: discord.Interaction, roblox_user: str, opps: str, region: discord.app_commands.Choice[str], link: str = None):
    """An admin-only version of /backup that does not ping the role."""
    await _send_backup_request(interaction, roblox_user, opps, region.value, link, is_debug=True)

@bot.tree.command(name="warstats", description="View statistics about past backup requests.")
async def warstats_command(interaction: discord.Interaction):
    """Displays statistics for all recorded wars on the server."""
    bot_instance = interaction.client
    guild_id = str(interaction.guild.id)
    guild_wars = bot_instance.war_data.get(guild_id, [])

    if not guild_wars:
        await interaction.response.send_message("No war data has been recorded for this server yet.")
        return

    total_wars = len(guild_wars)
    wins = sum(1 for w in guild_wars if w['status'] == 'Win')
    losses = sum(1 for w in guild_wars if w['status'] == 'Loss')
    truces = sum(1 for w in guild_wars if w['status'] == 'Truce')
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    total_duration = sum(w.get('duration_seconds', 0) for w in guild_wars)
    avg_duration_secs = total_duration / total_wars if total_wars > 0 else 0
    m, s = divmod(avg_duration_secs, 60)
    h, m = divmod(m, 60)
    avg_duration_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    embed = discord.Embed(
        title=f"War Statistics for {interaction.guild.name}",
        description=f"Analysis of **{total_wars}** concluded engagements.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else "https://i.imgur.com/P5LJ02a.png")
    
    embed.add_field(name="📈 Overall Record", value=f"**{wins}** Wins / **{losses}** Losses / **{truces}** Truces", inline=False)
    embed.add_field(name="📊 Win Rate", value=f"`{win_rate:.1f}%` (Based on Wins and Losses)", inline=True)
    embed.add_field(name="⏱️ Avg. Duration (H:M:S)", value=f"`{avg_duration_str}`", inline=True)

    if guild_wars:
        recent_wars = sorted(guild_wars, key=lambda w: w['end_time_utc'], reverse=True)[:5]
        recent_wars_text = []
        for war in recent_wars:
            start_ts = int(datetime.datetime.fromisoformat(war['start_time_utc']).timestamp())
            line = f"<t:{start_ts}:R>: **{war['status']}** vs {war['num_opponents']} opp(s) by <@{war['initiator_id']}>"
            recent_wars_text.append(line)
        embed.add_field(name="📜 Recent Engagements", value="\n".join(recent_wars_text), inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="resetstats", description="[ADMIN] Reset all war statistics for this server.")
@discord.app_commands.checks.has_permissions(administrator=True)
async def resetstats_command(interaction: discord.Interaction):
    """Deletes all recorded war data for the current guild."""
    bot_instance = interaction.client
    guild_id = str(interaction.guild.id)

    if guild_id in bot_instance.war_data and bot_instance.war_data[guild_id]:
        war_count = len(bot_instance.war_data[guild_id])
        del bot_instance.war_data[guild_id]
        await bot_instance.save_war_data()
        
        await interaction.response.send_message(
            f"✅ **Success!** All **{war_count}** war records for this server have been deleted.",
            ephemeral=True
        )
        logger.warning(f"War data for guild {guild_id} was reset by admin {interaction.user} (ID: {interaction.user.id}).")
    else:
        await interaction.response.send_message(
            "ℹ️ No war data was found for this server, so no action was taken.",
            ephemeral=True
        )

# --- Main execution block ---
if __name__ == "__main__":
    if TOKEN is None:
        logger.error("FATAL: DISCORD_TOKEN environment variable not set.")
        logger.error("Create a .env file next to the script/executable with DISCORD_TOKEN='your_token_here'")
        # For an executable, input() can hang, so we just exit.
        sys.exit("Environment variable not set. Check log file for details.")
    if DEV_GUILD_ID is None:
        logger.error("FATAL: DEV_GUILD_ID is not set. Please replace the placeholder ID in the script.")
        sys.exit("Developer Guild ID not set. Check log file for details.")
        
    try:
        # We pass log_handler=None because we have configured the root logger ourselves.
        bot.run(TOKEN, log_handler=None)
    except Exception as e:
        logger.critical(f"Bot run failed: {e}", exc_info=True)
        sys.exit("Bot encountered a fatal error. Check log file for details.")