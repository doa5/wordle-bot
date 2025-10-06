import discord
from discord.ext import commands
import logging
import sqlite3

class DatabaseCog(commands.Cog):
    """
    Cog to manage database connections and operations.
    """
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the DatabaseCog with bot instance."""
        self.bot = bot
        self.database_path = 'wordle_scores.db'
        self.connection = None
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

    @commands.Cog.listener()
    async def on_cog_unload(self) -> None:
        """Ensure the database connection is closed when the cog is unloaded."""
        self.close_connection()

    @commands.command(aliases=["dbstats"])
    @commands.is_owner()
    async def db_stats(self, ctx: commands.Context) -> None:
        """Show database statistics.

        Args:
            ctx: The command context.
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
    async def db_guilds(self, ctx):
        """List all servers using the bot."""
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

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(DatabaseCog(bot))
    logging.info("DatabaseCog has been added to bot.")