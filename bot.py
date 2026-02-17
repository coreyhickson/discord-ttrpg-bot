import discord
from discord.ext import commands
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

class IdleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), IdleHandler)
    server.serve_forever()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'user_has_group.json'

def load_user_status():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_status(user_status):
    with open(DATA_FILE, 'w') as f:
        json.dump(user_status, f)

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')

@bot.command()
async def startgroup(ctx):
    user_id = str(ctx.author.id)
    guild = ctx.guild
    user_status = load_user_status()
    
    if user_id in user_status:
        await ctx.send("You already created a group! Speak to an admin if you need another.")
        return
    
    group_name = f"{ctx.author.display_name}'s TTRPG Group"
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            read_message_history=False
        ),
        ctx.author: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, manage_channels=True,
            manage_permissions=True, view_channel=True, connect=True,
            read_message_history=True
        )
    }
    
    category = await guild.create_category(group_name, overwrites=overwrites, reason=f"Private group for {ctx.author}")
    
    user_status[user_id] = True
    save_user_status(user_status)
    
    text_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
    }
    voice_overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
        ctx.author: discord.PermissionOverwrite(connect=True, speak=True, view_channel=True)
    }
    
    await guild.create_text_channel("general", category=category, overwrites=text_overwrites)
    await guild.create_voice_channel("chat", category=category, overwrites=voice_overwrites)
    
    await ctx.send(f"✅ **{group_name}** created! You have full manage permissions.")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    bot.run(os.getenv('DISCORD_TOKEN'))
