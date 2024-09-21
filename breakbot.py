import json
from discord.ext import commands
import discord
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

@dataclass
class Session:
    is_active: bool = False
    start_time: float = 0.0
    break_duration: int = 0  # Break duration in seconds
    end_time: datetime = None  # To track the end time
    manually_ended: bool = False  # Track if the break was manually ended
    last_break_end_time: datetime = None  # End time of the last break
    last_break_duration: int = 0  # Duration of the last break in seconds

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to store sessions per guild (server)
sessions = {}

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

async def countdown(ctx, session):
    duration = int((session.end_time - datetime.now()).total_seconds())
    message = await ctx.send(f"Break active: {duration//60:02d}:{duration%60:02d}, be back at: {session.end_time.strftime('%H:%M')}")

    warned_two_minutes = False
    warned_thirty_seconds = False

    while duration > 0:
        if not session.is_active:
            # If the session was manually stopped, break out of the loop
            break

        await asyncio.sleep(5)  # Update every 5 seconds
        duration = int((session.end_time - datetime.now()).total_seconds())
        minutes, seconds = divmod(duration, 60)

        # Warn when 2 minutes are left
        if 0 < duration <= 120 and not warned_two_minutes:
            await ctx.send("@everyone 2 minutes left of the break.")
            warned_two_minutes = True

        # Warn when 30 seconds are left
        if 0 < duration <= 30 and not warned_thirty_seconds:
            await ctx.send("@everyone Warning! Last 30 seconds of the break.")
            warned_thirty_seconds = True

        # Update the countdown message
        await message.edit(content=f"Break active: {minutes:02d}:{seconds:02d}, be back at: {session.end_time.strftime('%H:%M')}")

    if session.is_active:
        await ctx.send(f"Break is over! It's {session.end_time.strftime('%H:%M')}. Time to work")
        # Record the last break info
        session.last_break_end_time = session.end_time
        session.last_break_duration = int((session.end_time - datetime.fromtimestamp(session.start_time)).total_seconds())
        session.is_active = False

@bot.command()
@commands.has_permissions(manage_guild=True)  # Restrict to users with Manage Server permission
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
        end_hour, end_minute = map(int, end_time.split(":"))
        if not (0 <= end_hour <= 23 and 0 <= end_minute <= 59):
            raise ValueError

        now = datetime.now()
        session.end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        # If the end time is earlier than the current time, assume it's the next day
        if session.end_time <= now:
            session.end_time += timedelta(days=1)
            await ctx.send(f"Note: The end time is set for tomorrow at {session.end_time.strftime('%H:%M')}.")

        session.is_active = True
        session.start_time = now.timestamp()
        session.manually_ended = False

        # Calculate the duration in minutes
        session.break_duration = int((session.end_time - now).total_seconds())
        break_minutes = session.break_duration // 60

        human_readable_time = now.strftime("%H:%M")
        await ctx.send(f"@everyone Break started at: {human_readable_time}. Break will be around {break_minutes} minutes. Be back at: {session.end_time.strftime('%H:%M')}.")

        # Start the countdown
        await countdown(ctx, session)

    except ValueError:
        await ctx.send("Wrong format! Use HH:MM, e.g., !start 14:20.")

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
    end_time = datetime.now()
    duration = (end_time - datetime.fromtimestamp(session.start_time)).total_seconds()

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

@bot.command()
async def last(ctx):
    guild_id = ctx.guild.id
    if guild_id not in sessions or sessions[guild_id].last_break_end_time is None:
        await ctx.send("No break has been registered yet.")
    else:
        session = sessions[guild_id]
        end_time_str = session.last_break_end_time.strftime("%H:%M")
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

# Error handling for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.CommandInvokeError):
        # Handle specific invoke errors if needed
        await ctx.send(f"An error occurred: {error.original}")
    else:
        await ctx.send(f"An error occurred: {error}")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run('YOUR_BOT_TOKEN')
