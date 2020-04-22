
from discord.ext import commands
import json
import os
import traceback
with open('creds.json','r') as f:
    creds = json.load(f)
    token = creds["token"]

bot = commands.AutoShardedBot(command_prefix='!', formatter=None, description=None, pm_help=False,max_messages=50000)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"ID: {bot.user.id}")
    print(f"invite: https://discordapp.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot")
    try:
        for cog in os.listdir('cogs/'):

            if cog.endswith('.py'):
                bot.load_extension("cogs."+cog[:-3])
        print("All cogs loaded OK")
    except Exception as e:
        print("Error loading cog")
        print(e)
        print("""**Traceback:**\n```{0}```\n""".format(' '.join(traceback.format_exception(None, e, e.__traceback__))))


bot.run(token)
