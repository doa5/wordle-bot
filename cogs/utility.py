import discord
from discord.ext import commands
import logging
import asyncio

class UtilityCog(commands.Cog):
    """General utility and admin commands for bot management"""
    
    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the UtilityCog with bot instance."""
        self.bot = bot

    @commands.command(aliases=["allcommands", "commands", "cmds"])
    async def show_all_commands(self, ctx: commands.Context) -> None:
        """List all commands available across all cogs"""
        all_commands = {}
        
        # Get commands from all cogs
        for cog_name, cog in self.bot.cogs.items():
            cog_commands = [command.name for command in cog.get_commands()]
            if cog_commands:
                all_commands[cog_name] = cog_commands
        
        # Format the output
        if not all_commands:
            await ctx.send("No commands found. Something is very wrong.")
            return
        
        embed = discord.Embed(
            title="All Available Commands",
            description="Complete command list across all systems",
            color=0x4d79ff
        )
        
        for cog_name, commands_list in all_commands.items():
            embed.add_field(
                name=f"{cog_name}",
                value=", ".join(commands_list),
                inline=False
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
        
        # Get the DatabaseCog to handle logging
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.message.add_reaction("❌")
            await ctx.send("Database system unavailable. Cannot enable logging.")
            return
        
        database_cog.log_channel_id = channel.id
        
        root_logger = logging.getLogger()
        if database_cog.discord_handler not in root_logger.handlers:
            root_logger.addHandler(database_cog.discord_handler)
        
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
        # Get the DatabaseCog to handle logging
        database_cog = self.bot.get_cog('DatabaseCog')
        if not database_cog:
            await ctx.message.add_reaction("❌")
            await ctx.send("Database system unavailable. Cannot disable logging.")
            return
        
        root_logger = logging.getLogger()
        try:
            root_logger.removeHandler(database_cog.discord_handler)
        except ValueError:
            pass  
        
        database_cog.log_channel_id = None
        await ctx.message.add_reaction("❌")
        await ctx.send("Terminal log capture disabled. Why would you turn off something so useful?")
        logging.info("Terminal logging to Discord disabled")

async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(UtilityCog(bot))
    logging.info("UtilityCog has been added to bot.")