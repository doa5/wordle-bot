import discord
from discord.ext import commands
import json
import os
from database import WordleDatabase
from parser import parse_wordle_score, is_wordle_message


class WordleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        
        super().__init__(command_prefix=self.get_prefix(), intents=intents)
        
        self.db = WordleDatabase()
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from config.json."""
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        else:
            print("Warning: config.json not found. Please create one from config.json.example")
            return {
                'token': '',
                'command_prefix': '!',
                'wordle_bot_id': None
            }
    
    def get_prefix(self):
        """Get the command prefix from config."""
        if hasattr(self, 'config'):
            return self.config.get('command_prefix', '!')
        return '!'

    async def on_ready(self):
        """Called when the bot is ready."""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')

    async def on_message(self, message):
        """Called when a message is received."""
        # Don't respond to ourselves
        if message.author == self.user:
            return
        
        # Check if message contains a Wordle score
        if is_wordle_message(message.content):
            result = parse_wordle_score(message.content)
            if result:
                wordle_number, score = result
                user_id = str(message.author.id)
                username = message.author.display_name
                
                # Try to add the score to the database
                success = self.db.add_score(user_id, username, wordle_number, score)
                
                if success:
                    score_text = "X" if score == 7 else str(score)
                    await message.add_reaction('✅')
                    print(f'Recorded Wordle {wordle_number} score {score_text}/6 for {username}')
                else:
                    # Score already exists
                    await message.add_reaction('⚠️')
                    print(f'Duplicate score for Wordle {wordle_number} from {username}')
        
        # Process commands
        await self.process_commands(message)


# Initialize bot
bot = WordleBot()


@bot.command(name='leaderboard', aliases=['lb', 'scores'])
async def leaderboard(ctx, timeframe: str = 'week'):
    """
    Display the Wordle leaderboard.
    
    Usage: !leaderboard [week|all]
    """
    if timeframe.lower() in ['week', 'weekly']:
        results = bot.db.get_weekly_leaderboard()
        title = '📊 Weekly Wordle Leaderboard'
    else:
        results = bot.db.get_all_time_leaderboard()
        title = '📊 All-Time Wordle Leaderboard'
    
    if not results:
        await ctx.send('No scores recorded yet!')
        return
    
    # Build the leaderboard message
    embed = discord.Embed(title=title, color=discord.Color.gold())
    
    description = ''
    for i, (username, avg_score, total_games) in enumerate(results[:10], 1):
        medal = ''
        if i == 1:
            medal = '🥇 '
        elif i == 2:
            medal = '🥈 '
        elif i == 3:
            medal = '🥉 '
        
        description += f'{medal}**{i}. {username}**\n'
        description += f'   Avg: {avg_score:.2f} | Games: {total_games}\n\n'
    
    embed.description = description
    await ctx.send(embed=embed)


@bot.command(name='stats', aliases=['mystats'])
async def stats(ctx):
    """
    Display your personal Wordle statistics.
    
    Usage: !stats
    """
    user_id = str(ctx.author.id)
    result = bot.db.get_user_stats(user_id)
    
    if not result:
        await ctx.send('You haven\'t recorded any Wordle scores yet!')
        return
    
    username, avg_score, total_games = result
    
    embed = discord.Embed(
        title=f'📈 Wordle Stats for {username}',
        color=discord.Color.blue()
    )
    embed.add_field(name='Average Score', value=f'{avg_score:.2f}', inline=True)
    embed.add_field(name='Total Games', value=str(total_games), inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='help_wordle', aliases=['wordlehelp'])
async def help_wordle(ctx):
    """
    Display help information about the Wordle bot.
    
    Usage: !help_wordle
    """
    embed = discord.Embed(
        title='🎮 Wordle Bot Help',
        description='Track your Wordle scores automatically!',
        color=discord.Color.green()
    )
    
    embed.add_field(
        name='How it works',
        value='Simply paste your Wordle result in any channel and the bot will automatically record it!',
        inline=False
    )
    
    embed.add_field(
        name='Commands',
        value=(
            '`!leaderboard` or `!lb` - Show weekly leaderboard\n'
            '`!leaderboard all` - Show all-time leaderboard\n'
            '`!stats` - Show your personal statistics\n'
            '`!help_wordle` - Show this help message'
        ),
        inline=False
    )
    
    embed.add_field(
        name='Example Wordle Message',
        value='Wordle 1,234 4/6\n⬛⬛🟨⬛⬛\n🟨🟩⬛⬛⬛\n⬛🟩🟩🟩🟩\n🟩🟩🟩🟩🟩',
        inline=False
    )
    
    await ctx.send(embed=embed)


def main():
    """Main entry point for the bot."""
    bot_token = bot.config.get('token')
    
    if not bot_token:
        print('Error: No bot token found in config.json')
        print('Please create config.json from config.json.example and add your bot token.')
        return
    
    bot.run(bot_token)


if __name__ == '__main__':
    main()
