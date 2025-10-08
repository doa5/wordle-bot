import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime
import logging

class OguriCapCog(commands.Cog):
    """Fun commands based on Oguri Cap's personality - calm and hungry"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Oguri Cap GIF collection - Real GIF URLs from Tenor!
        self.gifs = {
            'eating': [
                'https://c.tenor.com/m5ImGvJ9W_UAAAAC/tenor.gif',  # Oguri Cap eating with help by Bijin
                'https://c.tenor.com/XfS0xnrKmIYAAAAd/tenor.gif',  # Oguri eating croquette
                'https://c.tenor.com/MkRliGFdw80AAAAd/tenor.gif',  # Eating with Opera O
                'https://c.tenor.com/3iVg3SDxgHUAAAAd/tenor.gif',  # Oguri Cap enjoying a donut
                'https://media.tenor.com/2whuMhugjvoAAAAi/umamusumeprettyderby.gif',  # Oguri Cap waving meat
                'https://c.tenor.com/Y4y4Pc5OaJUAAAAC/tenor.gif',  # Oguri Cap eating ice cream
                'https://c.tenor.com/AMtA6XvnPHoAAAAd/tenor.gif',  # Oguri Cap eating biscuits
                'https://c.tenor.com/3uMulYc14dYAAAAd/tenor.gif',  # Oguri Cap eating like a hamster
                'https://c.tenor.com/mDKuP2oJ8KIAAAAC/tenor.gif',  # Oguri Cap eating soba
                'https://c.tenor.com/0HVg47Q6vmcAAAAC/tenor.gif'  # Oguri Cap eating more ice cream
            ],
            'victory': [
                'https://c.tenor.com/yvjzZ4Sfl_AAAAAd/tenor.gif',   # Oguri Cap blue aura
                'https://c.tenor.com/Gbp-6yjg8cEAAAAd/tenor.gif',  # Late start burst
                'https://c.tenor.com/-nUpMuuwamYAAAAd/tenor.gif'  # Late surger
            ]
        }
    
    def get_random_gif(self, category: str) -> str:
        """Get a random GIF from the specified category"""
        if category in self.gifs and self.gifs[category]:
            return random.choice(self.gifs[category])
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "food" in message.content.lower():
            await message.channel.send('Did someone say food?')

    @commands.command()
    async def snack(self, ctx: commands.Context) -> None:
        """Watch Oguri Cap devour some delicious food"""
        
        # Get eating GIF
        gif_url = self.get_random_gif("eating")
        satisfaction = ["Eating well is part of the race too.", 
                        "I can't go all-out on an empty stomach.",
                        "I run. I earned this.",
                        "Don’t worry. It’s fuel, not indulgence.",
                        "Calories are strategy.",
                        "Rest, eat, repeat. That’s the cycle.",
                        "Running fast means eating smart.",
                        "Food’s part of training. Always has been.",
                        "This isn’t greed. It’s preparation.",
                        "Speed alone doesn’t fill you up.",
                        "Everything tastes better after a race.",
                        "You can’t sprint on an empty stomach.",
                        "I’ll stop when I’m full. Probably.",
                        "That’s one more step toward victory.",
                        "Good food, good race.",
                        "Even focus needs fuel.",
                        "It’s not a weakness. It’s discipline.",
                        "I could run another lap... after this bite.",
                        "Don’t look at me like that. It’s necessary."
                       ]
        
        embed = discord.Embed(
            title="Snack time",
            description=random.choice(satisfaction),
            color=0x4d79ff
        )
        if gif_url:
            embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
        logging.info(f"Snack time initiated by {ctx.author}")

    @commands.command()
    @commands.is_owner()
    async def say(self, ctx: commands.Context, *, message: str) -> None:
        """Makes Oguri Cap deliver your message to general.
        
        Args:
            message: The message text to send.
        
        Usage:
            woguri say This is a text-only message
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass 
        
        # Find the general channel
        general_channel = discord.utils.get(ctx.guild.channels, name="general")
        if general_channel:
            await general_channel.send(message)
            logging.info(f"Announcement sent to #general by {ctx.author}")
        else:
            await ctx.send(message)  # Fallback to current channel
            logging.warning("❌ No #general channel found. Message not sent.")

    @commands.command(name="announce")
    @commands.is_owner()
    async def announce(self, ctx: commands.Context, *, message: str) -> None:
        """Official Oguri Cap announcement (text only). Announcements go to #general channel.

        Args:
            message: The announcement text to send.
        
        Usage:
            woguri announce This is a text-only announcement
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title="📢 Official Announcement",
            description=message,
            color=0x4d79ff
        )
        embed.set_footer(text="- Oguri Cap, Mile Championship (1989)")

        general_channel = discord.utils.get(ctx.guild.channels, name="general")
        if general_channel:
            await general_channel.send(embed=embed)
            logging.info(f"Announcement sent to #general by {ctx.author}")
        else:
            await ctx.send(embed=embed)  # Fallback to current channel
            logging.warning("❌ No #general channel found. Message not sent.")

    @commands.command(name="announcewithgif")
    @commands.is_owner()
    async def announce_with_gif(self, ctx: commands.Context, gif_url: str, *, message: str) -> None:
        """Official Oguri Cap announcement with GIF.
        
        Args:
            gif_url: URL of the GIF to include in the announcement.
            message: The announcement text to send.
        Usage:
            woguri announcewithgif https://gif-url.com/gif.gif Your message here
        """
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title="📢 Official Announcement",
            description=message,
            color=0x4d79ff
        )
        embed.set_footer(text="- Oguri Cap, Mile Championship (1989)")
        
        embed.set_image(url=gif_url)

        general_channel = discord.utils.get(ctx.guild.channels, name="general")
        if general_channel:
            await general_channel.send(embed=embed)
            logging.info(f"Announcement sent to #general by {ctx.author}")
        else:
            await ctx.send(embed=embed)  # Fallback to current channel
            logging.warning("❌ No #general channel found. Message not sent.")

    @commands.command()
    async def celebrate_victory(self, ctx: commands.Context) -> None:
        """Celebrate a victory with Oguri Cap"""

        oguri_cap_gif = self.get_random_gif("victory")
        embed = discord.Embed(
            title="A fine victory for Mr. Tricks",
            description="AND THE GOAT WINS AGAIN 🎉",
            color=0x4d79ff
        )
        if oguri_cap_gif:
            embed.set_image(url=oguri_cap_gif)

        await ctx.send(embed=embed)
  
async def setup(bot):
    """Setup function to add OguriCapCog to the bot"""
    await bot.add_cog(OguriCapCog(bot))
    logging.info("OguriCapCog has been added to bot.")