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
    
    bot = commands.Bot(command_prefix=['Woguri ', 'woguri '], intents=intents)
    logging.info("Bot instance created")
    return bot

async def setup_error_handlers(bot: commands.Bot) -> None:
    """Set up error handlers for the bot (Oguri Cap style)."""
    
    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        """Handle command errors with Oguri Cap's calm tone."""
        
        if isinstance(error, commands.CommandNotFound):
            # Handle both "Woguri " and "woguri " prefixes
            message_content = ctx.message.content if ctx.message.content else ""
            if message_content.startswith('Woguri '):
                invalid_command = message_content.replace('Woguri ', '', 1).split()[0] if message_content else "???"
            elif message_content.startswith('woguri '):
                invalid_command = message_content.replace('woguri ', '', 1).split()[0] if message_content else "???"
            else:
                invalid_command = "???"
            
            logging.warning(f"Invalid command '{invalid_command}' used by {ctx.author} ({ctx.author.id}) in guild {ctx.guild.id if ctx.guild else 'DM'}")
            
            responses = [
                f"'{invalid_command}' isn’t a valid command.",
                f"I don’t recognise '{invalid_command}'.",
                f"That command doesn’t exist.",
                f"'{invalid_command}'... not found.",
                f"No command by that name.",
                f"Invalid command: '{invalid_command}'.",
                f"I don’t think that’s right.",
                f"Check your input. '{invalid_command}' isn’t one of mine."
            ]
            
            import random
            response = random.choice(responses)
            await ctx.send(response, delete_after=8)
            
        elif isinstance(error, commands.NotOwner):
            logging.warning(f"Non-owner {ctx.author} ({ctx.author.id}) tried to use owner command {ctx.command}")
            
            responses = [
            "That command’s above your pay grade.",
            "Only really cool people can use that command. And you're...",
            "Oh thats not..."
            "He pays for my food. That’s why he gets access.",
            "You’re not cleared for that. Sorry buddy.",
            "You could try again, but it won’t change anything."
        ]
            
            import random
            response = random.choice(responses)
            await ctx.send(response, delete_after=8)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            logging.info(f"Missing argument for command {ctx.command} by {ctx.author}")
            await ctx.send("You’re missing a required argument.", delete_after=10)
            
        elif isinstance(error, commands.BadArgument):
            logging.info(f"Bad argument for command {ctx.command} by {ctx.author}: {error}")
            await ctx.send("Invalid input type. Try again.", delete_after=10)
            
        else:
            logging.error(f"Unexpected error in command {ctx.command}: {error}", exc_info=True)
            await ctx.send("An error occurred. I’ll keep running.", delete_after=10)

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
    await setup_error_handlers(bot)
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



