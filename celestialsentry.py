import discord
import os
import sys
import re
import json
import logging
import datetime
import asyncio
from discord.ui import View, Button, Modal, TextInput
from dotenv import load_dotenv
# FIX: Import necessary types for improved type hinting
from typing import Optional, Union, cast

# --- COMPILE-READY SETUP: Determine application's base directory ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Setup logging to both console and a file ---
log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
log_file_path = os.path.join(BASE_DIR, 'bot.log')

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

# --- REFACTOR: Data Management ---
class DataManager:
    """
    A thread-safe manager for loading and saving JSON data.
    This class handles file I/O and uses an asyncio.Lock to prevent race conditions
    during write operations.
    """
    def __init__(self, filename: str):
        self.filepath = os.path.join(BASE_DIR, filename)
        self._lock = asyncio.Lock()
        self._data: dict = {} # FIX: Explicitly type the internal data store
        self.load()

    def load(self):
        """Loads data from the JSON file into memory."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
                logger.info(f"Data loaded successfully from {self.filepath}")
        except FileNotFoundError:
            logger.warning(f"{self.filepath} not found. A new file will be created on first save.")
            self._data = {}
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {self.filepath}. Starting with empty data.")
            self._data = {}

    async def save(self):
        """Asynchronously saves the current in-memory data to the JSON file."""
        async with self._lock:
            try:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(self._data, f, indent=4)
                logger.info(f"Data successfully saved to {self.filepath}")
            except Exception as e:
                logger.error(f"Failed to save data to {self.filepath}: {e}", exc_info=True)

    def get(self, key: str, default=None):
        """Gets a value from the data dictionary."""
        return self._data.get(key, default)

    def set(self, key: str, value):
        """Sets a value in the data dictionary. Requires a call to save() to persist."""
        self._data[key] = value


class BackupBot(discord.Client):
    """
    A Discord bot for requesting backup in-game, refactored for scalability and robustness.
    """
    def __init__(self, *, intents: discord.Intents, guild_id: int):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        
        # REFACTOR: Use DataManager for configuration and war data
        # FIX: Add type hints to custom attributes
        self.configs: DataManager = DataManager("config.json")
        self.war_data: DataManager = DataManager("war_data.json")

        self.dev_guild = discord.Object(id=guild_id)

    async def setup_hook(self) -> None:
        """
        Called once the bot logs in. Loads data, registers views, and syncs commands.
        """
        self.add_view(self.BackupControlsView(bot=self))
        self.tree.copy_global_to(guild=self.dev_guild)
        await self.tree.sync(guild=self.dev_guild)
        logger.info(f"Commands synced for guild: {self.dev_guild.id}")

    # --- ADDED: Centralized Error Handling ---
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handles errors from all slash commands globally."""
        user = interaction.user
        # FIX: Handle cases where interaction is in DMs (guild is None). This resolves the error
        # "id" is not a known attribute of "None" by checking for guild existence first.
        guild_name = interaction.guild.name if interaction.guild else "Direct Message"
        guild_id = interaction.guild.id if interaction.guild else "N/A"
        command = interaction.command.name if interaction.command else "unknown_command"

        if isinstance(error, discord.app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            await interaction.response.send_message(
                f"⏳ **Woah There, Warrior!**\nThis command is on cooldown. Please try again in **{retry_after}** second{'s' if retry_after > 1 else ''}.",
                ephemeral=True
            )
        elif isinstance(error, discord.app_commands.MissingPermissions):
            logger.warning(f"User {user} ({user.id}) tried to use '/{command}' in guild '{guild_name}' ({guild_id}) without permissions.")
            await interaction.response.send_message(
                "❌ **Permission Denied**\nYou do not have the required permissions to run this command.",
                ephemeral=True
            )
        elif isinstance(error, discord.app_commands.CheckFailure):
            logger.warning(f"Check failed for user {user} ({user.id}) on command '/{command}' in guild '{guild_name}' ({guild_id}).")
            await interaction.response.send_message(
                "🚫 **Action Not Allowed**\nYou cannot perform this action.",
                ephemeral=True
            )
        else:
            # For any other errors, log the full traceback and inform the user.
            logger.error(f"Unhandled error in command '/{command}' triggered by {user} ({user.id}) in guild '{guild_name}' ({guild_id}):", exc_info=error)
            
            # Use followup if the interaction has already been responded to.
            response_method = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
            await response_method(
                "🐛 **An Unexpected Error Occurred**\nI've encountered a problem while processing your command. My developer has been notified.",
                ephemeral=True
            )
            
    # --- Utility Functions ---
    @staticmethod
    def is_author_or_admin(interaction: discord.Interaction, author_id: int) -> bool:
        """Checks if the interacting user is the original author or has admin permissions."""
        # FIX: Check if the user is a Member before checking permissions. A User in a DM has no permissions.
        if interaction.user.id == author_id:
            return True
        if isinstance(interaction.user, discord.Member):
            return interaction.user.guild_permissions.administrator
        return False

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
            # FIX: A modal submitted from a component interaction is guaranteed to have a message.
            # Use an assertion to inform the type checker.
            assert interaction.message is not None, "Interaction from a modal must have a message"
            
            new_opps = self.opps_input.value
            original_embed = interaction.message.embeds[0]

            for i, field in enumerate(original_embed.fields):
                if field.name == "💀 Opponents":
                    original_embed.set_field_at(i, name="💀 Opponents", value=f"`{new_opps}`", inline=False)
                    break
            
            await interaction.response.edit_message(embed=original_embed)
            guild_name = interaction.guild.name if interaction.guild else "DM"
            logger.info(f"Opponents list edited by {interaction.user} in guild '{guild_name}' ({interaction.guild.id})")

    class ConfirmResetView(View):
        # FIX: The author can be a User or Member. Use Union for accurate typing.
        def __init__(self, *, bot: 'BackupBot', author: Union[discord.User, discord.Member]):
            super().__init__(timeout=60.0)
            self.bot = bot
            self.author = author
            self.confirmed = False

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("This isn't for you!", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, button: Button):
            # FIX: This command is guild-only, so add a guard clause for type safety.
            if not interaction.guild:
                await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
                return

            guild_id = str(interaction.guild.id)
            war_count = 0
            guild_war_data = self.bot.war_data.get(guild_id)

            if guild_war_data:
                war_count = len(guild_war_data)
                self.bot.war_data.set(guild_id, [])
                await self.bot.war_data.save()
            
            logger.warning(f"War data for guild '{interaction.guild.name}' ({guild_id}) was reset by admin {self.author}.")

            # FIX: Only Buttons have a `disabled` attribute. Check the type before setting.
            for item in self.children:
                if isinstance(item, (Button, discord.ui.Select)):
                    item.disabled = True
            
            await interaction.response.edit_message(
                content=f"✅ **Success!** All **{war_count}** war records have been deleted for this server.", 
                view=self
            )
            self.confirmed = True
            self.stop()

    class BackupControlsView(View):
        def __init__(self, *, bot: 'BackupBot'):
            super().__init__(timeout=None)
            self.bot = bot

        @staticmethod
        def get_author_id_from_embed(embed: discord.Embed) -> int:
            # FIX: Handle the case where the footer or its text is None.
            if embed.footer and embed.footer.text:
                match = re.search(r"Author ID: (\d+)", embed.footer.text)
                return int(match.group(1)) if match else 0
            return 0

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            # FIX: This interaction is from a message component, so message is guaranteed. Assert it.
            assert interaction.message is not None, "Interaction from a view must have a message"
            
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
            assert interaction.message is not None
            current_opps = ""
            for field in interaction.message.embeds[0].fields:
                if field.name == "💀 Opponents":
                    # FIX: field.value is always str per discord.py types, so stripping is safe.
                    # This resolves the Pylance error "strip is not a known attribute of None".
                    current_opps = field.value.strip('`')
                    break
            await interaction.response.send_modal(self.bot.EditOppsModal(current_opps=current_opps))

        async def end_war(self, interaction: discord.Interaction, status: str, color: discord.Color, title: str):
            # FIX: Guard against non-guild interactions and interactions without a source message.
            if not interaction.guild:
                await interaction.response.send_message("This action can only be performed in a server.", ephemeral=True)
                return
            assert interaction.message is not None

            guild_id = str(interaction.guild.id)
            original_embed = interaction.message.embeds[0]
            
            # Check if this is a debug war. If so, do not record stats.
            if "DEBUG MODE" not in interaction.message.content:
                start_time = interaction.message.created_at
                end_time = interaction.created_at
                duration = end_time - start_time
                initiator_id = self.get_author_id_from_embed(original_embed)
                
                roblox_user, opponents_str, region = "Unknown", "Unknown", "Unknown"
                for field in original_embed.fields:
                    if field.name == "🛡️ User in Need":
                        # FIX: field.value is str, safe for regex. This resolves the Pylance error
                        # "No overloads for "search" match the provided arguments".
                        match = re.search(r"\*\*Roblox:\*\* `(.+?)`", field.value)
                        if match: roblox_user = match.group(1)
                    elif field.name == "💀 Opponents":
                        opponents_str = field.value.strip('`')
                    elif field.name == "🌍 Region":
                        region = field.value.strip('`')
                
                num_opponents = len([opp.strip() for opp in opponents_str.split(',') if opp.strip()])

                war_record = {
                    "war_id": interaction.message.id, "initiator_id": initiator_id,
                    "initiator_roblox_user": roblox_user, "opponents": opponents_str,
                    "num_opponents": num_opponents, "region": region,
                    "start_time_utc": start_time.isoformat(), "end_time_utc": end_time.isoformat(),
                    "duration_seconds": duration.total_seconds(), "status": status,
                    "concluded_by_id": interaction.user.id
                }
                
                guild_war_data = self.bot.war_data.get(guild_id, [])
                # FIX: Check if guild_war_data is not None (though default=[] makes this safe)
                if guild_war_data is not None:
                    guild_war_data.append(war_record)
                    self.bot.war_data.set(guild_id, guild_war_data)
                    await self.bot.war_data.save()
                
                logger.info(f"War record {interaction.message.id} saved for guild '{interaction.guild.name}' ({guild_id}).")

            original_embed.title = title
            original_embed.color = color
            original_embed.description = "This engagement has concluded."
            original_embed.add_field(name="Status", value=f"Concluded as a **{status}** by {interaction.user.mention}", inline=False)

            # FIX: Check type before disabling.
            for item in self.children:
                if isinstance(item, (Button, discord.ui.Select)):
                    item.disabled = True

            await interaction.response.edit_message(content=f"*This backup request has concluded.*", embed=original_embed, view=self)
            logger.info(f"Backup request concluded as '{status}' by {interaction.user} in guild '{interaction.guild.name}' ({interaction.guild.id})")

        @discord.ui.button(label="Win", style=discord.ButtonStyle.success, custom_id="backup_view:win")
        async def win(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Win", discord.Color.green(), "✔️ Backup Concluded (VICTORY!) ✔️")

        @discord.ui.button(label="Lose", style=discord.ButtonStyle.danger, custom_id="backup_view:lose")
        async def lose(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Loss", discord.Color.red(), "❌ Backup Concluded (DEFEAT) ❌")

        @discord.ui.button(label="Truce", style=discord.ButtonStyle.primary, custom_id="backup_view:truce")
        async def truce(self, interaction: discord.Interaction, button: Button):
            await self.end_war(interaction, "Truce", discord.Color.light_grey(), "🤝 Backup Concluded (TRUCE) 🤝")


# --- Bot instance and event listeners ---
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv('DISCORD_TOKEN')
DEV_GUILD_ID = 1167835890228416623

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = BackupBot(intents=intents, guild_id=DEV_GUILD_ID)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info('Bot is ready and listening for commands.')
    logger.info('------')


# --- Shared Command Logic ---
async def _send_backup_request(
    interaction: discord.Interaction, roblox_user: str, opps: str,
    region: str, link: Optional[str], is_debug: bool # FIX: link can be None
):
    # FIX: Cast client to our custom bot class to inform the type checker of our custom attributes.
    bot_instance = cast(BackupBot, interaction.client)
    
    # FIX: This function requires a guild. Add a guard clause.
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    server_config = bot_instance.configs.get(guild_id)

    if not server_config:
        await interaction.response.send_message(
            "**Bot Not Configured!** An administrator must run the `/setup` command first.",
            ephemeral=True
        )
        return

    allowed_channel_id = server_config.get('allowed_channel_id')
    backup_role_id = server_config.get('backup_role_id')

    if interaction.channel and interaction.channel.id != allowed_channel_id:
        await interaction.response.send_message(
            f"You can only use this command in the <#{allowed_channel_id}> channel.",
            ephemeral=True
        )
        return

    backup_role = interaction.guild.get_role(backup_role_id)
    if not backup_role and not is_debug:
        logger.error(f"Config error in guild '{interaction.guild.name}' ({guild_id}): Backup role ID '{backup_role_id}' not found.")
        await interaction.response.send_message(
            f"Configuration Error: The backup role was not found. An admin should re-run `/setup`.",
            ephemeral=True
        )
        return
        
    custom_color_val = server_config.get("embed_color")
    color = discord.Color(custom_color_val) if custom_color_val is not None else discord.Color.gold()
    
    custom_thumbnail_url = server_config.get("thumbnail_url")
    thumbnail_url = custom_thumbnail_url or "https://i.imgur.com/P5LJ02a.png"

    embed = discord.Embed(
        title="⚔️ Backup Request! ⚔️",
        description="A warrior requires aid! The status of this engagement is **Ongoing**.",
        color=color
    )
    embed.set_thumbnail(url=thumbnail_url)
    user_info = f"**Discord:** {interaction.user.mention}\n**Roblox:** `{roblox_user}`"
    embed.add_field(name="🛡️ User in Need", value=user_info, inline=False)
    embed.add_field(name="💀 Opponents", value=f"`{opps}`", inline=False)
    embed.add_field(name="🌍 Region", value=f"`{region}`", inline=False)

    if link:
        embed.add_field(name="🔗 Join Link", value=f"[Click Here to Join]({link})", inline=False)
    else:
        embed.add_field(name="🔗 Join Link", value="*No link provided. Join via user's Roblox profile.*", inline=False)

    embed.set_footer(text=f"Celestial Sentry | The Supreme Manager | Author ID: {interaction.user.id}")

    # FIX: Ensure backup_role is not None before accessing .mention
    message_content = f"**DEBUG MODE:** No roles pinged." if is_debug or not backup_role else backup_role.mention
    allowed_mentions = discord.AllowedMentions.none() if is_debug else discord.AllowedMentions(roles=True)

    await interaction.response.send_message(
        content=message_content, embed=embed, allowed_mentions=allowed_mentions,
        view=bot.BackupControlsView(bot=bot)
    )
    logger.info(f"Backup request started by {interaction.user} in guild '{interaction.guild.name}' (Debug: {is_debug})")

    if not link:
        await interaction.followup.send(
            content="**Friendly Reminder:** You didn't provide a server link. Make sure your **Roblox joins are on** so people can help!",
            ephemeral=True
        )


# --- Slash Command Definitions ---
@bot.tree.command(name="help", description="Shows a list of all available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Celestial Sentry Commands",
        description="Here's a list of commands you can use:",
        color=discord.Color.blurple()
    )
    
    admin_commands = ["setup", "debugbackup", "resetstats"]
    
    # FIX: Some command types (like context menu) don't have descriptions. Accessing command.description
    # directly would raise an AttributeError. Using a fallback resolves this.
    for command in bot.tree.get_commands():
        description = command.description or "No description available."
        if command.name in admin_commands:
            description += " `[ADMIN]`"
        
        embed.add_field(name=f"/{command.name}", value=description, inline=False)
    
    embed.set_footer(text="Contact an administrator for help with admin-only commands.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setup", description="[ADMIN] Configure the bot for this server.")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.describe(
    backup_channel="The channel where backup requests are sent.", 
    backup_role="The role to be pinged for backup requests.",
    embed_color="A hex color code for embeds (e.g., #FF5733).",
    thumbnail_url="A URL for the embed thumbnail image."
)
async def setup_command(
    interaction: discord.Interaction, 
    backup_channel: discord.TextChannel, 
    backup_role: discord.Role,
    embed_color: Optional[str] = None,   # FIX: These parameters are optional
    thumbnail_url: Optional[str] = None
):
    # FIX: Cast client and ensure command is used in a guild
    bot_instance = cast(BackupBot, interaction.client)
    if not interaction.guild:
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return
        
    guild_id = str(interaction.guild.id)
    
    # FIX: Providing a default {} ensures config_data is a dict, preventing the "Object of type 'None'
    # is not subscriptable" error if the guild has no existing config.
    config_data = bot_instance.configs.get(guild_id, {})
    config_data["backup_role_id"] = backup_role.id
    config_data["allowed_channel_id"] = backup_channel.id

    embed = discord.Embed(title="✅ Configuration Updated!", description="The bot's settings have been updated.", color=discord.Color.green())
    embed.add_field(name="Backup Channel", value=backup_channel.mention, inline=False)
    embed.add_field(name="Backup Role", value=backup_role.mention, inline=False)
    
    if embed_color:
        match = re.match(r'^#?([A-Fa-f0-9]{6})$', embed_color)
        if match:
            color_int = int(match.group(1), 16)
            config_data['embed_color'] = color_int
            embed.add_field(name="Embed Color", value=f"`#{match.group(1).upper()}`", inline=True)
        else:
            await interaction.response.send_message("❌ **Invalid Color:** Please use a valid 6-digit hex format (e.g., `#FF5733`).", ephemeral=True)
            return

    if thumbnail_url:
        if thumbnail_url.startswith(('http://', 'https://')):
            config_data['thumbnail_url'] = thumbnail_url
            embed.add_field(name="Thumbnail URL", value=f"[Link]({thumbnail_url})", inline=True)
        else:
            await interaction.response.send_message("❌ **Invalid URL:** Thumbnail URL must start with `http://` or `https://`.", ephemeral=True)
            return

    bot_instance.configs.set(guild_id, config_data)
    await bot_instance.configs.save()
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"Bot configured for guild '{interaction.guild.name}' ({guild_id}) by admin {interaction.user}.")


@bot.tree.command(name="backup", description="Request backup from your allies.")
@discord.app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.guild_id, i.user.id))
@discord.app_commands.describe(roblox_user="Your Roblox username or profile link.", opps="The usernames of the players teaming on you.", link="Optional: A private server link for easy joining.")
@discord.app_commands.choices(region=[
    discord.app_commands.Choice(name="🇺🇸 US East", value="US East"), discord.app_commands.Choice(name="🇺🇸 US West", value="US West"),
    discord.app_commands.Choice(name="🇪🇺 Europe", value="Europe"), discord.app_commands.Choice(name="🇦🇺 Australia", value="Australia"),
    discord.app_commands.Choice(name="🇸🇬 Asia", value="Asia"), discord.app_commands.Choice(name="❓ Unknown", value="Unknown"),
])
# FIX: `link` can be None, use Optional type hint
async def backup_command(interaction: discord.Interaction, roblox_user: str, opps: str, region: discord.app_commands.Choice[str], link: Optional[str] = None):
    await _send_backup_request(interaction, roblox_user, opps, region.value, link, is_debug=False)


@bot.tree.command(name="debugbackup", description="[ADMIN] Create a backup request without pinging roles.")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.choices(region=[
    discord.app_commands.Choice(name="🇺🇸 US East", value="US East"), discord.app_commands.Choice(name="🇺🇸 US West", value="US West"),
    discord.app_commands.Choice(name="🇪🇺 Europe", value="Europe"), discord.app_commands.Choice(name="🇦🇺 Australia", value="Australia"),
    discord.app_commands.Choice(name="🇸🇬 Asia", value="Asia"), discord.app_commands.Choice(name="❓ Unknown", value="Unknown"),
])
# FIX: `link` can be None, use Optional type hint
async def debugbackup_command(interaction: discord.Interaction, roblox_user: str, opps: str, region: discord.app_commands.Choice[str], link: Optional[str] = None):
    await _send_backup_request(interaction, roblox_user, opps, region.value, link, is_debug=True)


@bot.tree.command(name="warstats", description="View statistics about past backup requests.")
async def warstats_command(interaction: discord.Interaction):
    # FIX: Guard against non-guild usage.
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
        
    guild_id = str(interaction.guild.id)
    guild_wars = bot.war_data.get(guild_id, [])

    if not guild_wars:
        await interaction.response.send_message("No war data has been recorded for this server yet.", ephemeral=True)
        return

    total_wars = len(guild_wars)
    wins = sum(1 for w in guild_wars if w['status'] == 'Win')
    losses = sum(1 for w in guild_wars if w['status'] == 'Loss')
    truces = sum(1 for w in guild_wars if w['status'] == 'Truce')
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    total_duration = sum(w.get('duration_seconds', 0) for w in guild_wars)
    avg_duration_secs = total_duration / total_wars if total_wars > 0 else 0
    m, s = divmod(avg_duration_secs, 60); h, m = divmod(m, 60)
    avg_duration_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    embed = discord.Embed(title=f"War Statistics for {interaction.guild.name}", description=f"Analysis of **{total_wars}** concluded engagements.", color=discord.Color.blue())
    # FIX: guild.icon can be None, so handle this case.
    thumbnail_url = interaction.guild.icon.url if interaction.guild.icon else "https://i.imgur.com/P5LJ02a.png"
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name="📈 Overall Record", value=f"**{wins}** Wins / **{losses}** Losses / **{truces}** Truces", inline=False)
    embed.add_field(name="📊 Win Rate", value=f"`{win_rate:.1f}%` (Based on Wins and Losses)", inline=True)
    embed.add_field(name="⏱️ Avg. Duration (H:M:S)", value=f"`{avg_duration_str}`", inline=True)

    if guild_wars:
        recent_wars = sorted(guild_wars, key=lambda w: w['end_time_utc'], reverse=True)[:5]
        recent_wars_text = [
            f"<t:{int(datetime.datetime.fromisoformat(w['start_time_utc']).timestamp())}:R>: **{w['status']}** vs {w['num_opponents']} opp(s) by <@{w['initiator_id']}>"
            for w in recent_wars
        ]
        embed.add_field(name="📜 Recent Engagements", value="\n".join(recent_wars_text), inline=False)

    await interaction.response.send_message(embed=embed)
    logger.info(f"War stats viewed by {interaction.user} in guild '{interaction.guild.name}'.")


@bot.tree.command(name="resetstats", description="[ADMIN] Reset all war statistics for this server.")
@discord.app_commands.checks.has_permissions(administrator=True)
async def resetstats_command(interaction: discord.Interaction):
    # FIX: Guard against non-guild usage.
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)

    if not bot.war_data.get(guild_id):
        await interaction.response.send_message("ℹ️ No war data found for this server; no action is needed.", ephemeral=True)
        return

    # FIX: The view's __init__ now correctly accepts User or Member
    view = bot.ConfirmResetView(bot=bot, author=interaction.user)
    await interaction.response.send_message(
        "**⚠️ Are you sure?**\nThis action is irreversible and will delete all war statistics for this server.",
        view=view,
        ephemeral=True
    )

    await view.wait()
    
    if not view.confirmed:
        # FIX: Check item type before disabling.
        for item in view.children:
            if isinstance(item, (Button, discord.ui.Select)):
                item.disabled = True
        await interaction.edit_original_response(
            content="Confirmation timed out. No stats were reset.",
            view=view
        )


# --- Main execution block ---
if __name__ == "__main__":
    if not TOKEN:
        logger.critical("FATAL: DISCORD_TOKEN environment variable not set.")
        sys.exit("Environment variable not set. Check log file for details.")
    if not DEV_GUILD_ID:
        logger.critical("FATAL: DEV_GUILD_ID is not set. Please set the variable in the script.")
        sys.exit("Developer Guild ID not set. Check log file for details.")
        
    try:
        # Pass log_handler=None as we have configured the root logger ourselves.
        bot.run(TOKEN, log_handler=None)
    except Exception as e:
        logger.critical("Bot run failed with a fatal exception.", exc_info=e)
        sys.exit("Bot encountered a fatal error. Check log file for details.")