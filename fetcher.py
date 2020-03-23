import aiohttp
import asyncio
from datetime import datetime
from bs4 import *

class User:
    def __init__(self, k: dict):
        self.id = k['id']
        self.name = k['name']
        self.lastsub = k['lastsub']
        self.solvedtasks = k['solvedtasks']

    def __repr__(self):
        return f'{self.name}'


def url_from_id(i: int):
    return f"https://cses.fi/user/{i}/"


async def fetch_page(session: aiohttp.ClientSession, i: int):
    async with session.get(url_from_id(i)) as resp:
        return await resp.text()


def parse_page(text: str, i: int):
    soup = BeautifulSoup(text, 'html.parser')
    name = soup.h1.string[5:]
    lastsub = datetime.strptime(soup.find(string='Last submission').parent.parent.contents[1].string, '%Y-%m-%d '
                                                                                                      '%H:%M:%S')
    s = soup.find(string='CSES Problem Set')
    solved = int(s.parent.parent.contents[1].string if s is not None else '0')
    return User({'name': name, 'id': i, 'lastsub': lastsub, 'solvedtasks': solved})


async def fetch_user(session: aiohttp.ClientSession, i: int):
    page = await fetch_page(session, i)
    return parse_page(page, i)

async def main():
    async with aiohttp.ClientSession() as session:
        p = await fetch_page(session, 9243)
        print(parse_page(p, 9243))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
