import os
from discord.ext import commands
import discord
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import json

load_dotenv()  # Loads environment variables from .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("No BOT_TOKEN found in environment variables")

@dataclass
class Session:
    is_active: bool = False
    start_time: float = 0.0
    break_duration: int = 0  # Break duration in seconds
    end_time: datetime = None  # To track the end time
    manually_ended: bool = False  # Track if the break was manually ended
    last_break_end_time: datetime = None  # End time of the last break
    last_break_duration: int = 0  # Duration of the last break in seconds
    timezone: ZoneInfo = ZoneInfo('UTC')  # Default timezone

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store sessions per guild (server)
sessions = {}

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    load_sessions()  # Load sessions when the bot starts

def format_duration(duration_seconds):
    if duration_seconds >= 3600:
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        minutes, seconds = divmod(duration_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
def format_break_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60

    if hours > 0 and minutes > 0:
        return f"{hours} hour{'s' if hours !=1 else ''} and {minutes} minute{'s' if minutes !=1 else ''}"
    elif hours > 0:
        return f"{hours} hour{'s' if hours !=1 else ''}"
    else:
        return f"{minutes} minute{'s' if minutes !=1 else ''}"

async def countdown(ctx, session):
    try:
        now = datetime.now(session.timezone)
        duration = int((session.end_time - now).total_seconds())
        message = await ctx.send(f"`Break active: {format_duration(duration)}, be back at: {session.end_time.strftime('%H:%M %Z')}`")

        warned_two_minutes = False
        warned_thirty_seconds = False

        while duration > 0:
            if not session.is_active:
                break

            await asyncio.sleep(5)
            now = datetime.now(session.timezone)
            duration = int((session.end_time - now).total_seconds())

            # Warnings...
            if 0 < duration <= 120 and not warned_two_minutes:
                await ctx.send("@everyone\n `2 minutes left of the break.`")
                warned_two_minutes = True

            if 0 < duration <= 30 and not warned_thirty_seconds:
                await ctx.send("@everyone\n `Warning! Last 30 seconds of the break.`")
                warned_thirty_seconds = True

            # Update the countdown message
            try:
                await message.edit(content=f"`Break active: {format_duration(duration)}, be back at: {session.end_time.strftime('%H:%M %Z')}`")
            except discord.NotFound:
                message = await ctx.send(f"`Break active: {format_duration(duration)}, be back at: {session.end_time.strftime('%H:%M %Z')}`")

        if session.is_active:
            await ctx.send(f"@everyone\n`Break is over! It's {session.end_time.strftime('%H:%M %Z')}. Time to work!`")
            # Record the last break info
            start_time_dt = datetime.fromtimestamp(session.start_time, tz=session.timezone)
            session.last_break_end_time = session.end_time
            session.last_break_duration = int((session.end_time - start_time_dt).total_seconds())
            session.is_active = False
            save_sessions()
    except Exception as e:
        await ctx.send(f"An error occurred during the countdown: {e}")
        session.is_active = False

LUNCH_BREAK_TIME = 30 * 60  # 30 minutes in seconds

@bot.command()
@commands.has_permissions(manage_guild=True)
async def start(ctx, end_time: str):
    guild_id = ctx.guild.id
    if guild_id not in sessions:
        sessions[guild_id] = Session()
    session = sessions[guild_id]

    if session.is_active:
        await ctx.send("A break is already running.")
        return

    # Parsing the provided end time (HH:MM)
    try:
        end_hour, end_minute = map(int, end_time.strip().split(":"))
        if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            raise ValueError

        now = datetime.now(session.timezone)
        session.end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        # If the end time is earlier than the current time, assume it's the next day
        if session.end_time <= now:
            session.end_time += timedelta(days=1)
            await ctx.send(f"Note: The end time is set for tomorrow at {session.end_time.strftime('%H:%M %Z')}.")

        session.is_active = True
        session.start_time = now.timestamp()
        session.manually_ended = False

        # Calculate the duration in minutes
        session.break_duration = int((session.end_time - now).total_seconds())
        break_duration_formatted = format_break_duration(session.break_duration)

        if session.break_duration >= LUNCH_BREAK_TIME:
            special_message = "`LUNCH BREAK`\n"
        else:
            special_message = ""

        human_readable_time = now.strftime("%H:%M %Z")
        await ctx.send(
            f"@everyone\n"
            f"{special_message}"
            f"**Break started at:** {human_readable_time}\n"
            f"**Break duration:** {break_duration_formatted}\n"
            f"**Be back at:** {session.end_time.strftime('%H:%M %Z')}\n"
        )       
        save_sessions()

        # Start the countdown
        await countdown(ctx, session)

    except ValueError:
        await ctx.send("Invalid time format! Please use HH:MM in 24-hour format, e.g., !start 14:20.")
    except Exception as e:
        await ctx.send(f"An error occurred while starting the break: {e}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def stop(ctx):
    guild_id = ctx.guild.id
    if guild_id not in sessions or not sessions[guild_id].is_active:
        await ctx.send("No break is currently active.")
        return

    session = sessions[guild_id]
    session.is_active = False
    session.manually_ended = True
    end_time = datetime.now(session.timezone)
    start_time_dt = datetime.fromtimestamp(session.start_time, tz=session.timezone)
    duration = (end_time - start_time_dt).total_seconds()

    # Record the last break info
    session.last_break_end_time = end_time
    session.last_break_duration = int(duration)

    # Convert duration to timedelta for easy breakdown
    duration_timedelta = timedelta(seconds=int(duration))

    # Extract hours, minutes, and seconds
    hours, remainder = divmod(duration_timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Create a human-readable duration message
    duration_message = []
    if hours > 0:
        duration_message.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        duration_message.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or len(duration_message) == 0:
        duration_message.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    human_readable_duration = ', '.join(duration_message)

    await ctx.send(f"Break manually stopped after: {human_readable_duration}")
    save_sessions()

@bot.command()
async def last(ctx):
    guild_id = ctx.guild.id
    if guild_id not in sessions or sessions[guild_id].last_break_end_time is None:
        await ctx.send("No break has been registered yet.")
    else:
        session = sessions[guild_id]
        end_time_str = session.last_break_end_time.strftime("%H:%M %Z")
        duration_timedelta = timedelta(seconds=session.last_break_duration)
        hours, remainder = divmod(duration_timedelta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        duration_message = []
        if hours > 0:
            duration_message.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            duration_message.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or len(duration_message) == 0:
            duration_message.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        human_readable_duration = ', '.join(duration_message)
        await ctx.send(f"Previous break ended at: {end_time_str} and lasted for {human_readable_duration}.")

@bot.command()
async def how(ctx):
    description = """
    **Break Bot Commands:**
    `!start HH:MM` - Starts a break until the specified end time (24-hour format).
    `!stop` - Stops the current break.
    `!last` - Displays information about the last break.
    `!settimezone <Timezone>` - Sets the timezone for the server (admin only) Example: `!settimezone Europe/Stockholm`
    `!how`  - Shows this message.
    """
    await ctx.send(description)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def settimezone(ctx, *, timezone_name: str = None):
    if timezone_name is None:
        await ctx.send("Please specify a timezone. Example usage: `!settimezone Europe/Stockholm`.")
        return

    guild_id = ctx.guild.id
    if guild_id not in sessions:
        sessions[guild_id] = Session()

    session = sessions[guild_id]

    try:
        # Normalize the timezone name (strip whitespace)
        timezone_name = timezone_name.strip()
        
        # Attempt to create a ZoneInfo object
        new_timezone = ZoneInfo(timezone_name)
        
        # Get current timezone name
        current_timezone_name = session.timezone.key if session.timezone else "UTC"
        
        # Check if the timezone is the same as the current one
        if timezone_name == current_timezone_name:
            await ctx.send(f"The timezone is already set to `{timezone_name}`.")
            return
        
        # Update the timezone
        session.timezone = new_timezone
        save_sessions()
        await ctx.send(f"Timezone changed from `{current_timezone_name}` to `{timezone_name}`.")

    except Exception:
        # List of common timezones for examples
        common_timezones = [
            "UTC",
            "Europe/Stockholm",
            "America/New_York",
            "America/Los_Angeles",
            "Asia/Tokyo",
            "Europe/London",
            "Australia/Sydney"
        ]
        timezone_list = ", ".join(f"`{tz}`" for tz in common_timezones)
        await ctx.send(
            "Invalid timezone! Please provide a valid timezone name from the IANA database.\n"
            "Examples of valid timezones include:\n"
            f"{timezone_list}\n"
            "You can find a full list of timezones here: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>"
        )

# Error handling for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, discord.Forbidden):
            await ctx.send("I don't have the necessary permissions to perform that action.")
        else:
            await ctx.send(f"An unexpected error occurred: {error.original}")
    else:
        await ctx.send(f"An error occurred: {error}")


SESSION_FILE = "sessions.json"

def save_sessions():
    with open(SESSION_FILE, "w") as f:
        data = {
            str(guild_id): {
                "is_active": session.is_active,
                "start_time": session.start_time,
                "break_duration": session.break_duration,
                "end_time": session.end_time.timestamp() if session.end_time else None,
                "manually_ended": session.manually_ended,
                "last_break_end_time": session.last_break_end_time.timestamp() if session.last_break_end_time else None,
                "last_break_duration": session.last_break_duration,
                "timezone": session.timezone.key if session.timezone else "UTC",
            }
            for guild_id, session in sessions.items()
        }
        json.dump(data, f)

def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            for guild_id, session_data in data.items():
                timezone_name = session_data.get("timezone", "UTC")
                sessions[int(guild_id)] = Session(
                    is_active=session_data.get("is_active", False),
                    start_time=session_data.get("start_time", 0.0),
                    break_duration=session_data.get("break_duration", 0),
                    end_time=datetime.fromtimestamp(session_data["end_time"], tz=ZoneInfo(timezone_name)) if session_data.get("end_time") else None,
                    manually_ended=session_data.get("manually_ended", False),
                    last_break_end_time=datetime.fromtimestamp(session_data["last_break_end_time"], tz=ZoneInfo(timezone_name)) if session_data.get("last_break_end_time") else None,
                    last_break_duration=session_data.get("last_break_duration", 0),
                    timezone=ZoneInfo(timezone_name)
                )

bot.run(BOT_TOKEN)
