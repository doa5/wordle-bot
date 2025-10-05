# Wordle Bot

Discord bot that tracks Wordle scores with an Oguri Cap personality. Automatically parses results and maintains weekly leaderboards.

## What it does

- Automatically detects Wordle results from Discord messages
- Tracks scores in SQLite database with duplicate prevention
- Weekly leaderboards available Sunday evenings only
- Role management for daily puzzle completion
- Oguri Cap themed responses because why not

## Commands

- `woguri done` - Get the "done" role after completing your puzzle
- `woguri leaderboard` - View weekly scores (Sunday 5-11:59 PM only)
- `woguri resetlb` - Clear database (owner only)
- `woguri showlb` - Show leaderboard outside of view window (owner only)

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

Bot listens for Wordle result messages, extracts user scores, saves them to database. Users can get a role when they're done with the daily puzzle. Weekly leaderboard shows up Sunday evenings with total scores (lower is better).

Scoring: 1-6 attempts recorded as-is, failed attempts (X/6) count as 8 points.

## Architecture

Built with Discord.py cogs:

- WordleParser handles message detection
- DatabaseCog manages SQLite operations
- LeaderboardCog does weekly reports
- RoleCog handles role assignments

Has a full test suite with pytest covering the main functionality.

## Personal project notes

This is just for fun and learning Discord.py development. The Oguri Cap personality is from Uma Musume and makes the bot responses more interesting because she's based.
