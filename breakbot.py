import discord
from discord.ext import commands, tasks
import time
import asyncio
from datetime import datetime, timedelta

# Define the bot and set its command prefix
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define authorized users (Could also store the users in a separate file (maybe I will implement this)
AUTHORIZED_USERS = ["discord_username_here"]

# A dictionary to store information about breaks
break_info = {
    "last_break_length": None,
    "last_break_end_time": None
}

# Commands to start the break timer
@bot.command()
async def start_break(ctx, minutes: int):
    # Checks if the user is authorized
    if str(ctx.author) not in AUTHORIZED_USERS:
        await ctx.send(f"Sorry {ctx.author.mention}, you are not authorized to use this command")
        return
    
    # Converts seconds to minutes
    total_seconds = minutes * 60

    # Calculates the time to return after the break
    return_time = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")

    # Notify when the break starts including the time we return to class
    await ctx.send(f"@everyone Dags för {minutes} minuters rast! Åter Kl: {return_time}")

    # Countdown loop
    while total_seconds:
        mins, secs = divmod(total_seconds, 60)
        timer = "{:02d}:{02d}".format(mins, secs)

        # Sends warnings @ 2 minutes and @ 30 seconds before break is over
        if total_seconds == 2 * 60:
            await ctx.send("@everyone Nu är det bara 2 Minuter kvar!")
        if total_seconds == 30:
            await ctx.send("@everyone Nu är det bara 30 sekunder kvar!")

        await asyncio.sleep(1)
        total_seconds -= 1

    # Timer finished counting, sends the final message
    end_time = datetime.now().strftime("%H:%M")
    break_info["last_break_length"] = f"{minutes} minutes"
    break_info["last_break_end_time"] = end_time
    await ctx.send(f"@everyone Rasten är slut! Den senaste rasten var {minutes} minuter lång och tog slut Kl: {end_time}.")

    # Main logic implemented, now to add verification for the bot and specify channel