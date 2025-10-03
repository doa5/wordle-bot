import discord
from discord.ext import commands
import logging
import re
import os

class WordleParser(commands.Cog):
    """
    Cog to parse Wordle bot messages and store user scores in the database.
    
    This cog listens for messages from the official Wordle bot, extracts user scores,
    and saves them to a SQLite database for leaderboard tracking.
    """
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the WordleParser with bot instance."""
        self.bot = bot
        # Get bot ID from environment, default to 0 if not found
        wordle_bot_id_str = os.getenv("WORDLE_BOT_ID")
        if not wordle_bot_id_str:
            logging.warning("WORDLE_BOT_ID not found in environment variables")
            self.wordle_bot_id = 0
        else:
            try:
                self.wordle_bot_id = int(wordle_bot_id_str)
            except ValueError:
                logging.error(f"Invalid WORDLE_BOT_ID: {wordle_bot_id_str}")
                self.wordle_bot_id = 0

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Listen for messages from the Wordle bot and parse scores.
        
        Args:
            message: The Discord message object to process.
        """    
        if message.author == self.bot.user:
            return

        if message.author.id == self.wordle_bot_id and "day streak" in message.content and "Here are yesterday's results:" in message.content:   
            logging.info("Wordle report detected.")
            await self.parse_wordle_results(message)
        elif "day streak" in message.content and "Here are yesterday's results:" in message.content:
            # Testing purpose: simulate Wordle bot messages
            logging.info("Simulated Wordle report detected.")
            await self.parse_wordle_results(message)

    async def parse_wordle_results(self, message: discord.Message) -> None:
        """
        Parse Wordle bot results and extract scores
        
        Args:
            message: The Discord message object containing Wordle results.
        """
 

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
                            # Convert user ID to integer
                            member_id = int(user_id)
                            
                            # Get the user object
                            user = message.guild.get_member(member_id)
                            username = user.display_name if user else f"Unknown_{user_id}"
                            
                            # TODO: Add actual database saving function here
                            # save_wordle_score(user_id, username, score, str(message.guild.id))
                            logging.info(f"Would save: {username} ({user_id}) = {score} points")
                            total_saved += 1
                            
                        except ValueError:
                            logging.warning(f"Invalid user ID format: {user_id}")
                        except Exception as e:
                            logging.error(f"Unexpected error processing user {user_id}: {e}")
        
        if total_saved > 0:
            await message.channel.send(f"I've recorded the results for {total_saved} participants. Better not have cheated.")
        else:
            await message.channel.send("I couldn't find any scores to record this time. Perhaps everyone is still working on their puzzles.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WordleParser(bot))
    logging.info("WordleParserCog has been added to bot.")