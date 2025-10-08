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
                'https://media.tenor.com/2whuMhugjvoAAAAj/umamusumeprettyderby.gif',  # Oguri Cap waving meat
                'https://c.tenor.com/XfS0xnrKmIYAAAAd/tenor.gif',  # Oguri eating croquette
                'https://c.tenor.com/MkRliGFdw80AAAAd/tenor.gif',  # Eating with Opera O
                'https://c.tenor.com/3iVg3SDxgHUAAAAd/tenor.gif'  # Oguri Cap enjoying a donut
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
    async def snack(self, ctx):
        """Watch Oguri Cap devour some delicious food"""
        
        # Get eating GIF
        gif_url = self.get_random_gif("eating")
        satisfaction = ["Eating well is part of the race too.", 
                        "I can't go all-out on an empty stomach.",
                        "I run. I earned this."]
        
        embed = discord.Embed(
            title="Snack time",
            description=random.choice(satisfaction),
            color=0x4d79ff
        )
        if gif_url:
            embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
        await asyncio.sleep(3)

    async def celebrate_victory(self, ctx):
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

    @commands.command(aliases=["allcommands", "commands", "cmds"])
    async def show_all_commands(self, ctx):
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
  
async def setup(bot):
    """Setup function to add OguriCapCog to the bot"""
    await bot.add_cog(OguriCapCog(bot))
    logging.info("OguriCapCog has been added to bot.")