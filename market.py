import re
import asyncio
import aiohttp
import discord
from discord.ext import commands
import discord.utils as utils
from market_info import *

class MktBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)
        self.remove_command('help')

bot = MktBot(command_prefix='!', description= '''The market price portion.''')
root = 'http://blocgame.com/'
market_url = root + 'market.php'

# bot will only listen to Blue Sashes
@bot.check
def check_role(ctx):
    roles = ctx.message.author.roles
    if utils.find(lambda r: r.id==role_id, roles):
        return True or check_me(ctx)
# prevent #general_chat from interacting with bot
@bot.check
def check_channel(ctx):
    return ctx.message.channel.id != '272570598381584384'

session = aiohttp.ClientSession()

async def get_html(url):
    async with session.get(url) as resp:
        html = await resp.text()
        return html

async def post_html(url, data):
    post_header = { 'User-Agent':'Firefox',
                    'Content-Type':'application/x-www-form-urlencoded' }
    async with session.post(url = url,
                            data = data,
                            headers = post_header) as resp:
        pass

async def login(username):
    #use in get_status_html(), which is always called before any html
    #action anyway. So, just have the login and status check pages the same
    login_post = {'username':username,'password':pwd,'login':1}
    page = await get_html(market_url)
    while page.find('action="login.php"') is not -1:
        await post_html(url = root+'login.php',
                        data = login_post)
        page = await get_html(market_url)
    return page

async def logout():
    await get_html(root + 'logout.php')

async def get_market_html(username):
    html = await login(username)
    re_market = r'<table class="table table-hover">[\s\S]*?<\/table>'
    market = re.search(re_market, html).group(0)
    await logout()
    return market

def get_price(market, key):
    _re = r'[\s\S]*?<button'
    price_re = r'(?<=<b>)\d+'
    price = re.search(key+_re, market).group(0)
    price = re.search(price_re, price).group(0)
    return price

def get_prices(market):
    prices = ['Buy Oil', 'Sell Oil', 'Buy Raw Material', 'Sell Raw Material',
                'Buy Food', 'Sell Food', 'Buy Manufactured Goods',
                'Sell Manufactured Goods']
    values = [get_price(market, p) for p in prices]
    return dict(zip(prices, values))

async def get_all_prices():
    regions = [ME, AS, LA, AF]
    markets = []
    for region in regions:
        market = await get_market_html(region)
        markets.append(market)
    prices = [get_prices(market) for market in markets]
    return dict(zip(['ME', 'AS', 'LA', 'AF'], prices))

@bot.command()
async def market():
    tmp = await bot.say('Fetching prices')
    prices = await get_all_prices()
    await bot.delete_message(tmp)
    for region, market in prices.items():
        market['oil'] = '{}/{}'.format(market['Buy Oil'],                market['Sell Oil'])
        market['RM']  = '{}/{}'.format(market['Buy Raw Material'],       market['Sell Raw Material'])
        market['fud'] = '{}/{}'.format(market['Buy Food'],               market['Sell Food'])
        market['MG']  = '{}/{}'.format(market['Buy Manufactured Goods'], market['Sell Manufactured Goods'])
        market['width'] = max([len(v) for v in market.values()]) + 2
    regions = ['ME', 'AS', 'LA', 'AF']
    resources = ['oil', 'RM', 'fud', 'MG']
    width = 5 # 'oil' + 2
    fmt_w = {'w':width, 'ME_w': prices['ME']['width'], 'AS_w': prices['AS']['width'], 'LA_w': prices['LA']['width'], 'AF_w': prices['AF']['width']}
    msg = '`\u2554{:\u2550^{w}}\u2566{:\u2550^{ME_w}}\u2564{:\u2550^{AS_w}}\u2564{:\u2550^{LA_w}}\u2564{:\u2550^{AF_w}}\u2557`\n'.format('','','','','', **fmt_w)
    msg += '`\u2551{:^{w}}\u2551{:^{ME_w}}\u2502{:^{AS_w}}\u2502{:^{LA_w}}\u2502{:^{AF_w}}\u2551`\n'.format('',*regions, **fmt_w)
    msg += '`\u255f{:\u2500^{w}}\u256b{:\u2500^{ME_w}}\u2536{:\u2500^{AS_w}}\u2536{:\u2500^{LA_w}}\u2536{:\u2500^{AF_w}}\u2562`\n'.format('','','','','', **fmt_w)
    for resource in resources:
        msg += '`\u2551{:^{w}}\u2551'.format(resource, w=width)
        for region in regions:
            msg += '{:^{w}}\u2502'.format(prices[region][resource], w=prices[region]['width'])
        msg = msg[:-1]
        msg += '\u2551`\n'
    msg += '`\u255a{:\u2550^{w}}\u2569{:\u2550^{ME_w}}\u2567{:\u2550^{AS_w}}\u2567{:\u2550^{LA_w}}\u2567{:\u2550^{AF_w}}\u255d`\n'.format('','','','','', **fmt_w)
    await bot.say(msg)

bot.run(token)
