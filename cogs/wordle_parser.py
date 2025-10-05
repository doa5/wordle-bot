import discord
from discord.ext import commands
import logging
import re
import os
from datetime import datetime

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
                    
                    for user_id in user_mentions:
                        try:
                            member_id = int(user_id)
                    
                            user = message.guild.get_member(member_id)
                            username = user.display_name if user else f"Unknown_{user_id}"
                            
                            # Get database cog and save score
                            database_cog = self.bot.get_cog('DatabaseCog')
                            if database_cog:
                                today = datetime.now().strftime('%Y-%m-%d')
                            
                                if database_cog.has_duplicate_submission(user_id, today):
                                    logging.info(f"Duplicate submission ignored: {username} already recorded for {today}")
                                    await message.add_reaction("❌")
                                    continue
                                
                                success = database_cog.save_wordle_score(user_id, username, score, today)
                                if success:
                                    logging.info(f"Saved: {username} ({user_id}) = {score} points")
                                    total_saved += 1
                                else:
                                    logging.error(f"Failed to save score for {username}")
                            else:
                                logging.error("DatabaseCog not found!")
                            
                        except ValueError:
                            logging.warning(f"Invalid user ID format: {user_id}")
                        except Exception as e:
                            logging.error(f"Unexpected error processing user {user_id}: {e}")
        
        if total_saved > 0:
            await message.channel.send(f"I've recorded the results for {total_saved} participants. Better not have cheated.")
            await message.add_reaction("✅")
        else:
            await message.channel.send("I found nothing worth recording. Either the report is broken, or you've all collectively failed me.")

async def setup(bot: commands.Bot) -> None:
    """Setup the WordleParser cog."""
    await bot.add_cog(WordleParser(bot))
    logging.info("WordleParserCog has been added to bot.")