import discord
from discord.ext import commands, tasks
import time
import asyncio
from datetime import datetime, timedelta
import json

# Load the Discord token from botkey.json
with open("botkey.json") as f:
    bot_key_data = json.load(f)
    DISCORD_TOKEN = bot_key_data["token"]  # Fixed this to use brackets, not parentheses

# Define the bot and set its command prefix
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define authorized users (Could also store the users in a separate file)
AUTHORIZED_USERS = ["discord_username_here"]

# A dictionary to store information about breaks
break_info = {
    "last_break_length": None,
    "last_break_end_time": None
}

# Which channel to use for breaks
BREAK_CHANNEL_NAME = "breakbot"

# Global variable for break task, so it can be stopped
break_task = None

# Helper function to find the correct channel by name
async def find_break_channel(ctx):
    # Looks for the channel with a specific name
    for channel in ctx.guild.channels:
        if channel.name == BREAK_CHANNEL_NAME:
            return channel
    return None

# Command to start the break timer
@bot.command()
async def start_break(ctx, minutes: int):
    global break_task
    # Check if the user is authorized
    if str(ctx.author) not in AUTHORIZED_USERS:
        await ctx.send(f"Tyvärr {ctx.author.mention}, du är inte behörig att använda detta kommando.")
        return
    
    # Find the correct breakbot channel
    break_channel = await find_break_channel(ctx)
    if not break_channel:
        await ctx.send(f"Tyvärr, jag kunde inte hitta #{BREAK_CHANNEL_NAME} kanalen.")
        return
    
    # Check if break task is already running and inform the user
    if break_task is not None and not break_task.cancelled():
        await break_channel.send("En rast är redan aktiv! Du kan välja att vänta eller stoppa den genom att skriva '!stop'.")
        return

    # Convert minutes to seconds
    total_seconds = minutes * 60

    # Calculate the time to return after the break
    return_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")

    # Notify when the break starts including the return time
    await break_channel.send(f"@everyone Dags för {minutes} minuters rast! Åter kl: {return_time}")

    # Define the countdown logic as an async task that can be stopped
    async def countdown():
        global break_info
        nonlocal total_seconds

        # Countdown loop
        while total_seconds:
            mins, secs = divmod(total_seconds, 60)
            timer = "{:02d}:{:02d}".format(mins, secs)

            # Send warnings at 2 minutes and 30 seconds
            if total_seconds == 2 * 60:
                await break_channel.send("@everyone Nu är det 2 minuter kvar!")
            if total_seconds == 30:
                await break_channel.send("@everyone Nu är det bara 30 sekunder kvar!")

            # Wait for 1 second and reduce the total_seconds
            await asyncio.sleep(1)
            total_seconds -= 1

        # Timer finished, send the final message
        end_time = datetime.now().strftime("%H:%M")
        break_info["last_break_length"] = f"{minutes} minuter"
        break_info["last_break_end_time"] = end_time
        await break_channel.send(f"@everyone Rasten är slut! Den senaste rasten var {minutes} minuter lång och tog slut kl: {end_time}.")

    # Start the countdown task
    break_task = bot.loop.create_task(countdown())

# Command to stop the break timer
@bot.command()
async def stop(ctx):
    global break_task
    # Check if the user is authorized
    if str(ctx.author) not in AUTHORIZED_USERS:
        await ctx.send(f"Tyvärr {ctx.author.mention}, du är inte behörig att använda detta kommando.")
        return

    # Find the correct breakbot channel
    break_channel = await find_break_channel(ctx)
    if not break_channel:
        await ctx.send(f"Tyvärr, jag kunde inte hitta #{BREAK_CHANNEL_NAME} kanalen.")
        return

    # If no break is running, notify the user
    if break_task is None or break_task.cancelled():
        await break_channel.send("Ingen rast är för närvarande aktiv.")
    else:
        # Cancel the current break task
        break_task.cancel()
        await break_channel.send("@everyone Rasten har stoppats i förtid.")

# Command to show when the last break ended and how long it was
@bot.command()
async def lastbreak(ctx):
    # Find the breakbot channel
    break_channel = await find_break_channel(ctx)
    if not break_channel:
        await ctx.send(f"Tyvärr, jag kunde inte hitta #{BREAK_CHANNEL_NAME} kanalen.")
        return

    if break_info["last_break_length"] and break_info["last_break_end_time"]:
        await break_channel.send(f"Den senaste rasten varade i {break_info['last_break_length']} och slutade kl: {break_info['last_break_end_time']}.")
    else:
        await break_channel.send("Ingen rast har startats än.")

# Run the bot using the token from botkey.json
bot.run(DISCORD_TOKEN)