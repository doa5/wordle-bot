import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(levelname)-8s] %(message)s'
    )
    logging.info("Logging system initialized")


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot instance."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(command_prefix='woguri ', intents=intents)
    logging.info("Bot instance created")
    return bot

async def load_cogs(bot: commands.Bot) -> None:
    """Load all cog extensions."""
    cogs_to_load = [
        "cogs.role_manager",
        "cogs.wordle_parser",
        "cogs.leaderboard",
        "utils.database",
        "cogs.oguri_cap"
    ]
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            logging.info(f"Loaded cog: {cog}")
        except Exception as e:
            logging.error(f"Failed to load cog {cog}: {e}")

async def main() -> None:

    setup_logging()
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logging.error("DISCORD_TOKEN not found in environment variables!")
        return

    bot = create_bot()
    await load_cogs(bot)
    try:
        await bot.start(token)
        logging.info("Woguri is awake!")
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise



