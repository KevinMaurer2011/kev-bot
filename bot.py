import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
import ollama

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# --- CONFIGURATION ---
AFK_DATA_FILE = 'afk_data.json'
AI_MODEL = "llama3.2:3b"  # <--- I added this variable here so the bot knows which model to use
# ---------------------

def load_afk_data():
    if not os.path.exists(AFK_DATA_FILE):
        return {}
    try:
        with open(AFK_DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_afk_data(data):
    with open(AFK_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_voice_state_update(member, before, after):
    # Check if member moved to the AFK channel
    if after.channel and member.guild.afk_channel and after.channel == member.guild.afk_channel:
        # Avoid counting if they were already in the AFK channel
        if before.channel == after.channel:
            return

        data = load_afk_data()
        user_id = str(member.id)
        user_name = str(member.name)
        
        if user_id not in data:
            data[user_id] = {'count': 0, 'name': user_name}
        
        data[user_id]['name'] = user_name
        data[user_id]['count'] += 1
        
        save_afk_data(data)
        print(f"Tracked AFK move for {user_name}. Total: {data[user_id]['count']}")

@bot.command(name='afktally')
async def afktally(ctx):
    data = load_afk_data()
    if not data:
        await ctx.send("No AFK stats recorded yet.")
        return

    sorted_users = sorted(data.items(), key=lambda item: item[1]['count'], reverse=True)
    top_users = sorted_users[:10]
    
    msg = "**AFK Channel Trip Tally**\n"
    for rank, (user_id, info) in enumerate(top_users, 1):
        msg += f"{rank}. **{info['name']}**: {info['count']} times\n"
    
    await ctx.send(msg)

@bot.command()
async def roast(ctx, member: discord.Member = None, *, context: str = None):
    # 1. Handle cases where no user is tagged (roast the sender)
    if member is None:
        member = ctx.author

    # 2. Show typing indicator
    async with ctx.typing():
        
        # 3. Build the prompt dynamically
        if context:
            # If you provided specific ammo:
            prompt = f"Roast {member.name}. Specifically roast them for this reason: '{context}'. Be sarcastic and rude. Keep it under 2 sentences."
        else:
            # If you didn't provide ammo (Generic roast):
            prompt = f"Roast {member.name}. They are a user on a Discord server. Be sarcastic, funny, and lighthearted. Keep it under 2 sentences."
        
        try:
            # 4. Send to AI
            response = ollama.chat(model=AI_MODEL, messages=[
                {'role': 'system', 'content': 'You are a rude and sarcastic comedian.'},
                {'role': 'user', 'content': prompt},
            ])
            
            ai_reply = response['message']['content']
            await ctx.send(f"{member.mention} {ai_reply}")

        except Exception as e:
            await ctx.send(f"I tried to roast them but my brain broke: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # --- I fixed the try/except block here ---
    print("Waking up the AI... (this might take a few seconds)")
    try:
        ollama.chat(model=AI_MODEL, messages=[{'role': 'user', 'content': 'hi'}])
        print(f"Success! {AI_MODEL} is loaded and ready.")
    except Exception as e:
        print(f"Warning: Could not pre-load AI. It will load on first command. Error: {e}")
    # -----------------------------------------

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('pong')

@bot.command(name='roastme')
async def roastme(ctx):
    insults = [
        "You're like a cloud. When you disappear, it's a beautiful day.",
        "I'd roast you, but my mom told me not to burn trash.",
        "You have something on your chin... no, the 3rd one down.",
        "I’m not saying I hate you, but I would unplug your life support to charge my phone.",
        "You’re the reason the gene pool needs a lifeguard.",
        "If I wanted to kill myself, I’d climb your ego and jump to your IQ.",
        "You're proof that evolution can go in reverse.",
        "I'd give you a nasty look, but you've already got one.",
        "You're not the dumbest person in the world, but you better hope they don't die.",
        "Some cause happiness wherever they go; others whenever they go."
    ]
    roast = random.choice(insults)
    await ctx.send(f"{ctx.author.mention} {roast}")

if __name__ == '__main__':
    if not TOKEN or TOKEN == 'your_token_here':
        print("Error: DISCORD_TOKEN not found or not set in .env file.")
    else:
        bot.run(TOKEN)