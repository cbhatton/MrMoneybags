import os
import json
from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="$")

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

    drip.start()


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)


@bot.command()
async def balance(ctx):
    user = ctx.author.id
    await open_account(user)
    users = await bank_info()
    print(users)
    cash = users[str(user)]['cash']

    await ctx.send(f'Balance: {cash}')
    return f'Balance: {cash}'


async def open_account(user):
    users = await bank_info()
    if str(user) in users:
        return False
    else:
        users[str(user)] = {}
        users[str(user)]['cash'] = 0

    with open("./bank.json", 'w') as f:
        json.dump(users, f)

    return True


@tasks.loop(minutes=1)
async def drip():
    wallets = await bank_info()
    for guild in bot.guilds:
        channels = guild.voice_channels
        for channel in channels:
            voices = channel.voice_states
            for user in voices:
                if voices[user].afk is False:
                    await open_account(user)
                    wallets[str(user)]['cash'] += 1
                    await dump(wallets)


async def bank_info():
    with open("./bank.json") as f:
        return json.load(f)


async def dump(users):
    with open("./bank.json", 'w') as f:
        json.dump(users, f)


async def transaction(ctx, type, amount):
    wallets = await bank_info()
    if type == 'give':
        wallets[str(ctx.author.id)]['cash'] += amount
    elif type == 'take':
        wallets[str(ctx.author.id)]['cash'] -= amount

    await dump(wallets)


@bot.command()
async def test(ctx):
    if await check_funds(ctx, 10) is False:
        await ctx.send('transaction canceled')
        return

    await ctx.send("thanks for your money, sucker!")



#========================STORE=======================#
# here are commands that users will be able to call in
# order to purcahse certain FUNctions


async def check_funds(ctx, amount):
    bank = await bank_info()
    user = ctx.author
    cash = bank[str(user.id)]['cash']
    if cash < amount:
        await ctx.send("Insufficient funds")
        return False

    # ask user if they would like to purcahse this FUNction
    await ctx.send(f'spend {amount} to use this FUNction?\nenter y/n:')

    def check(msg):
        return msg.author == user and (msg.content == 'y' or msg.content == 'n')
    response = await bot.wait_for('message', check=check)
    if response == 'n':
        return False
    elif response == 'y':
        return True


@bot.command(name='lets-role')
async def create_new_role(ctx, name):
    if await check_funds(ctx, 100) is False:
        await ctx.send('transaction canceled')
        return

    for role in ctx.guild.roles:
        if role.name == name:
            await transaction(ctx, 'take', 100)
            await ctx.send('transaction complete, you have been added to this role')
            return

    role = await ctx.guild.create_role(name=name)
    await ctx.author.add_roles(role)
    await transaction(ctx, 'take', 100)
    await ctx.send('transaction complete')


@bot.command()
async def mint(ctx, item):
    if await check_funds(ctx, 10) is False:
        await ctx.send('transaction canceled')
        return

    users = await bank_info()
    for user in users:
        if item in users[user]:
            ctx.send(f"This item is already owned by {ctx.guild.get_member(int(user))}")
            return
    ctx.send("enter a brief description for this item")
    def check(msg):
        return msg.author == user
    item_description = await bot.wait_for('message', check=check)
    users[str(ctx.author.id)][str(item)] = item_description

    await dump(users)



bot.run(TOKEN)