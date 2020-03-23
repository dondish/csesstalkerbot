import asyncio
import aiohttp
import os
import discord
import fetcher
import time

client = discord.Client()
session = aiohttp.ClientSession()

ids = set()

filelock = asyncio.locks.Lock()


async def file_writer():
    async with filelock:
        with open('ids.txt', 'w') as f:
            f.write('\n'.join(str(x) for x in ids))
    return


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


async def parse_command(msg: discord.Message):
    s = msg.content
    cmd = s[5:].strip().split()[0]
    args = s[5:].strip().split()[1:]
    if cmd == 'help':
        await msg.channel.send('hi! commands are: help, addid, removeid, searchid, leaderboard')
    elif cmd == 'addid':
        if len(args) > 0:
            i = int(args[0])
            user = await fetcher.fetch_user(session, i)
            await msg.channel.send(f'Added {user.name}!')
            ids.add(i)
            await file_writer()
    elif cmd == 'removeid':
        if len(args) > 0:
            i = int(args[0])
            if i in ids:
                user = await fetcher.fetch_user(session, i)
                ids.remove(i)
                await file_writer()
                await msg.channel.send(f'Removed {user.name}!')
            else:
                await msg.channel.send('This id was never there!')
    elif cmd == 'searchid':
        if len(args) > 0:
            i = int(args[0])
            user = await fetcher.fetch_user(session, i)
            embed = discord.Embed(title=f'CSES User: {user.name}', color=discord.Colour.blue()) \
                .add_field(name='Last Submission', value=user.lastsub, inline=False) \
                .add_field(name='Solved Tasks', value=user.solvedtasks, inline=False)
            await msg.channel.send(embed=embed)
    elif cmd == 'leaderboard':
        users = []
        for idx in ids:
            users.append(await fetcher.fetch_user(session, idx))
        users.sort(key=lambda x: x.solvedtasks, reverse=True)
        await msg.channel.send('```\n' + '\n'.join(f'{ind + 1}. {u.name}. Solved: {u.solvedtasks}.'
                                                   f' Last Submission: {u.lastsub}' for ind, u in
                                                   enumerate(users)) + '```')


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.content.startswith('cses!') and message.channel.permissions_for(message.guild.me).send_messages:
        await parse_command(message)


if __name__ == '__main__':
    try:
        with open('ids.txt', 'r') as f:
            ids.update(map(int, f.readlines()))
    except FileNotFoundError:
        pass
    token = os.environ['TOKEN']
    client.run(token)
