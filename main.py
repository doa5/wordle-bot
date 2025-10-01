import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import time
import asyncio
import sqlite3
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Database setup
def init_database():
    """Initialize SQLite database for Wordle scores"""
    conn = sqlite3.connect('wordle_scores.db')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wordle_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            score INTEGER NOT NULL,
            date TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Database initialized!")

# Bot setup
# Configure logging to show in terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-8s] %(message)s')

print("woguri is all fired up...")
logging.info("Logging system initialized")

# Initialize database on startup
init_database()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix='woguri ', intents=intents)

# Setup event for when the bot is ready
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user.name} - {bot.user.id}")
    print(f"I'm ready, {bot.user.name} take off!")
    # Start the daily reset task
    daily_reset_task.start()

# Simple message response
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if this is a Wordle bot message
    if "day streak" in message.content and "Here are yesterday's results:" in message.content:
        await parse_wordle_results(message)

    if message.content.lower() == 'woguri':
        await message.channel.send('Hello?')

    if "food" in message.content.lower():
        await message.channel.send('Did someone say food?')

    await bot.process_commands(message)

# Silly ping command
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
    logging.info(f"Ping command used by {ctx.author}")


# Command to assign "done" role to be used after completing the wordle
role_name = "done"

@bot.command()
async def done(ctx):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} so you are done?")
        logging.info(f"Assigned 'done' role to {ctx.author}")
    else:
        await ctx.send(f"Role '{role_name}' not found.")
        logging.warning(f"Role '{role_name}' not found in guild {ctx.guild.name}")

# Removal of "done" role when its midnight (12 AM)
@bot.command()
async def reset(ctx):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        for member in ctx.guild.members:
            if role in member.roles:
                await member.remove_roles(role)
        await ctx.send("All 'done' roles have been removed. Good luck.")
        logging.info(f"All 'done' roles removed by {ctx.author}")
    else:
        await ctx.send(f"Role '{role_name}' not found.")
        logging.warning(f"Role '{role_name}' not found in guild {ctx.guild.name}")

# Weekly leaderboard command
@bot.command()
async def top(ctx):
    """Show weekly Wordle leaderboard"""
    # Get start and end of current week (Monday to Sunday)
    today = datetime.now()
    days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
    week_start = today - timedelta(days=days_since_monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # Query database for this week's scores
    conn = sqlite3.connect('wordle_scores.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, SUM(score) as total_score, COUNT(*) as games_played
        FROM wordle_scores 
        WHERE guild_id = ? AND date BETWEEN ? AND ?
        GROUP BY user_id 
        ORDER BY total_score ASC
        LIMIT 10
    ''', (str(ctx.guild.id), week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
    logging.info(f"Top scores queried for guild {ctx.guild.id}")
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        await ctx.send("No scores recorded this week.")
        logging.info(f"No scores found for guild {ctx.guild.id} this week.")
        return
    
    # Format leaderboard
    leaderboard = "**Weekly Wordle Leaderboard**\n"
    leaderboard += f"*Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d')}*\n\n"
    
    for i, (user_id, username, total_score, games) in enumerate(results, 1):
        if i == 1:
            leaderboard += f"👑 **{username}**: {total_score} points\n"
        else:
            leaderboard += f"{i}. **{username}**: {total_score} points\n"

    await ctx.send(leaderboard)
    logging.info(f"Weekly leaderboard sent for guild {ctx.guild.id}")

# Automatic daily reset task
@tasks.loop(hours=24)
async def daily_reset_task():
    """Automatically reset 'done' roles at midnight"""
    # Wait until it's midnight
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    wait_seconds = (midnight - now).total_seconds()
    
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
    
    # Remove 'done' role from all members
    role_name = "done"
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            for member in guild.members:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        logging.info(f"Removed 'done' role from {member.name} in {guild.name}")
                    except discord.Forbidden:
                        logging.warning(f"No permission to remove role from {member.name}")
                    except Exception as e:
                        logging.error(f"Error removing role from {member.name}: {e}")

            # Send message to a specific channel
            channel = discord.utils.get(guild.channels, id=1253606896917549110) 
            if channel:
                await channel.send("All 'done' roles have been removed. Good luck.")

    logging.info("Daily reset completed at midnight!")




# Function to save Wordle score to database
def save_wordle_score(user_id, username, score, guild_id):
    """Save a Wordle score to the database"""
    conn = sqlite3.connect('wordle_scores.db')
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if this user already has a score for today
    cursor.execute('''
        SELECT id FROM wordle_scores 
        WHERE user_id = ? AND date = ? AND guild_id = ?
    ''', (user_id, today, guild_id))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing score
        cursor.execute('''
            UPDATE wordle_scores 
            SET score = ?, username = ?, timestamp = CURRENT_TIMESTAMP
            WHERE user_id = ? AND date = ? AND guild_id = ?
        ''', (score, username, user_id, today, guild_id))
        logging.info(f"Updated score for {username}: {score}")
    else:
        # Insert new score
        cursor.execute('''
            INSERT INTO wordle_scores (user_id, username, score, date, guild_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, score, today, guild_id))
        logging.info(f"Added new score for {username}: {score}")
    
    conn.commit()
    conn.close()

# Function to parse Wordle results
async def parse_wordle_results(message):
    """Parse Wordle bot results and extract scores"""
    import re

    logging.info(f"Parsing Wordle message from {message.author}")
    logging.info(f"Message content:\n{message.content}")

    total_saved = 0
    
    # Parse each line to get users and their scores
    lines = message.content.split('\n')
    for line in lines:
        if '/6:' in line:
            # Extract score and users from each line (including X/6 for failures)
            score_match = re.search(r'(\d|X)/6:', line)
            if score_match:
                score_str = score_match.group(1)
                # Convert X to 8 points, numbers stay as numbers
                score = 8 if score_str == 'X' else int(score_str)
                
                # Extract mentioned users (@ mentions)
                user_mentions = re.findall(r'<@!?(\d+)>', line)
                
                # Save each user's score to database
                for user_id in user_mentions:
                    try:
                        # Get the user object to get their username
                        user = message.guild.get_member(int(user_id))
                        username = user.display_name if user else f"Unknown_{user_id}"
                        
                        # Save to database
                        save_wordle_score(user_id, username, score, str(message.guild.id))
                        total_saved += 1
                        print(f"✅ SAVED: {username} = {score} points")
                        
                    except Exception as e:
                        logging.error(f"Error saving score for user {user_id}: {e}")
    
    if total_saved > 0:
        await message.channel.send(f"Saved {total_saved} Wordle scores to database!")
    else:
        await message.channel.send("No valid scores found to save.")

@daily_reset_task.before_loop
async def before_daily_reset():
    await bot.wait_until_ready()

bot.run(token)



