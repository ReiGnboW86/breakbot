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