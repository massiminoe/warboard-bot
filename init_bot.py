"""

26/08/2022
"""
import discord
from discord.ext import commands
import jsonenv
import os
import utils
import warboard_reader

CMD_PREFIX = "!wb "

# Load env and setup bot
env = jsonenv.load_env()
token = env['discord_token']
valid_servers = env['valid_servers']
owner_id = int(env['owner_id'])
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=commands.when_mentioned_or(CMD_PREFIX), intents=intents, owner_id=owner_id)


# Events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    # Ensure folder exists
    if not os.path.isdir('./data'):
        os.makedirs('./data')
    if not os.path.isdir('./data/raw'):
        os.makedirs('./data/raw')


# Commands
@bot.command(name="status")
async def status(ctx):
    """\o/"""
    print(f'{ctx.guild.name}: {ctx.guild.id}')
    res = 3
    await ctx.send(res)

@bot.command(name="read")
async def read(ctx: commands.Context):
    """Read and process uploaded warboards in the context's thread."""

    war_name = ctx.channel.name
    war_name = war_name.replace("/", "-")
    await ctx.send(f"Reading {war_name}")

    print(f'[{ctx.message.created_at}] {ctx.author.name}: !wb read')

    # Validate
    err_msg = utils.validate_ctx(ctx, env, check_thread=True)
    if err_msg:
        await ctx.send(err_msg)
        return print(err_msg)

    
    await utils.save_warboards(ctx, env)
    warboard_reader.read_war_data(war_name)
    await utils.upload_data(ctx, env)
    await utils.del_warboards(ctx, env)


bot.run(token)
