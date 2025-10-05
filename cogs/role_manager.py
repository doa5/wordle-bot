import discord
from discord.ext import commands, tasks
import logging
from datetime import time

class RoleCog(commands.Cog):
    """
    Manages user roles for Wordle completion tracking.
    
    This cog handles assigning and removing the 'done' role to track
    which users have completed their daily Wordle puzzle so they can
    avoid spoilers. 
    """
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the RoleCog with bot instance and role configuration."""
        self.bot = bot
        self.role_name = "done"

    @commands.command(aliases=["done"])
    async def give_done_role(self, ctx: commands.Context) -> None:
        """
        Assign the 'done' role to indicate Wordle completion.
        
        Gives the user the 'done' role to show they've finished today's Wordle, in order to access the wordle channel without spoilers.
        
        Args:
            ctx: The command context containing message and author info.
            
        Example:
            woguri done
        """
        role = discord.utils.get(ctx.guild.roles, name=self.role_name)
        if role:
            await ctx.author.add_roles(role)
            await ctx.message.add_reaction("🏇")
            await ctx.send(f"{ctx.author.mention}, well done. Access granted.")
            logging.info(f"Assigned 'done' role to {ctx.author}")
            
        else:
            await ctx.send(f"I'm afraid I can't find the '{self.role_name}' role. Perhaps it needs to be created first?")
            await ctx.message.add_reaction("❌")
            logging.warning(f"Role '{self.role_name}' not found in guild {ctx.guild.name}")

    async def _remove_done_roles(self, guild: discord.Guild, notify_channel: discord.TextChannel = None) -> int:
        """
        Helper method to remove 'done' roles from all members.
        
        Args:
            guild: The Discord server to process
            notify_channel: Optional channel to send completion message
            
        Returns:
            Number of roles removed
        """
        role = discord.utils.get(guild.roles, name=self.role_name)
        if not role:
            logging.warning(f"Role '{self.role_name}' not found in {guild.name}")
            return 0
        
        removed_count = 0
        for member in guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    removed_count += 1
                    logging.info(f"Removed 'done' role from {member.name}")
                    
                except Exception as e:
                    logging.error(f"Error removing role from {member.name}: {e}")
        
        # Optional notification
        if notify_channel and removed_count == 1:
            await notify_channel.send(f"Good morning, everyone. I've reset the roles for {removed_count} member. Good luck with today's puzzle.")
        elif notify_channel and removed_count > 1:
            await notify_channel.send(f"Good morning, everyone. I've reset the roles for {removed_count} members. Good luck with today's puzzle.")
        return removed_count

    @commands.command(aliases=["reset"])
    @commands.is_owner()
    async def reset_done_roles(self, ctx: commands.Context) -> None:
        """
        Remove the 'done' role from all server members.
     
        Args:
            ctx: The command context containing message and server info.
            
        Example:
            woguri reset
            
        Note:
            Requires appropriate permissions to manage roles.
        """
        removed = await self._remove_done_roles(ctx.guild, ctx.channel)
        if removed == 0:
            await ctx.send(f"There's nothing to reset at the moment. Everyone must still be working on their puzzles.")
            await ctx.message.add_reaction("❌")
        else:
            await ctx.message.add_reaction("✅")

    @tasks.loop(time=time(0, 0))
    async def daily_reset_task(self) -> None:
        """
        Automatically reset 'done' roles at midnight
        
        Args:
            None - runs automatically at midnight daily
        
        Note:
            Requires appropriate permissions to manage roles.
        """
        total_removed = 0
        for guild in self.bot.guilds:
            # Find a general channel for notification (optional)
            notify_channel = discord.utils.get(guild.channels, name="general")
            removed = await self._remove_done_roles(guild, notify_channel)
            total_removed += removed

        logging.info(f"Daily reset completed! Removed roles from {total_removed} users.")

    @commands.command()
    @commands.is_owner()
    async def test_daily_reset(self, ctx) -> None:
        """Test the midnight reset functionality."""
        await self.daily_reset_task()  

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the RoleCog to the bot."""
    await bot.add_cog(RoleCog(bot))
    logging.info("RoleCog has been added to the bot.")
