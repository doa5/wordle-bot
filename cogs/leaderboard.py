from discord.ext import commands
import logging
from datetime import datetime, time, timedelta

class LeaderboardCog(commands.Cog):
    """
    Cog to manage the leaderboard related commands.
    """
    def __init__(self, bot) -> None:
        self.bot = bot

    def is_leaderboard_available(self) -> bool:
        """
        Check if leaderboard is available (Sunday 5 PM to Sunday 11:59 PM only).
        
        Returns:
            bool: True if current time is within Sunday 17:00 to Sunday 23:59
        """
        now = datetime.now()
        
        # Check if it's Sunday (weekday 6)
        if now.weekday() != 6:
            return False
        
        # Check if time is between 5 PM (17:00) and 11:59 PM (23:59)
        current_time = now.time()
        start_time = time(17, 0)   # 5 PM
        end_time = time(23, 59, 59)  # 11:59:59 PM
        
        return start_time <= current_time <= end_time
    
    def _get_next_sunday_5pm(self) -> datetime:
        """Calculate when the leaderboard will next be available.
        
        Returns:
            datetime: The next Sunday at 5 PM datetime object.
        """
        now = datetime.now()
        
        # Calculate days until next Sunday
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.time() > time(23, 59, 59):
            days_until_sunday = 7
        elif days_until_sunday == 0 and now.time() < time(17, 0):
            days_until_sunday = 0
        
        next_sunday = now + timedelta(days=days_until_sunday)
        return next_sunday.replace(hour=17, minute=0, second=0, microsecond=0)

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context) -> None:
        """
        Show weekly Wordle leaderboard (only available Sunday 5 PM - 11:59 PM).
        
        Args:
            ctx: The command context.
        
        Example:
            woguri leaderboard

        """
        if not self.is_leaderboard_available():
            next_sunday = self._get_next_sunday_5pm()
            await ctx.send(f"The weekly leaderboard is only available on Sundays from 5 PM to midnight. Next available: {next_sunday.strftime('%A, %B %d at %I:%M %p')}")
            return
    
        await self.produce_leaderboard(ctx)

    async def produce_leaderboard(self, ctx: commands.Context) -> None:
        """Produce the leaderboard for the current week.

        Args:
            ctx (commands.Context): The command context.
        """
        today = datetime.now()
        days_since_monday = today.weekday()  # 0=Monday, 6=Sunday
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # Get database cog for non-blocking operations
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.send("Database unavailable.")
            return
            
        query = '''
            SELECT username, SUM(score) as total_score, COUNT(*) as games_played
            FROM wordle_scores 
            WHERE date BETWEEN ? AND ?
            GROUP BY user_id, username
            ORDER BY total_score ASC
            LIMIT 10
        '''
        params = (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        results = database_cog.execute_query(query, params)
        logging.info(f"Top scores queried for guild {ctx.guild.id}")
        
        if not results:
            await ctx.send("No scores recorded this week.")
            logging.info(f"No scores found for guild {ctx.guild.id} this week.")
            return
        
        # Format leaderboard
        leaderboard = "**Weekly Wordle Leaderboard**\n"
        leaderboard += f"*Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d')}*\n\n"

        for i, (username, total_score, games) in enumerate(results, 1):
            if i == 1:
                leaderboard += f"👑 **{username}**: {total_score} points\n"
            elif i == 2:
                leaderboard += f"🥈 **{username}**: {total_score} points\n"
            elif i == 3:
                leaderboard += f"🥉 **{username}**: {total_score} points\n"
            else:
                leaderboard += f"{i}. **{username}**: {total_score} points\n"

        await ctx.send(leaderboard)
        logging.info(f"Weekly leaderboard sent for guild {ctx.guild.id}")

    @commands.command(aliases=["lbstatus", "lbwhen", "status"])
    @commands.is_owner() 
    async def leaderboard_status(self, ctx: commands.Context) -> None:
        """Report the current status of leaderboard access.

        Args:
            ctx (commands.Context): The command context.
        """
        now = datetime.now().replace(microsecond=0)  # ← Clean time
        available = self.is_leaderboard_available()
        next_time = self._get_next_sunday_5pm()

        await ctx.send(f"Status report: {now}\nLeaderboard access: {available}\nNext: {next_time}")

    @commands.command()
    @commands.is_owner() 
    async def reset_leaderboard(self, ctx: commands.Context) -> None:
        """
        Reset the leaderboard by clearing all scores from the database.
        
        Args:
            ctx: The command context.
        
        Example:
            woguri reset_leaderboard
        """
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.send("Database unavailable.")
            return
            
        # Use DatabaseCog for non-blocking delete
        query = 'DELETE FROM wordle_scores'
        results = database_cog.execute_query(query, ())
        deleted_rows = len(results) if results else 0

        await ctx.send(f"Archives cleared. {deleted_rows} entries processed.")
        logging.info(f"Leaderboard reset for guild {ctx.guild.id}, {deleted_rows} entries deleted.")

    @commands.command(aliases=["showleaderboard", "showlb"])
    @commands.is_owner()    
    async def show_leaderboard(self, ctx: commands.Context) -> None:
        """
        Show the entire leaderboard from the database (for debugging).
        
        Args:
            ctx: The command context.

        """
        await self.produce_leaderboard(ctx)

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(LeaderboardCog(bot))
    logging.info("LeaderboardCog has been added to bot.")
