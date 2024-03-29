"""

26/08/2022
"""
import discord
import os
import shutil
from discord.ext import commands
import requests


async def upload_data(ctx: commands.Context, env: dict):
    """Upload the relevant warboard csv"""

    war_name = ctx.channel.name.replace("/", "-")
    src = os.path.join(os.getcwd(), "data", "raw", f'{war_name} Raw.csv')
    await ctx.send(file=discord.File(src))


async def save_warboards(ctx: commands.Context, env: dict):
    """Save all of the warboard images into the appropriate folder"""

    # Ensure folder exists
    war_name = ctx.channel.name.replace("/", "-")
    if not os.path.isdir(f'./data/{war_name}'):
        os.makedirs(f'./data/{war_name}')
    
    num_found = 0
    async for message in ctx.channel.history(limit=200):
        for attachment in message.attachments:
            num_found += 1
            fn = f'{num_found}_{attachment.filename}'
            await attachment.save(f'./data/{war_name}/{fn}')
        for embed in message.embeds:
            r = requests.get(embed.url)
            with open(f'./data/{war_name}/embed_{num_found}.png', 'wb') as outfile:
                outfile.write(r.content)
            num_found += 1
    print(f'Found {num_found} attachments')

    return 0


async def del_warboards(ctx: commands.Context, env: dict):
    """Delete the warboard images associated with a read command"""
    
    war_name = ctx.channel.name.replace("/", "-")

    try:
        shutil.rmtree(f'./data/{war_name}')
    except OSError as e:
        print("Error: %s : %s" % (f'./data/{war_name}', e.strerror))


def validate_ctx(ctx: commands.Context, env: dict, check_thread: bool = False):
    """Validate the context of a command"""

    # Needs to be lowercase
    REQ_ROLES = ["members", "member", "war council", "bandit", "support team"]

    # Check server
    guild = str(ctx.guild.id)
    if guild not in env['valid_servers']:
        return f'{ctx.guild.name} is not a validated server. Aborting...'

    # Check role
    roles = get_roles(ctx.author)
    roles = [role.lower() for role in roles]
    print(f'[{ctx.message.created_at}] Roles: {roles}')
    if not (set(REQ_ROLES) & set(roles)):
        return f'Invalid user permissions. Aborting...'

    # Check in thread
    if (check_thread) and ("thread" not in str(ctx.channel.type)):
        return f'This command can only be run from within a thread. Aborting...'

    return 0


def get_roles(user) -> list:
    """Returns a list of strings of a user's roles"""

    return [x.name.lower() for x in user.roles]