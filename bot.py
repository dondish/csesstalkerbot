import asyncio
import aiohttp
import os
import discord
import fetcher
import time


class Bot:
    def __init__(self, loop: asyncio.AbstractEventLoop = None, session: aiohttp.ClientSession = None):
        self.loop = loop
        self.session = session


client = discord.Client()
bot = Bot()
ids = set()
timers = {}


async def calc_leaderboard(channel):
    if len(ids) == 0:
        return await channel.send('Not enough ids!')
    users = []
    for idx in ids:
        users.append(await fetcher.fetch_user(bot.session, idx))
    users.sort(key=lambda x: x.solvedtasks, reverse=True)
    ranking = 'Ranking'
    maxulen = len(max(users, key=lambda x: len(x.name)).name)
    solved = 'Solved'
    username = 'Username'.center(max(maxulen, len('Username')))
    lastsub = 'Last Submission'
    await channel.send(f'```\n{ranking} | {username} | {solved} | {lastsub}\n' + '\n'.join(
        f'{str(ind + 1).rjust(len(ranking) - 1)}.'
        f' | {u.name.center(len(username))}'
        f' | {str(u.solvedtasks).center(len(solved))}'
        f' | {str(u.lastsub).center(len(lastsub))}' for ind, u in enumerate(users)) + '\n```')


filelock = asyncio.locks.Lock()


class Timer:
    def __init__(self, delay: float, channel: discord.TextChannel):
        self.delay = delay
        self.channel = channel
        self.timer = None
        self.task = asyncio.create_task(self._add_timer())

    async def _add_timer(self):
        await asyncio.sleep(self.delay)
        await calc_leaderboard(self.channel)
        self.task = asyncio.create_task(self._add_timer())

    def cancel(self):
        self.task.cancel()


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
        await msg.channel.send('hi! commands are: help, add, remove, search, leaderboard, about')
    elif cmd == 'add':
        if len(args) > 0 and args[0].isdigit():
            i = int(args[0])
            user = await fetcher.fetch_user(bot.session, i)
            if user is not None:
                ids.add(i)
                await file_writer()
                await msg.channel.send(f'Added {user.name}!')
            else:
                await msg.channel.send('User not found.')
        else:
            await msg.channel.send('Correct Usage: cses!add <id>')
    elif cmd == 'remove':
        if len(args) > 0 and args[0].isdigit():
            i = int(args[0])
            if i in ids:
                user = await fetcher.fetch_user(bot.session, i)
                ids.remove(i)
                await file_writer()
                await msg.channel.send(f'Removed {user.name}!')

            else:
                await msg.channel.send('This id was never there!')
        else:
            await msg.channel.send('Correct Usage: cses!remove <id>')
    elif cmd == 'search':
        if len(args) > 0 and args[0].isdigit():
            i = int(args[0])
            user = await fetcher.fetch_user(bot.session, i)
            if user is not None:
                embed = discord.Embed(title=f'CSES User: {user.name}', color=discord.Colour.blue()) \
                    .add_field(name='Last Submission', value=user.lastsub, inline=False) \
                    .add_field(name='Solved Tasks', value=user.solvedtasks, inline=False)
                await msg.channel.send(embed=embed)
            else:
                await msg.channel.send('User not found.')
        else:
            await msg.channel.send('Correct Usage: cses!search <id>')
    elif cmd == 'leaderboard':
        await calc_leaderboard(msg.channel)
    elif cmd == 'about':
        embed = discord.Embed(title='CSESBot', color=discord.colour.Colour.blue()) \
            .set_footer(text='Created by: dondish', icon_url='https://cdn.discordapp.com'
                                                             '/avatars/239790360728043520'
                                                             '/109999a03001f63e4fc84725d118fe'
                                                             '25.png?size=128') \
            .add_field(name='GitHub', value='[GitHub](https://github.com/dondish/csesstalkerbot)')
        await msg.channel.send(embed=embed)
    elif cmd == 'addtimer':
        if len(args) > 0 and args[0].isdigit() and int(args[0]) > 0:
            seconds = int(args[0]) * 60
            if msg.guild.id in timers:
                timers[msg.guild.id].cancel()
            timers[msg.guild.id] = Timer(seconds, msg.channel)
            await msg.channel.send(f'Started the timer! It will update this channel every {seconds // 60} minutes!')
        else:
            await msg.channel.send('Correct Usage: cses!addtimer <minutes>')
    elif cmd == 'stoptimer':
        if msg.guild.id in timers:
            timers[msg.guild.id].cancel()
            timers[msg.guild.id] = None
            await msg.channel.send('Cancelled the timer!')
        else:
            await msg.channel.send('There was no timer set!')


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.content.startswith('cses!') and message.channel.permissions_for(message.guild.me).send_messages:
        await parse_command(message)


async def main():
    async with aiohttp.ClientSession(loop=loop) as session:
        token = os.environ['TOKEN']
        bot.session = session
        bot.loop = asyncio.get_event_loop()
        await client.start(token)



if __name__ == '__main__':
    try:
        with open('ids.txt', 'r') as f:
            ids.update(map(int, f.readlines()))
    except FileNotFoundError:
        pass
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
