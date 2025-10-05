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
    
    # Regex patterns for Wordle score parsing
    WORDLE_SCORE_PATTERN = r'\d+/6:|X/6:'
    SCORE_MATCH_PATTERN = r'^(\d|X)/6:?$'
    USER_MENTION_PATTERN = r'^<@!?(\d+)>$'
    PARSE_SCORE_PATTERN = r'(\d|X)/6:'
    PARSE_USER_PATTERN = r'<@!?(\d+)>'
    
    # Message detection patterns
    STREAK_TEXT = "day streak"
    RESULTS_TEXT = "Here are yesterday's results:"
    
    # Valid Wordle score values (1-6 attempts, 8 for failed/X)
    VALID_SCORES = [1, 2, 3, 4, 5, 6, 8]
    
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
        
        # Track messages being processed manually to avoid double processing
        self.processing_manual = set()

    def mark_message_as_manual(self, message_id: int) -> None:
        """Mark a message as being processed manually to prevent auto-processing."""
        self.processing_manual.add(message_id)
        logging.info(f"Message {message_id} marked for manual processing")
    
    def unmark_message_as_manual(self, message_id: int) -> None:
        """Remove manual processing flag from a message."""
        self.processing_manual.discard(message_id)
        logging.info(f"Message {message_id} unmarked from manual processing")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Listen for messages from the Wordle bot and parse scores.
        
        Args:
            message: The Discord message object to process.
        """    
        if message.author == self.bot.user:
            return
        
        # Skip processing if this is a bot command
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            logging.info("Skipping automatic processing - this is a bot command")
            return
        
        # Skip processing if this message is being handled manually
        if message.id in self.processing_manual:
            logging.info(f"Skipping automatic processing for message {message.id} - being handled manually")
            return

        if message.author.id == self.wordle_bot_id and self.STREAK_TEXT in message.content and self.RESULTS_TEXT in message.content:   
            logging.info("Wordle report detected.")
            await self.parse_wordle_results(message)
        elif self.STREAK_TEXT in message.content and self.RESULTS_TEXT in message.content:
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
                score_match = re.search(self.PARSE_SCORE_PATTERN, line)
                if score_match:
                    score_str = score_match.group(1)
                    # Convert X to 8 points, numbers stay as numbers
                    score = 8 if score_str == 'X' else int(score_str)
                    
                    # Extract mentioned users (@ mentions)
                    user_mentions = re.findall(self.PARSE_USER_PATTERN, line)
                    
                    for user_id in user_mentions:
                        try:
                            member_id = int(user_id)
                    
                            user = message.guild.get_member(member_id)
                            username = user.display_name if user else f"Unknown_{user_id}"
                            
                            # Get database cog and save score
                            database_cog = self.bot.get_cog('DatabaseCog')
                            if database_cog:
                                today = datetime.now().strftime('%Y-%m-%d')
                            
                                if database_cog.has_duplicate_submission(user_id, message.guild.id, today):
                                    logging.info(f"Duplicate submission ignored: {username} already recorded for {today}")
                                    await message.add_reaction("❌")
                                    continue
                                
                                success = database_cog.save_wordle_score(user_id, message.guild.id, username, score, today)
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


    async def validate_date(self, date: str, ctx: commands.Context) -> bool:
        """Validate date string is in YYYY-MM-DD format."""
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return True
        except ValueError:
            await ctx.message.add_reaction("❌")
            await ctx.send("Your date format is... inadequate. Use YYYY-MM-DD format. Precision matters.")
            return False

    @commands.command(aliases=["add_score", "manual_score"])
    @commands.is_owner()
    async def add_manual_score(self, ctx: commands.Context, date: str, *, score_data: str) -> None:
        """
        Manually add Wordle scores for users on a specific date.
        
        Supports multiple formats:
        - Single score for yourself: "3/6" or "3"
        - Score with user mention: "3/6 @user" or "@user 3/6"
        - Multiple users: "3/6 @user1 @user2" or "3/6: @user1 @user2"
        - Wordle bot format: "3/6: @user1 @user2 4/6: @user3"
        
        Args:
            ctx: The command context.
            date: Date in YYYY-MM-DD format (e.g., 2024-10-01).
            score_data: Score and user data in various formats.
        
        Example:
            woguri add_score 2024-10-01 3/6
            woguri add_score 2024-10-01 3/6 @doa
            woguri add_score 2024-10-01 "3/6: @doa @user2 4/6: @user3"
        """
        logging.info(f"Manual score addition requested by {ctx.author} for date {date} with data: {score_data}")
        
        valid_date = await self.validate_date(date, ctx)
        if not valid_date:
            return
        
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.message.add_reaction("❌")
            await ctx.send("The database is currently unavailable. Even champions need proper record-keeping systems.")
            logging.error("DatabaseCog not found!")
            return
        
        saved_count = 0
        errors = []
        
        # Parse Wordle bot format (multiple scores with users)
        if re.search(self.WORDLE_SCORE_PATTERN, score_data):
            lines = score_data.split()
            current_score = None
            
            for token in lines:
                score_match = re.match(self.SCORE_MATCH_PATTERN, token.upper())
                if score_match:
                    current_score = score_match.group(1)
                    continue
                
                user_match = re.match(self.USER_MENTION_PATTERN, token)
                if user_match and current_score:
                    user_id = int(user_match.group(1))
                    score_value = 8 if current_score == 'X' else int(current_score)
                    
                    user = ctx.guild.get_member(user_id)
                    username = user.display_name if user else f"Unknown_{user_id}"
                    
                    if database_cog.has_duplicate_submission(user_id, ctx.guild.id, date):
                        errors.append(f"{username} already has a score for {date}")
                        continue
                    
                    success = database_cog.save_wordle_score(user_id, ctx.guild.id, username, score_value, date)
                    if success:
                        saved_count += 1
                        logging.info(f"Manual score added: {username} ({user_id}) = {score_value} points on {date}")
                    else:
                        errors.append(f"Failed to save score for {username}")
        
        else:
            # Handle simple formats
            # Extract all user mentions
            user_mentions = re.findall(r'<@!?(\d+)>', score_data)
            
            score_match = re.search(r'(\d|X)(/6)?', score_data.upper())
            if not score_match:
                await ctx.message.add_reaction("❌")
                await ctx.send("That score format makes no sense. I expect clear, precise reporting. Use 3/6, X/6, 3, or X.")
                return
            
            score_str = score_match.group(1)
            score_value = 8 if score_str == 'X' else int(score_str)
            
            if score_value not in self.VALID_SCORES:
                await ctx.message.add_reaction("❌")
                await ctx.send("Those numbers are outside acceptable parameters. Scores must be 1-6 or X for complete failure.")
                return
            
            if not user_mentions:
                user_mentions = [str(ctx.author.id)]
                logging.info("No user mentions found, defaulting to command author")
            
            for user_id_str in user_mentions:
                user_id = int(user_id_str)
                user = ctx.guild.get_member(user_id)
                username = user.display_name if user else f"Unknown_{user_id}"
                
                if database_cog.has_duplicate_submission(user_id, ctx.guild.id, date):
                    errors.append(f"{username} already has a score for {date}")
                    logging.info(f"Duplicate score submission detected for {username} on {date}")
                    continue
                
                success = database_cog.save_wordle_score(user_id, ctx.guild.id, username, score_value, date)
                if success:
                    saved_count += 1
                    logging.info(f"Manual score added: {username} ({user_id}) = {score_value} points on {date}")
                else:
                    errors.append(f"Failed to save score for {username}")
        
        if saved_count == 1:
            await ctx.message.add_reaction("✅")
            await ctx.send(f"Score has been properly documented.\nDate: {date}\nEntries processed: {saved_count}\nMaintaining accurate records is essential.")
        elif saved_count > 1:
            await ctx.message.add_reaction("✅")
            await ctx.send(f"Multiple scores have been recorded.\nDate: {date}\nEntries processed: {saved_count}\nEfficiency noted.")

        if errors:
            error_msg = "\n".join([f"❌ {error}" for error in errors[:5]])  # Limit to 5 errors
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            await ctx.send(error_msg)

    @commands.command(aliases=["overwrite_score", "replace_score"])
    @commands.is_owner()
    async def overwrite_manual_score(self, ctx: commands.Context, date: str, *, score_data: str) -> None:
        """
        Overwrite existing Wordle scores for users on a specific date.
        
        Supports multiple formats:
        - Single score for yourself: "3/6" or "3"
        - Score with user mention: "3/6 @user" or "@user 3/6"
        - Multiple users: "3/6 @user1 @user2" or "3/6: @user1 @user2"
        - Wordle bot format: "3/6: @user1 @user2 4/6: @user3"
        
        Args:
            ctx: The command context.
            date: Date in YYYY-MM-DD format (e.g., 2024-10-01).
            score_data: Score and user data in various formats.
        
        Example:
            woguri overwrite_score 2024-10-01 3/6
            woguri overwrite_score 2024-10-01 3/6 @doa
            woguri replace_score 2024-10-01 "3/6: @doa @user2 4/6: @user3"
        """
        logging.info(f"Manual score overwrite requested by {ctx.author} for date {date} with data: {score_data}")
        
        valid_date = await self.validate_date(date, ctx)
        if not valid_date:
            return
        
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.message.add_reaction("❌")
            await ctx.send("Database systems are offline. Even the best strategies require functional infrastructure.")
            logging.error("DatabaseCog not found!")
            return
        
        saved_count = 0
        errors = []
        
        # Parse Wordle bot format (multiple scores with users)
        if re.search(self.WORDLE_SCORE_PATTERN, score_data):
            lines = score_data.split()
            current_score = None
            
            for token in lines:
                score_match = re.match(self.SCORE_MATCH_PATTERN, token.upper())
                if score_match:
                    current_score = score_match.group(1)
                    continue
                
                user_match = re.match(self.USER_MENTION_PATTERN, token)
                if user_match and current_score:
                    user_id = int(user_match.group(1))
                    score_value = 8 if current_score == 'X' else int(current_score)
                    
                    user = ctx.guild.get_member(user_id)
                    username = user.display_name if user else f"Unknown_{user_id}"
                    
                    # For overwrite, we don't check for duplicates - we force overwrite
                    success = database_cog.save_wordle_score(user_id, ctx.guild.id, username, score_value, date)
                    if success:
                        saved_count += 1
                        logging.info(f"Manual score overwritten: {username} ({user_id}) = {score_value} points on {date}")
                    else:
                        errors.append(f"Failed to save score for {username}")
        
        else:
            # Handle simple formats
            # Extract all user mentions
            user_mentions = re.findall(r'<@!?(\d+)>', score_data)
            
            score_match = re.search(r'(\d|X)(/6)?', score_data.upper())
            if not score_match:
                await ctx.message.add_reaction("❌")
                await ctx.send("That score format makes no sense. I expect clear, precise reporting. Use 3/6, X/6, 3, or X.")
                return
            
            score_str = score_match.group(1)
            score_value = 8 if score_str == 'X' else int(score_str)
            
            if score_value not in self.VALID_SCORES:
                await ctx.message.add_reaction("❌")
                await ctx.send("Those numbers are outside acceptable parameters. Scores must be 1-6 or X for complete failure.")
                return
            
            if not user_mentions:
                user_mentions = [str(ctx.author.id)]
                logging.info("No user mentions found, defaulting to command author")
            
            for user_id_str in user_mentions:
                user_id = int(user_id_str)
                user = ctx.guild.get_member(user_id)
                username = user.display_name if user else f"Unknown_{user_id}"
                
                # For overwrite, we don't check for duplicates - we force overwrite
                success = database_cog.save_wordle_score(user_id, ctx.guild.id, username, score_value, date)
                if success:
                    saved_count += 1
                    logging.info(f"Manual score overwritten: {username} ({user_id}) = {score_value} points on {date}")
                else:
                    errors.append(f"Failed to save score for {username}")
        
        if saved_count == 1:
            await ctx.message.add_reaction("✅")
            await ctx.send(f"Previous record has been corrected and updated.\nDate: {date}\nEntries modified: {saved_count}\nAccuracy is paramount.")
        elif saved_count > 1:
            await ctx.message.add_reaction("✅")
            await ctx.send(f"Multiple records have been corrected.\nDate: {date}\nEntries modified: {saved_count}\nPrecision maintained.")

        if errors:
            error_msg = "\n".join([f"❌ {error}" for error in errors[:5]])  # Limit to 5 errors
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors) - 5} more errors"
            await ctx.send(error_msg)



async def setup(bot: commands.Bot) -> None:
    """Setup the WordleParser cog."""
    await bot.add_cog(WordleParser(bot))
    logging.info("WordleParserCog has been added to bot.")