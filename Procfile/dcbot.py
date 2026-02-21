import discord
from discord.ext import tasks, commands
import instaloader
import json
import os
import asyncio

# -------- CONFIGURATION SECTION --------

import os
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")   # bot token
TARGET_CHANNEL_ID = 1474768338084302900        # Discord channel ID
INSTAGRAM_USERNAME = "pixelvibes05"              # Instagram username 
CHECK_INTERVAL_SECONDS = 1800                  # how often to check

LAST_POSTS_FILE = "last_posts.json"
# ---------------------------------------


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

insta_loader = instaloader.Instaloader()

def load_last_posts():
    # If file does not exist, just return empty dict
    if not os.path.exists(LAST_POSTS_FILE):
        return {}

    try:
        with open(LAST_POSTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, PermissionError, OSError):
        # If file is corrupted or access issue, just ignore and start fresh
        return {}


def save_last_posts(data):
    try:
        with open(LAST_POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except PermissionError as e:
        print(f"Cannot write to {LAST_POSTS_FILE}: {e}")


async def fetch_latest_instagram_post(username: str):
    """
    Uses instaloader to get the latest post shortcode for a public Instagram profile.
    Returns (shortcode, post_url) or (None, None) on error.
    """
    try:
        profile = instaloader.Profile.from_username(insta_loader.context, username)
        posts = profile.get_posts()
        latest_post = next(posts, None)
        if latest_post is None:
            return None, None
        shortcode = latest_post.shortcode
        url = f"https://www.instagram.com/p/{shortcode}/"
        return shortcode, url
    except Exception as e:
        print(f"Error fetching Instagram for {username}: {e}")
        return None, None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_instagram_posts.start()

@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_instagram_posts():
    await bot.wait_until_ready()
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check TARGET_CHANNEL_ID.")
        return

    last_posts = load_last_posts()
    last_shortcode = last_posts.get(INSTAGRAM_USERNAME)

    shortcode, url = await fetch_latest_instagram_post(INSTAGRAM_USERNAME)
    if shortcode is None or url is None:
        print("Could not get latest post.")
        return

    if shortcode != last_shortcode:
        embed = discord.Embed(
            title=f"New Instagram post by {INSTAGRAM_USERNAME}",
            description=url,
            color=0xE1306C  # Instagram-like color
        )
        embed.add_field(name="Profile", value=f"https://www.instagram.com/{INSTAGRAM_USERNAME}/", inline=False)

        await channel.send(embed=embed)

        last_posts[INSTAGRAM_USERNAME] = shortcode
        save_last_posts(last_posts)
        print(f"Posted new Instagram link: {url}")
    else:
        print("No new post.")

@bot.command()
async def ping(ctx):
    await ctx.send("Bot is online!")

bot.run(DISCORD_TOKEN)
