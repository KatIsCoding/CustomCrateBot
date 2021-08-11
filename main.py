import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions
from discord import Member
import json
import requests
import asyncio
from random import randint
import os

intents = discord.Intents.default()
intents.members = True


#import tracemalloc
#tracemalloc.start()

prefix = ("c!","C!")

TOKEN = ""
bot = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True,help_command=None)
defaultcommandschannelid = 803720790184820758
defaultgiveawaychannelid = 803810291916996608
cratename = "Common"
count = 0
limit = 200

def inventoryfunc(ctx,serverid,userid):
    embedVar = discord.Embed(title="Inventory",description="Let's see what things do you have in your bag", color=0x00FF00)
    embedVar.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
    with open("storage.json","r") as crate, open("inventory.json","r") as inventory:
        crates = json.load(crate)
        inv = json.load(inventory)
    if userid not in inv:
        inv[userid] = {}
    if userid not in crates[serverid]:
        crates[serverid][userid] = {}
    embedVar.add_field(name="---Crates---",value="--------------------", inline=False)
    for x in crates[serverid][userid]:
        if crates[serverid][userid][x] > 0:
            embedVar.add_field(name=x,value=crates[serverid][userid][x], inline=False)
    embedVar.add_field(name="---Items---",value="--------------------", inline=False)
    currencydict = {}
    if userid in inv:
        for x in inv[userid]:
            if inv[userid][x] > 0:        
                if ":mcoin:" in x or ":xp:" in x:
                    special = x.replace("<:mcoin:804490130877972480>","").replace("<:xp:798475384370233376>","")
                    special = int(special)
                    emojiindex =  x.find("<")
                    if x[emojiindex::] not in currencydict:
                        currencydict[x[emojiindex::]] = special * inv[userid][x]
                    else:
                        currencydict[x[emojiindex::]] += special * inv[userid][x]
                    embedVar.add_field(name=f"{x[emojiindex::]}",value=f"{x} (x{inv[userid][x]})", inline=False)       
                else:    
                    embedVar.add_field(name=x,value=inv[userid][x], inline=False)
        embedVar.add_field(name="Totals", value="-------------", inline=False)
        for x in currencydict:
            embedVar.add_field(name=x,value=currencydict[x], inline=True)
        currencydict = {}
    return embedVar


def rename_keys(d, keys):
    return [(keys) for k, v in d.items()]
def in_channel(channel_id):
    def predicate(ctx):
        return ctx.message.channel.id == channel_id
    return commands.check(predicate)
def calcprize(crate):
    currentlist = {}
    with open("registeredcrates.json","r") as jsonn:
        crates = json.load(jsonn)
    currentlist[next(iter(crates[crate]))] = range(0,crates[crate][next(iter(crates[crate]))])
    last = crates[crate][next(iter(crates[crate]))]
    # Stores in the dictionary the name of the first prize in the crate and define it's value
    # (Which is from 0 to the number of probabilities the prize has)
    for x in crates[crate]:
        if x not in currentlist:    #Checks if the actual prize is already in the list, necessary because if not is going to overwrite
            if crates[crate][x] != 0:
                currentlist[x] = range(last, crates[crate][x] + last)  #Setting up the numbers for each prize
                last = last + crates[crate][x]
        if last == 0:
            return False
    randomnumber = randint(0,last) # Random number from 0 to the last number used
    for x in currentlist:
        if randomnumber in currentlist[x]:
            return x



@bot.command()
async def help(ctx):
    embedVar = discord.Embed(title=f"Commands Help",description="Usage and description of every command", color=0x00FF00)
    embedVar.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
    embedVar.add_field(name="---Admin Commands---",value="-----------------------------------------------", inline=False)
    embedVar.add_field(name="c!edit",value="Used to edit a crate. c!edit |cratename| |oldprizename| |newprizename|", inline=False)
    embedVar.add_field(name="c!create",value="Used to add new crates. c!create |cratename|",inline=False)
    embedVar.add_field(name="c!add",value="Used to give crates to users. c!add |cratename| |@user|",inline=False)
    embedVar.add_field(name="c!update", value="Used to add prizes to an existing crate. c!update |cratename| |prizename| |quantity|",inline=False)
    embedVar.add_field(name="c!remove", value="Used to remove items or crates from players. c!remove |crate / item| |@user| |name| |quantity|",inline=False)
    embedVar.add_field(name="c!setchannel", value="Used to set the giveaway announcement channel. c!setchannel |channel_id|",inline=False)
    embedVar.add_field(name="c!setconf", value="Used to change giveaway configuration. c!setconf |msgs / crate| |integer / name|",inline=False)
    embedVar.add_field(name="c!inventory", value="Used to see own inventory or other's inventory. c!inventory |@user(optional)|. Only admins can see other's inventory",inline=False)
    embedVar.add_field(name="c!remcrate", value="Used to remove crates and its contents. c!remcrate |cratename|.",inline=False)
    embedVar.add_field(name="c!info", value="Used to return crate prizes. c!infto |cratename|",inline=False)
    embedVar.add_field(name="---Member Commands---",value="-----------------------------------------------", inline=False)
    embedVar.add_field(name="c!gift", value="Used to gift crates. c!gift |cratename| |@user|",inline=False)
    
    embedVar.add_field(name="c!open", value="Used to open a crate. c!open |cratename|",inline=False)
    embedVar.add_field(name="c!crates", value="Used to list all crates",inline=False)
    await ctx.send(embed=embedVar)


#@tasks.loop(seconds=5)
async def auto_api():
    while True:
        auth = {"Authorization" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI4MDQ0Mjg4NjIyODgxNjcwMjYiLCJpYXQiOjE2MTE4NjExODZ9.gA2vUOrsHGsz9rkEvlk9lp284M3nHCKiTY9KertO74A"}
        currencydict = {}
        #try:
        with open("inventory.json","r") as inventory:
            inv = json.load(inventory)
        for users in inv:
            currencydict = {}
            for x in inv[users]:
                if inv[users][x] > 0:        
                    if ":mcoin:" in x:
                        special = x.replace("<:mcoin:804490130877972480>","")
                        special = int(special)
                        emojiindex =  x.find("<")
                        if x[emojiindex::] not in currencydict:
                            currencydict[x[emojiindex::]] = special * inv[users][x]
                        else:
                            currencydict[x[emojiindex::]] += special * inv[users][x]


            if "<:mcoin:804490130877972480>" in currencydict:
                if currencydict["<:mcoin:804490130877972480>"] >= 1000:
                    limit = 1000
                    r = requests.patch(url=f"https://unbelievaboat.com/api/v1/guilds/534158738735497217/users/{users}",json={"cash":1000}, headers=auth)
                    currencydict.pop("<:mcoin:804490130877972480>")
                    while limit > 0:
                        for x in list(inv[users]):
                            if ":mcoin:" in x and inv[users][x] > 0:
                                specialx = x.replace("<:mcoin:804490130877972480>","")
                                specialx = int(specialx)
                                if specialx > limit:
                                    inv[users][str(specialx - limit) + "<:mcoin:804490130877972480>"] = inv[users].pop(x) 
                                    limit = 0
                                else:
                                    inv[users][x] += -1
                                    limit = limit - int(specialx)
                                print(limit)
                                print(specialx)
                with open("inventory.json", "w") as write:
                    json.dump(inv, write, indent=4)
            print(currencydict)       
            currencydict = {}
            await asyncio.sleep(5)
    #except Exception:
    #    pass

                

        




@bot.command()
@has_permissions(manage_roles=True, ban_members=True)
async def remcrate(ctx, cratename):
    cratename = cratename.lower().capitalize()
    with open("registeredcrates.json","r") as crate:
        crates = json.load(crate)
    if cratename in crates:
        crates.pop(cratename)
        await ctx.send("Done")
        with open("registeredcrates.json","w") as crate:
            json.dump(crates,crate,indent=4)
    else:
        await ctx.send("This crate doesn't exists")
    

@bot.command()
async def crates(ctx):
    f = open("registeredcrates.json","r")
    cratevar = json.load(f)
    f.close()
    last = 1
    embedVar = discord.Embed(title="Crates List",description="If you are interested to include your **Own Crates** , contact <@182864577657044993>", color=0x00FF00)
    for x in cratevar:
        embedVar.add_field(name=f"{last}. {x}",value="*--------------------------------*",inline=False)
        last += 1
        #for y in cratevar[x]:
        #    embedVar.add_field(name=y,value=cratevar[x][y])
            
    await ctx.send(embed=embedVar)


@bot.command(brief="Used to set giveaway channel")
@has_permissions(manage_roles=True, ban_members=True)
async def setchannel(ctx,channel_id):
    global defaultgiveawaychannelid
    try:
        channel_id = int(channel_id)
        defaultgiveawaychannelid = channel_id
        await ctx.send("Done")
    except Exception:
        await ctx.send("Error, check sintaxis")
            

@bot.command()
@has_permissions(manage_roles=True, ban_members=True)
async def setconf(ctx, mode, name):
    global limit
    global cratename
    global count
    name = name.lower().capitalize()
    if mode == "msgs":
        try:
            limit = int(name)
            count = 0
            await ctx.send("Limit changed to " + name)

        except Exception:
            await ctx.send("Please, use an integer for msgs limit")
    elif mode == "crate":
        try:
            with open("registeredcrates.json","r") as crate:
                crates = json.load(crate)
            if str(name) in crates:
                cratename = str(name)
                await ctx.send("Prize changed to " + name)
            else:
                await ctx.send("Use a valid cratename for this command")
        except Exception:
            await ctx.send("Please, use a string for crates")
    elif mode == "show":
        await ctx.send(f"Current config: Limit: {limit}, Crate: {cratename}")
    else:
        await ctx.send("Unknown mode")


@bot.command()
@has_permissions(manage_roles=True, ban_members=True)
async def remove(ctx,mode, user, name, quantity):
    
    serverid = str(ctx.message.guild.id)
    name = name.lower().capitalize()
    mode = mode.lower()
    user = user.replace("!","").replace("@","").replace("<","").replace(">","")
    try:
        if mode == "crate":
            with open("storage.json","r") as storage:
                data = json.load(storage)
            data[serverid][user][name] += -int(quantity)
            if data[serverid][user][name] < 0:
                data[serverid][user][name] = 0
            with open("storage.json","w") as storage:
                json.dump(data,storage,indent=4)
            await ctx.send(f"Crate **{quantity} {name}** deleted from <@{user}>")
        elif mode == "item":
            with open("inventory.json","r") as inventory:
                inv = json.load(inventory)
            inv[user][name] += -int(quantity)
            if inv[user][name] < 0:
                inv[user][name] = 0
            with open("inventory.json","w") as inventory:
                json.dump(inv,inventory,indent=4)
            await ctx.send(f"Item **{quantity} {name}** deleted from <@{user}>")
        else:
            await ctx.send("Unknown mode")
    except Exception:
        ctx.send("ERROR: Please, check your sintaxis and try again")

@remove.error
async def remove_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry <@{}>, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)

#@bot.command()
#async def withdraw(ctx):


@bot.command(pass_context=True)
@has_permissions(manage_roles=True, ban_members=True)
async def inventory(ctx, *args):
    userid = str(ctx.message.author.id)
    serverid = str(ctx.message.guild.id)
    temp = False
    #print(args[0])
    try:
        destiny = args[0].replace("!","").replace("@","").replace("<","").replace(">","")
        print(destiny)
        async for member in ctx.guild.fetch_members(limit=None):
            if int(destiny) == member.id:
                await ctx.send(embed=inventoryfunc(ctx,serverid,destiny))
                temp = True
        if not temp:
            await ctx.send(embed=inventoryfunc(ctx,serverid,userid))
    except Exception:
        print("Error")
        await ctx.send(embed=inventoryfunc(ctx,serverid,userid))

@inventory.error
async def inventory_error(ctx, error):
    userid = str(ctx.message.author.id)
    serverid = str(ctx.message.guild.id)
    if isinstance(error, MissingPermissions):
        await ctx.send(embed=inventoryfunc(ctx,serverid,userid))

@bot.command()
async def gift(ctx, cratename, user):
    cratename = cratename.lower().capitalize()
    userid = str(ctx.message.author.id)
    user = user.replace("!","").replace("@","").replace("<","").replace(">","")
    serverid = str(ctx.message.guild.id)
    with open("storage.json","r") as stor:
        data = json.load(stor)

    if cratename in data[serverid][userid] and data[serverid][userid][cratename] > 0: 
        if user not in data[serverid]:
            data[serverid][user] =  {}
            if cratename not in data[serverid][user]:
                data[serverid][user][cratename] = 1
            else:
                data[serverid][user][cratename] += 1
        elif cratename not in data[serverid][user]:
                data[serverid][user][cratename] = 1
        else:
                data[serverid][user][cratename] += 1
        data[serverid][userid][cratename] += -1
        with open("storage.json","w") as stor:
            json.dump(data,stor,indent=4)
        embedVar = discord.Embed(title="Success!! - "+ cratename,description=f"{ctx.author} just gave a **{cratename}** crate to <@{user}>!!**",color=0x00FF00)
        await ctx.send(embed=embedVar)
    else:
        embedVar = discord.Embed(title="Error",description=f"{ctx.author} looks like you don't have this crate! How unfortunate :c", color=0xFF0000)
        await ctx.send(embed=embedVar)
    
@bot.command(name="edit", pass_context=True)
@has_permissions(manage_roles=True, ban_members=True)
async def _editcrate(ctx,cratename,prizename,newprize):
    cratename = cratename.lower().capitalize()
    prizename = prizename.lower().capitalize()
    newprize = newprize.lower().capitalize()
    with open("registeredcrates.json","r") as crate:
        crates = json.load(crate)
    crates[cratename][newprize] = crates[cratename].pop(prizename) 
    with open("registeredcrates.json","w") as crate:
        json.dump(crates,crate,indent=4)
    
@_editcrate.error
async def editcrate_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry <@{}>, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)


@bot.command(name="add", pass_context=True)
@has_permissions(manage_roles=True, ban_members=True)
async def _givecrate(ctx,cratename,user):
    #print(user)

    serverid = str(ctx.message.guild.id)
    print(serverid)
    guild = ctx.guild
    print(guild)
    cratename = cratename.lower().capitalize()
    user = user.replace("<@!","").replace(">","")
    print("Yes")
    with open("registeredcrates.json","r") as crates:
        cratedata = json.load(crates)
    if cratename in cratedata:
        print("True")
        with open("storage.json","r") as storage:
            data = json.load(storage)
        #data[serverid][user][cratename] = 1
        if user not in data[serverid]:
            data[serverid][user] =  {}
            if cratename not in data[serverid][user]:
                data[serverid][user][cratename] = 1
            else:
                data[serverid][user][cratename] += 1
        elif cratename not in data[serverid][user]:
                data[serverid][user][cratename] = 1
        else:
                data[serverid][user][cratename] += 1
        with open("storage.json","w") as storage:
            json.dump(data,storage,indent=4)
            
        #else:
        #    data[serverid][user][cratename] += 1
        #    with open("storage.json","w") as storage:
        #        json.dump(data,storage,indent=4)
        embedVar = discord.Embed(title=cratename,description=f"<@{user}>, {ctx.author} just gave you this crate!!")
        with open("images.json", "r") as image:
            images = json.load(image)
        if cratename in images:
            embedVar.set_thumbnail(url=images[cratename])
        await ctx.send(embed=embedVar)
    else:
        await ctx.send("Sorry, this crate doesn't exist, use c!create first")

@_givecrate.error
async def givecrate_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry <@{}>, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)

@bot.command(name="update", pass_context=True)
@has_permissions(manage_roles=True, ban_members=True)
async def _updatecrate(ctx, cratename, prize, quantity):
    cratename = cratename.lower().capitalize()
    prize = prize.lower().capitalize()
    with open("registeredcrates.json", "r") as crates:
        data = json.load(crates)
    try:
        quantity = int(quantity)
        print("Generating a new prize...")
        if cratename in data:
            data[cratename][prize] = quantity
            with open("registeredcrates.json","w") as crates:
                json.dump(data,crates,indent=4)
                embedVar = discord.Embed(title=prize, description=f"A new prize!! Wonder who will be the first. Be quick before it goes out of stock", color=0x7CFC00)
                await ctx.send(embed = embedVar)
        else:
            await ctx.send("This crate doesn't exist! use c!create first!")
        
    except Exception:
        await ctx.send("Please provide an integer for the quantity")
    

@_updatecrate.error
async def updatecrate_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry @{}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)

@bot.command(name="create", pass_context=True)
@has_permissions(manage_roles=True, ban_members=True)
async def _addcrate(ctx, cratename):
    if type(cratename) == str:
        cratename = cratename.lower().capitalize()
        with open("registeredcrates.json","r") as cratedata:
            data = json.load(cratedata)

        data[cratename] = {}
        with open("registeredcrates.json","w") as cratedata:
            json.dump(data,cratedata,indent=4)
        await ctx.send("Done!")

    else:
        await ctx.send("You should provide a valid name to the crate (string)")

@_addcrate.error
async def addcrate_error(ctx, error):
    if isinstance(error, MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(manage_roles=True, ban_members=True)
async def info(ctx, crate):
    crate = crate.lower().capitalize()
    currentprizes = {}
    total = 0
    with open("registeredcrates.json", "r") as crates:
        data = json.load(crates)
    try:
        for x in data[crate]:
            total += data[crate][x] 
            currentprizes[x] = data[crate][x]

        #for x in currentprizes:
        #    currentprizes[x] = round((currentprizes[x] * 100) / total, 1)

        embedVar = discord.Embed(title=crate, description=f"The current prizes for this crate and it appearing % are:", color=0x7CFC00)
        for i, (k, v) in enumerate(currentprizes.items()):
            embedVar.add_field(name="{}. {}".format(i + 1,k), value=f"{v}", inline=False)
        await ctx.send(embed = embedVar)
        #for x in currentprizes:
        #    embedVar.add_field(name=x, value=currentprizes[x], inline=False)
        #await ctx.send(embed = embedVar)
    except Exception:
        embedVar = discord.Embed(title="Error", description=f"This crate doesn't exist, or maybe someone just decided to stole it.. Hmm.. suspicious", color=0xB10000)
        await ctx.send(embed = embedVar)
        

@bot.command(name="open")
#@in_channel(803720790184820758)
async def opencrate(ctx, crate):
    crate = crate.lower().capitalize()
    directory = "/root/cratebot/src"
    with open("storage.json","r") as storage:
        data = json.load(storage)
    

    serverid = str(ctx.message.guild.id)
    userid = str(ctx.message.author.id)
    if serverid in data and userid in data[serverid]: #Checks if the server and user are in the config
        try:
            if crate in data[serverid][userid] and data[serverid][userid][crate] > 0: #Checks if user has crate
                #Open the crate    
                prize = calcprize(crate)
                embedVar = discord.Embed(title=prize, description="Congrats! This is your prize!!", color=0x39CA44)
                with open("images.json","r") as image:
                    images = json.load(image)
                for x in images:
                    if x == crate:
                       embedVar.set_thumbnail(url=images[x])
                embedVar.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                await ctx.send(embed = embedVar)
                
                try:
                    for image in os.listdir(directory):
                        if image.endswith(".png"):
                            image = image.replace(".png","")
                            div = image.find("_")
                            if image[:div] in crate.lower() and image[div + 1:] in prize.lower():
                                print("True")
                                await ctx.send(file=discord.File(f'{directory}/{image}.png'))
                except Exception:
                    print("No image found")
                    pass
                
                data[serverid][userid][crate] += -1 
                with open("registeredcrates.json","r") as crates:
                    cratedata = json.load(crates)
                cratedata[crate][prize] += -1
                with open("registeredcrates.json","w") as crates:
                    json.dump(cratedata,crates,indent=4)
                with open("storage.json","w") as storage:
                    json.dump(data,storage,indent=4)
                with open("inventory.json","r") as inv:
                    inventory = json.load(inv)
                if userid not in inventory:
                    inventory[userid] = {}
                    inventory[userid][prize] = 1
                elif prize not in inventory[userid]:
                    inventory[userid][prize] = 1 
                else:
                    inventory[userid][prize] += 1
                with open("inventory.json","w") as inv:
                    json.dump(inventory,inv,indent=4)
            else:
                embedVar = discord.Embed(title="Error", description=f"<@{userid}> Sorry, you don't have this crate!", color=0xB10000)
                await ctx.send(embed = embedVar)
        except Exception:
            embedVar = discord.Embed(title="Error", description=f"This crate is empty! Who stole everything!?!? Tell this to the server admins, be quick!", color=0xB10000)
            await ctx.send(embed = embedVar)

    else:
        embedVar = discord.Embed(title="Error", description=f"<@{userid}> Sorry, you don't have this crate!", color=0xB10000)
        await ctx.send(embed = embedVar)
        data[serverid][userid] =  {}
        with open("storage.json","w") as storage:
            json.dump(data,storage,indent=4)

@bot.event
#@in_channel("803720790184820758")
async def on_message(message):
    global count
    global cratename
    global limit
    global defaultcommandschannelid
    global defaultgiveawaychannelid

    if message.channel.id == defaultcommandschannelid:
        await bot.process_commands(message)

    if message.channel.id == defaultcommandschannelid:
        user = str(message.author.id)
        if user != "803092771678191639":
            count += 1
            if count == limit:
                count = 0

                with open("storage.json","r") as storage, open("registeredcrates.json","r") as crates:
                    cratedata = json.load(crates)
                    data = json.load(storage)
                serverid = str(message.guild.id)
                if cratename in cratedata:
                    print("True")
                    with open("storage.json","r") as storage:
                        data = json.load(storage)
                    if user not in data[serverid]:
                        data[serverid][user] =  {}
                        if cratename not in data[serverid][user]:
                            data[serverid][user][cratename] = 1
                        else:
                            data[serverid][user][cratename] += 1
                    elif cratename not in data[serverid][user]:
                            data[serverid][user][cratename] = 1
                    else:
                            data[serverid][user][cratename] += 1
                with open("storage.json","w") as storage:
                    json.dump(data,storage,indent=4)
                giveawaychannel = bot.get_channel(defaultgiveawaychannelid)
                await giveawaychannel.send(f"WehKawKaw <@{user}>, you just won a {cratename} crate!!!")
@bot.event
async def on_ready():
    print("Ready")
    bot.loop.create_task(auto_api())
bot.run(TOKEN)
