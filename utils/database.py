import discord
from discord.ext import commands
import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta

class DiscordLogHandler(logging.Handler):
    """Custom logging handler that sends terminal logs to Discord"""
    
    def __init__(self, database_cog):
        super().__init__()
        self.database_cog = database_cog
        self.setLevel(logging.INFO)  # Capture INFO and above
        
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.setFormatter(formatter)
    
    def emit(self, record):
        """Called whenever a log message is generated"""
        try:
            log_message = self.format(record)
            
            # Add emoji based on log level
            if record.levelno >= logging.ERROR:
                emoji = "❌"
            elif record.levelno >= logging.WARNING:
                emoji = "⚠️"
            else:
                emoji = "ℹ️"
            
            formatted_message = f"{emoji} `{log_message}`"
            
            if self.database_cog.log_channel_id:
                try:
                    self.database_cog.log_queue.put_nowait(formatted_message)
                except asyncio.QueueFull:
                    pass
        except Exception:
            pass  

class DatabaseCog(commands.Cog):
    """
    Cog to manage database connections and operations.
    """
    MAXIMUM_LOG_QUEUE = 100
    LOG_PROCESSOR_TIMEOUT = 5.0  # seconds to wait for new log messages
    LOG_SEND_DELAY = 1.0         # seconds between Discord messages to avoid rate limits
    LOG_ERROR_RETRY_DELAY = 5.0  # seconds to wait after log processor errors
    
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the DatabaseCog with bot instance."""
        self.bot = bot
        self.database_path = 'wordle_scores.db'
        self.connection = None
        
        self.log_queue = asyncio.Queue(maxsize=self.MAXIMUM_LOG_QUEUE)
        self.log_channel_id = None
        self.discord_handler = DiscordLogHandler(self)
        self.log_processor_task = None
        
        # Start log processor (only if bot has a loop - not in tests)
        if hasattr(self.bot, 'loop') and hasattr(self.bot.loop, 'create_task'):
            self.log_processor_task = self.bot.loop.create_task(self.log_processor())
        
        self.connect_to_database()

    def connect_to_database(self) -> None:
        """Establish a connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.database_path)
            logging.info(f"Connected to database at {self.database_path}")
            self.create_tables()
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            self.connection = None

    def create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        if not self.connection:
            logging.error("No database connection.")
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wordle_scores (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    username TEXT,
                    score INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.connection.commit()
            logging.info("Database tables ensured.")
            
            
        except sqlite3.Error as e:
            logging.error(f"Error creating tables: {e}")
            self.connection = None
    

    def close_connection(self) -> None:
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed.")

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: The SQL query to execute.
            params: Optional parameters for the SQL query.
                   Common examples:
                   - Single value: (user_id,)
                   - Multiple values: (user_id, username, score, date)
                   - Date range: ("2024-01-01", "2024-01-31")
                   - User list: (123456, 789012, 345678)
        
        Returns:
            List of tuples containing the query results.
        """
        if not self.connection:
            logging.error("No database connection.")
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            self.connection.commit()
            logging.info(f"Executed query: {query} with params: {params}")
            return results
        except sqlite3.Error as e:
            logging.error(f"Database query error: {e}")
            return []

    def save_wordle_score(self, user_id: int, guild_id: int, username: str, score: int, date: str) -> bool:
        """
        Save a Wordle score to the database.

        Args:
            user_id: Discord user ID.
            guild_id: Discord server (guild) ID.
            username: Discord username.
            score: Number of attempts (1-6) or 8 for failure.
            date: Date when the report was processed (YYYY-MM-DD format).
                  * NOTE: Bot processes at 00:20, so this represents the day
                  * the report was received, not necessarily the puzzle date.

        Returns:
            True if the score was saved successfully, False otherwise.
        """
        if not self.connection:
            logging.error("No database connection.")
            return False
        query = """INSERT OR REPLACE INTO wordle_scores 
                   (user_id, guild_id, username, score, date) 
                   VALUES (?, ?, ?, ?, ?)"""
        params = (user_id, guild_id, username, score, date)
        logging.info(f"Saving score for user {username} ({user_id}) in guild {guild_id}: {score} on {date}")
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            logging.info("Score saved successfully.")
            return True
        except sqlite3.Error as e:
            logging.error(f"Error saving score: {e}")
            return False
    
    def has_duplicate_submission(self, user_id: int, guild_id: int, date: str) -> bool:
        """Check if a user has already submitted a score for a specific date in a guild.

        Args:
            user_id (int): The ID of the user.
            guild_id (int): The ID of the guild (server).
            date (str): The date to check (YYYY-MM-DD format).

        Returns:
            bool: True if a duplicate submission exists, False otherwise.
        """
        query = "SELECT id FROM wordle_scores WHERE user_id = ? AND guild_id = ? AND date = ?"
        params = (user_id, guild_id, date)
        logging.info(f"Checking for duplicate submission for user {user_id} in guild {guild_id} on {date}")
        result = self.execute_query(query, params)
        logging.info(f"Duplicate submission check result: {bool(result)}")
        return bool(result)

    async def log_processor(self) -> None:
        """Background task to process log messages and send them to Discord channel."""
        try:
            while not self.bot.is_closed():
                try:
                    message = await asyncio.wait_for(self.log_queue.get(), timeout=self.LOG_PROCESSOR_TIMEOUT)
                    
                    if self.log_channel_id:
                        channel = self.bot.get_channel(self.log_channel_id)
                        if channel:
                            await channel.send(message)
                    
                    await asyncio.sleep(self.LOG_SEND_DELAY)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    # Log processor errors shouldn't crash the bot
                    await asyncio.sleep(self.LOG_ERROR_RETRY_DELAY)
        except asyncio.CancelledError:
            pass

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start log processor when bot is ready."""
        if self.log_processor_task is None:
            self.log_processor_task = asyncio.create_task(self.log_processor())

    @commands.Cog.listener()
    async def on_cog_unload(self) -> None:
        """Cleanup when the cog is unloaded."""
        # Remove handler from root logger
        root_logger = logging.getLogger()
        if hasattr(self, 'discord_handler'):
            try:
                root_logger.removeHandler(self.discord_handler)
            except ValueError:
                pass  
        
        # Cancel log processor task
        if self.log_processor_task and hasattr(self.log_processor_task, 'done') and not self.log_processor_task.done():
            self.log_processor_task.cancel()
            
        self.close_connection()

    @commands.command(aliases=["dbstats"])
    @commands.is_owner()
    async def db_stats(self, ctx: commands.Context) -> None:
        """Show database statistics.

        Args:
            ctx: The command context.
        
        Example:
            woguri db_stats
        """
        logging.info("Gathering database statistics.")
        total_query = "SELECT COUNT(*) FROM wordle_scores"
        total_result = self.execute_query(total_query)
        total_count = total_result[0][0] if total_result else 0
        logging.info(f"Total records in database: {total_count}")
        
        guild_query = "SELECT COUNT(*) FROM wordle_scores WHERE guild_id = ?"
        guild_result = self.execute_query(guild_query, (ctx.guild.id,))
        guild_count = guild_result[0][0] if guild_result else 0
        logging.info(f"Records for guild {ctx.guild.id}: {guild_count}")
        
        servers_query = "SELECT COUNT(DISTINCT guild_id) FROM wordle_scores"
        servers_result = self.execute_query(servers_query)
        servers_count = servers_result[0][0] if servers_result else 0
        logging.info(f"Database stats - Total: {total_count}, This Guild: {guild_count}, Total Guilds: {servers_count}")
        
        embed = discord.Embed(title="Database Statistics", color=0x4d79ff)
        embed.add_field(name="Total Records", value=total_count, inline=True)
        embed.add_field(name="This Server", value=guild_count, inline=True)  
        embed.add_field(name="Total Servers", value=servers_count, inline=True)
        logging.info("Sending database statistics embed.")
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["dbguilds"])
    @commands.is_owner() 
    async def db_guilds(self, ctx: commands.Context) -> None:
        """List all servers using the bot.
        
        Args:
            ctx: The command context.

        Example:
            woguri db_guilds
        """
        query = """SELECT guild_id, COUNT(*) as records, 
                        MAX(date) as latest_date
                FROM wordle_scores 
                GROUP BY guild_id 
                ORDER BY records DESC"""
        
        results = self.execute_query(query)
        logging.info(f"Retrieved {len(results)} guilds from database.")
        
        if not results:
            await ctx.send("No data found in database.")
            logging.info("No data found in database.")
            return
        
        embed = discord.Embed(title="Database Servers", color=0x4d79ff)
        
        for guild_id, count, latest in results[:10]:  # Show top 10
            guild_name = f"Guild {guild_id}"
            try:
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    guild_name = guild.name
                    logging.info(f"Found guild name: {guild_name} for ID: {guild_id}")
            except Exception as e:
                logging.error(f"Error retrieving guild name for ID {guild_id}: {e}")

            embed.add_field(
                name=guild_name,
                value=f"Records: {count}\nLatest: {latest}",
                inline=True
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def enable_terminal_logs(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Enable capturing terminal logs to Discord
        Args:
            ctx: The command context.
            channel: Optional Discord text channel to send logs to. Defaults to current channel.
        
        Example:
            woguri enable_terminal_logs # uses current channel
            woguri enable_terminal_logs #general # uses #general channel
        """
        if channel is None:
            channel = ctx.channel
        
        self.log_channel_id = channel.id
        
        root_logger = logging.getLogger()
        if self.discord_handler not in root_logger.handlers:
            root_logger.addHandler(self.discord_handler)
        
        await ctx.message.add_reaction("✅")
        await ctx.send(f"Terminal logs now being sent to {channel.mention}, good job.")
        logging.info("Terminal logging to Discord enabled")

    @commands.command()
    @commands.is_owner()
    async def disable_terminal_logs(self, ctx: commands.Context) -> None:
        """Disable terminal log capture
        Args:
            ctx: The command context.

        Example:
            woguri disable_terminal_logs
        """
        root_logger = logging.getLogger()
        try:
            root_logger.removeHandler(self.discord_handler)
        except ValueError:
            pass  
        
        self.log_channel_id = None
        await ctx.message.add_reaction("❌")
        await ctx.send("Terminal log capture disabled. Why would you turn off something so useful?")
        logging.info("Terminal logging to Discord disabled")

    @commands.command(aliases=["recent", "query_scores"])
    @commands.is_owner()
    async def recent_scores(self, ctx: commands.Context, limit: int = 10, date: str = None, user: discord.Member = None) -> None:
        """Show database entries with flexible filtering
        
        Usage:
            woguri recent_scores                           # Last 10 entries
            woguri recent_scores 25                        # Last 25 entries  
            woguri recent_scores 10 2025-10-06            # 10 entries from specific date
            woguri recent_scores 10 2025-10-06 @user      # 10 entries from date for user
        """
        # Validate and cap the limit
        if limit > 50:
            limit = 50
            await ctx.add_reaction("⚠️")
            await ctx.send("Limit capped at 50 entries. You're being a bit greedy, don't you think?")
        
        try:
            cursor = self.connection.cursor()
            
            # Build query based on filters
            base_query = "SELECT username, score, date, guild_id, user_id FROM wordle_scores"
            conditions = []
            params = []
            
            # Add date filter if provided
            if date and date.lower() != "none":
                try:
                    # Validate date format
                    datetime.strptime(date, '%Y-%m-%d')
                    conditions.append("date = ?")
                    params.append(date)
                except ValueError:
                    await ctx.send("That’s not a valid date. Use YYYY-MM-DD, please. It’s not that hard.")
                    return
            
            # Add user filter if provided
            if user:
                conditions.append("user_id = ?")
                params.append(str(user.id))
            
            # Combine conditions
            if conditions:
                query = f"{base_query} WHERE {' AND '.join(conditions)}"
            else:
                query = base_query
            
            # Add ordering and limit
            query += " ORDER BY date DESC, username LIMIT ?"
            params.append(limit)
            
            logging.info(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                filter_parts = []
                if date and date.lower() != "none":
                    filter_parts.append(f"date {date}")
                if user:
                    filter_parts.append(f"user {user.display_name}")
                
                filter_text = f" matching {', '.join(filter_parts)}" if filter_parts else ""
                await ctx.send(f"No results found{filter_text}. Try again if you want.")
                return
            
            # Create formatted output
            output = "```\n"
            
            # Add header with filter info
            header_parts = [f"Showing {len(results)} entries"]
            if date and date.lower() != "none":
                header_parts.append(f"for {date}")
            if user:
                header_parts.append(f"for {user.display_name}")
            
            output += f"{' '.join(header_parts)}\n"
            output += "=" * 60 + "\n"
            output += f"{'Username':<15} {'Score':<5} {'Date':<12} {'Guild':<10}\n"
            output += "-" * 60 + "\n"
            
            for username, score, date_col, guild_id, user_id in results:
                username_display = username[:14] if username else "Unknown"
                guild_display = str(guild_id)[:8] if guild_id else "Unknown"
                
                output += f"{username_display:<15} {score:<5} {date_col:<12} {guild_display:<10}\n"
            
            output += "```"
            await ctx.send(output)
                
        except Exception as e:
            logging.error(f"Error in recent_scores command: {e}")
            await ctx.add_reaction("❌")
            await ctx.send("Something went wrong with your request. Probably your input.")

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(DatabaseCog(bot))
    logging.info("DatabaseCog has been added to bot.")
