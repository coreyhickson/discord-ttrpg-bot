import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'user_groups.json'

# Load existing user groups from JSON
def load_groups():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save user groups to JSON
def save_groups(groups):
    with open(DATA_FILE, 'w') as f:
        json.dump(groups, f)

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')

@bot.command()
async def startgroup(ctx):
    user_id = str(ctx.author.id)
    guild = ctx.guild
    
    # Load current groups
    groups = load_groups()
    
    # Check if user already has a group
    if user_id in groups:
        existing_cat = guild.get_channel(int(groups[user_id]))
        if existing_cat and existing_cat.category:
            await ctx.send(f"You already have a group: **{existing_cat.name}**. Delete it first if needed.")
            return
        else:
            # Clean up stale entry
            del groups[user_id]
            save_groups(groups)
    
    # Create unique category name
    group_name = f"Group-{ctx.author.display_name}-{ctx.author.discriminator}"
    
    # Permission overwrites: only invoker can manage, @everyone denied
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
        ctx.author: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, manage_channels=True,
            manage_permissions=True, view_channel=True, connect=True
        )
    }
    
    # Create the private category
    category = await guild.create_category(group_name, overwrites=overwrites, reason=f"Private group for {ctx.author}")
    
    # Save the mapping
    groups[user_id] = str(category.id)
    save_groups(groups)
    
    # Create sample channels (optional; user can manage/add more)
    text_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    voice_overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
        ctx.author: discord.PermissionOverwrite(connect=True, speak=True, view_channel=True)
    }
    
    await guild.create_text_channel("general", category=category, overwrites=text_overwrites)
    await guild.create_voice_channel("chat", category=category, overwrites=voice_overwrites)
    
    await ctx.send(f"✅ **{group_name}** created! You have full manage permissions (create/delete channels, delete category).\nIt’s private to you only.")

@bot.command()
@commands.has_permissions(administrator=True)
async def cleangroups(ctx):
    """Admin: Clean up all user groups (for testing)"""
    groups = load_groups()
    guild = ctx.guild
    deleted = 0
    for user_id, cat_id in list(groups.items()):
        cat = guild.get_channel(int(cat_id))
        if cat:
            await cat.delete()
            deleted += 1
    groups.clear()
    save_groups(groups)
    await ctx.send(f"🧹 Deleted {deleted} groups.")

bot.run(os.getenv('DISCORD_TOKEN'))
