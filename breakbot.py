from discord.ext import commands
import discord
from datetime import timedelta
from dataclasses import dataclass

# BOT_TOKEN = "token"
# CHANNEL_ID = "channel_id"

@dataclass
class Session:
    is_active: bool = False
    start_time: int = 0

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
session = Session()

@bot.event
async def on_ready():
    print("Botten fungerar på servern")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("Hej! Rastbotten är redo!")

@bot.command()
async def start(ctx):
    if session.is_active:
        await ctx.send("Det är redan en rast igång.")
        return
    
    session.is_active = True
    session.start_time = ctx.message.created_at.timestamp()
    human_readable_time = ctx.message.created_at.strftime("%H:%M")
    await ctx.send(f"Rast startad Kl: {human_readable_time}")

@bot.command()
async def end(ctx):
    if not session.is_active:
        await ctx.send("Ingen rast pågår för tillfället.")
        return
    
    session.is_active = False
    end_time = ctx.message.created_at.timestamp()
    duration = end_time - session.start_time
    
    # Convert duration to timedelta for an easy breakdown
    duration_timedelta = timedelta(seconds=int(duration))
    
    # Extracts hours, minutes, and seconds
    hours, remainder = divmod(duration_timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Create a more readable duration message
    duration_message = []
    if hours > 0:
        duration_message.append(f"{hours} timme{"r" if hours > 1 else ""}")
    if minutes > 0:
        duration_message.append(f"{minutes} minut{"er" if minutes > 1 else ""}")
    if seconds > 0 or len(duration_message) == 0:
        duration_message.append(f"{seconds} sekund{"er" if seconds > 1 else ""}")
    
    # Combine the parts into a full message
    human_readable_duration = ', '.join(duration_message)
    
    await ctx.send(f"Rasten tog slut efter: {human_readable_duration}")

bot.run(BOT_TOKEN)