import time
import discord
from discord.ext import commands
from discord.ext.pages import Paginator, Page
import pickle
import re

import requests

with open("guild.pickle", "rb") as f:
    guild = pickle.load(f)

class Smokespew(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def search_card(self, message: discord.Message):
        x = re.search("(?<=\[\[).+(?=\]\])", message.content)
        if not x:
            return
        full_json = []
        for match in x.groups():
            time.sleep(0.25)
            response = requests.get(
                f"https://api.scryfall.com/cards/named?fuzzy={match}",
                headers={"UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"},
            )
            full_json += (resjson := response.json())["data"]
            while resjson["has_more"]:
                time.sleep(0.25)
                response = requests.get(
                    resjson["next_page"],
                    headers={"UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"},
                )
                full_set_json += (resjson := response.json())["data"]
        paginator = Paginator(pages=[Page(content=f'{c["uri"][:-3]}discord') for c in full_json])
        ctx = await self.get_context(message)
        await paginator.send(ctx)

def setup(bot):
    bot.add_cog(Smokespew(bot))