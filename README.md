# Wordle Bot ( ◡̀_◡́)ᕤ

Discord bot that tracks Wordle scores with an Oguri Cap personality. Automatically parses results and maintains weekly leaderboards.

## Add to your server

[Invite Woguri Bot](https://discord.com/oauth2/authorize?client_id=1422909283451932803&permissions=275146730560&integration_type=0&scope=bot)

The bot is hosted and maintained, just invite and use.

## What it does

- Automatically detects Wordle results from Discord messages
- Tracks scores in SQLite database with duplicate prevention
- Weekly leaderboards available Sunday evenings only
- Role management for daily puzzle completion
- Oguri Cap themed responses because why not (￣ ▽ ￣)"
- Manual score entry and database admin tools
- Terminal logging to Discord for remote monitoring

## Commands

### Daily Use

- `woguri done` - Get the "done" role after completing your puzzle
- `woguri leaderboard` - View weekly scores (Sunday 5-11:59 PM only)
- `woguri snack` - Random Oguri Cap GIF because she's hungry
- `woguri show_all_commands` - List all available commands if you forget

### Score Management (Owner/Admin)

- `woguri manual_score 2024-01-15 @user 3` - Add scores manually
- `woguri overwrite_score 2024-01-15 @user 4` - Replace existing scores
- `woguri recent_scores 10` - Show last 10 database entries
- `woguri recent_scores 25 2024-10-06` - Show entries from specific date
- `woguri recent_scores 10 2024-10-06 @user` - Filter by user and date

### Database Admin (Owner Only)

- `woguri db_stats` - Database statistics
- `woguri db_guilds` - Show all servers using the bot
- `woguri show_duplicates` - Find duplicate submissions
- `woguri clean_duplicates` - Remove duplicates (keeps first entry)
- `woguri resetlb` - Clear database (dangerous!)
- `woguri showlb` - Show leaderboard outside of view window

### Role Management (Owner Only)

- `woguri reset` - Remove "done" role from everyone manually
- `woguri resetcheck` - Check if daily role reset is working
- `woguri test_daily_reset` - Test the midnight reset functionality

### Logging System (Owner Only)

- `woguri enable_terminal_logs` - Send bot logs to Discord
- `woguri disable_terminal_logs` - Stop Discord logging
- `woguri log_status` - Check logging system status

Works with both `woguri` and `Woguri` prefixes. Invalid commands get Oguri Cap responses.

## For Developers

If you want to run your own instance, here's how:

## Setup

Need Python 3.8+ and a Discord bot token.

```bash
pip install -r requirements.txt
```

Create `.env` file:

```env
DISCORD_TOKEN=your_bot_token_here
WORDLE_BOT_ID=official_wordle_bot_id_here
```

Run with:

```bash
python main.py
```

The bot needs basic Discord permissions (read/send messages, manage roles, add reactions) and you'll want a "done" role in your server.

## How it works

Bot listens for Wordle result messages, extracts user scores, saves them to database. Users can get a role when they're done with the daily puzzle. Weekly leaderboard shows up Sunday evenings with total scores (lower is better). (⁀ᗢ⁀)

Scoring: 1-6 attempts recorded as-is, failed attempts (X/6) count as 8 points.

## Architecture

Built with Discord.py cogs:

- WordleParser handles message detection
- DatabaseCog manages SQLite operations and terminal logging
- LeaderboardCog does weekly reports
- RoleCog handles role assignments
- OguriCapCog for personality and GIFs

Has a full test suite with pytest covering the main functionality.

## Personal project notes

This is just for fun and learning Discord.py development. The Oguri Cap personality is from Uma Musume and makes the bot responses more interesting because she's based. ᕙ(‾̀◡‾́)ᕗ

Deployed on Oracle Cloud VM because why pay for hosting when you can get it free. Has terminal logging to Discord so you can monitor it remotely.

And it's Woguri because Wordle + Oguri in case you didn't catch on. (─‿─)
