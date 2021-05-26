#*******************************************************************************
# Programmer: Reebal Karaki
#
# Class: N/A 
#
# Programming Assignment: DiscordHelper
#
# Last updated: 5/26/2021                                                      
#                                                                             
# Description: DiscordHelper started as a summer project meant to make discord meetings more enjoyable. The
#              discord bot can play music, share memes, generate random numbers, tell jokes, and perform basic
#              mathematical operations.                   
#*******************************************************************************


#imports
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
import random
import json
import os
from discord.utils import get
import youtube_dl
from random import randint
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
from discord.voice_client import VoiceClient

client = commands.Bot(command_prefix='!')#prefix for all commands
TOKEN='ODQxNzgwMzA2Mzk0NjExNzEy.YJrvAA.V4rH5yqIszEjZywEFXF79OI4KFo'#Defining the token to run the bot


#Event for when the bot is ready
@client.event
async def on_ready():
    print("Bot is online")
    print(client.user.name)
    print(client.user.id)
    print('---------------')
    await client.change_presence(activity=discord.Game("Music"))#Adding a status to the bot


#Event for someone joining the server
@client.event
async def on_member_join(member):
    print(f"{member} has joined the server!")

#Event for someone leaving the server
@client.event
async def on_member_leave(member):
    print(f"{member} has left the server.")

#Command for hello
@client.command(aliases =["HI","Hi","Hello","Hey","HEY","hello"])
async def hi(ctx):
    HelloResponse=["Hi!","Hello!","Hey!", "Hello there!"]
    await ctx.send(f"{random.choice(HelloResponse)}")

#Command to find bot's latency
@client.command()
async def ping(ctx):
    await ctx.send(f"Ping: {round(client.latency *1000)}ms")

#Command to generate random number
@client.command(aliases =["Random","random","Rand"])
async def rand(ctx, amount1=0,amount2=1000):
    await ctx.send(f"Random number is {random.randint(amount1, amount2)}!")

#Command to roll Dice
@client.command(aliases =["Diceroll","rolldice","diceroll","Rolldice","Dice"])
async def dice(ctx):
    await ctx.send(f"Dice roll is {random.randint(1,6)}!")

#Command to change nickname
@client.command(pass_content=True)
async def changename(ctx,member: discord.Member, nick):
    await member.edit(nick=nick)
    await ctx.send(f"Nickname has been changed to {member.mention}")

#Command to give add numbers
@client.command()
async def add(ctx,numb1: int,numb2:int):
   await ctx.send(numb1+numb2)

#Command to give subtract numbers
@client.command()
async def subtract(ctx,numb1: int,numb2:int):
   await ctx.send(numb1-numb2)

#Command to give divide numbers
@client.command()
async def divide(ctx,numb1: int,numb2:int):
   await ctx.send(numb1/numb2)

#Command to give multiply numbers
@client.command()
async def multiply(ctx,numb1: int,numb2:int):
   await ctx.send(numb1*numb2)

#Command to join channel
@client.command(pass_content=True)
async def join(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
         channel = ctx.author.voice.channel
         await channel.connect()
         await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You are not connected to a voice channel.")
        return

#Required ytdl settings
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


#Command to play music
@client.command(aliases=["p","Play","P"])
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to end music
@client.command(name='stop')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

#Command to resume music after pausing
@client.command(name='resume')
async def resume(ctx):
   # Checks if music is paused and resumes it, otherwise sends the player a message that nothing is playing
   try:
       ctx.voice_client.resume()
   except:
       await ctx.send(f"{ctx.author.mention} i'm not playing music at the moment!")

#Command to pause music
@client.command()
async def pause( ctx):
        # Checks if music is playing and pauses it, otherwise sends the player a message that nothing is playing
        try:
            ctx.voice_client.pause()
        except:
            await ctx.send(f"{ctx.author.mention} i'm not playing music at the moment!")

#Command to change volume
@client.command()
async def volume(ctx, volume: int):

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

#Command to leave channel
@client.command(pass_content=True)
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(f"Left {channel}")
    else:
        await ctx.send("I am not in a voice channel")
    
#Command to play fortnitecard sound
@client.command(name='fortnitecard')
async def fortnitecard(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    url="https://youtu.be/Bpq36HqaPlI"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to play ps2 sound
@client.command()
async def ps2(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    url="https://youtu.be/w5SoqjQR6eU"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to play elevator music
@client.command()
async def elevatormusic(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    url="https://youtu.be/VBlFHuCzPgY"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to play fortnite music
@client.command()
async def fortnitemusic(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    url="https://youtu.be/tCng3Wu6Zo0"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to play sus sound
@client.command(name='sus')
async def sus(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    url="https://youtu.be/8UFqY9ad8x8"
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: {}'.format(player.title))

#Command to show all commands
@client.command(aliases=["Commands","Help"])
async def commands(ctx):
    embed=discord.Embed(
        title="Commands",
        description="Below are the commands for the DiscordHelper! Use the **!** as a prefix for the commands",
        colour=discord.Colour.dark_blue()
        )
    embed.add_field(name="Utility Commands",value="!hi\n!clear\n!joke\n!kick\n!ping\n!rand\n!dice\n!subtract\n!multiply\n!divide\n!coinflip\n!changename\n!fact\n!add\n!commmands", inline=True)
    embed.add_field(name="Music Commands",value="!join\n!leave\n!play\n!stop\n!volume\n!resume\n!pause", inline=True)
    embed.add_field(name="Sound Commands",value="!sus\n!fortnitecard\n!ps2\n!elevatormusic\n!fortnitemusic", inline=True)
    embed.add_field(name="Meme Commands",value="!monkey\n!doge\n!walter\n!cat", inline=True)
    await ctx.send(embed=embed)
#Command to send funny image of monkey
@client.command(aliases= ["Monkey","Monke","monke"])
async def monkey(ctx):
    images=[
        'https://i.redd.it/lrpkqge1lz441.jpg',
        'https://i.redd.it/qlik8bue8lf51.jpg',
        'https://fmobserver.com/wp-content/uploads/2019/08/baboon-mouse-picture.png',
        'https://i.redd.it/r2rn2ub614461.jpg',
        'https://i.kym-cdn.com/entries/icons/original/000/036/684/bananacover.jpg',
        'https://i.ytimg.com/vi/2_9SeWEyK0Y/maxresdefault.jpg',
        'https://i.redd.it/erc0d2vba9561.jpg',
        'https://i.ytimg.com/vi/fxE-FCxnRA0/maxresdefault.jpg',
        'https://i.pinimg.com/originals/40/12/c0/4012c000cbbe1f0090719b28568c0ed2.png',
        'https://i.ytimg.com/vi/dN-B82WfNeI/maxresdefault.jpg']
    embeddedMonkey= discord.Embed(color=discord.Colour.dark_grey())
    random_image= random.choice(images)
    embeddedMonkey.set_image(url=random_image)
    await ctx.send(embed= embeddedMonkey)

#Command to send image of Doge
@client.command(aliases= ["dog","Dog","Doge"])
async def doge(ctx):
    embeddedDoge= discord.Embed(color=discord.Colour.dark_teal())
    embeddedDoge.set_image(url= 'https://dogecoin.org/static/11cf6c18151cbb22c6a25d704ae7b313/dd8fa/doge-main.jpg')
    await ctx.send(embed= embeddedDoge)

#Command to send image of Walter
@client.command(aliases= ["Walter"])
async def walter(ctx):
    embeddedWalter= discord.Embed(color=discord.Colour.lighter_gray())
    embeddedWalter.set_image(url= 'https://i.kym-cdn.com/entries/icons/original/000/027/707/henry.png')
    await ctx.send(embed= embeddedWalter)

#Command to send image of Cat
@client.command(aliases= ["Cat"])
async def cat(ctx):
    embeddedCat= discord.Embed(color=discord.Colour.blurple())
    images=['https://i.kym-cdn.com/photos/images/newsfeed/001/471/100/0e5.jpg','https://i.kym-cdn.com/entries/icons/original/000/026/027/halfiecat.png']
    random_image=random.choice(images)
    embeddedCat.set_image(url= random_image)
    await ctx.send(embed= embeddedCat)

#Command to send image of Walter
@client.command(aliases= ["Stonk","Stonks","stonk"])
async def stonks(ctx):
    embeddedStonks= discord.Embed(color=discord.Colour.purple())
    embeddedStonks.set_image(url= 'https://i.kym-cdn.com/entries/icons/original/000/029/959/Screen_Shot_2019-06-05_at_1.26.32_PM.jpg')
    await ctx.send(embed= embeddedStonks)

#Command to flip a coin
@client.command(aliases =["coinflip","Flipcoin","Coinflip","Coin","flipcoin"])
async def coin(ctx):
    CoinFlip=random.randint(0, 100)
    resultFlip="NULL"

    if(CoinFlip%2==0):
        resultFlip="Heads"
    else:
        resultFlip="Tails"

    await ctx.send(f"{resultFlip}!")

#Command to clear chat, default parameters are 5
@client.command(aliases =["Clear","CLEAR","CLear","CLEar"])
async def clear(ctx,amount=5):
    await ctx.channel.purge(limit= amount+1)#I put a plus one since the message you send counts

#Command to make jokes
@client.command(aliases =["joke?", "jokes","Joke","JOke","Jokes","JOkes"])
async def joke(ctx):
    jokes=["How do celebrities stay cool? They have many fans.","What kind of egg did the evil chicken lay? A deviled egg.",
           "Why did the coach go to the bank? To get his quarter back.","What did the fisherman say to the magician? Pick a cod, any cod.",
           "What do you call a fake noodle? An impasta.","How do you organize a space party? You planet.",
           "Which is faster, hot or cold? Hot, because you can catch a cold.","Why are skeletons so calm? Because nothing gets under their skin.",
           "What did one ocean say to the other ocean? Nothing, they just waved.","Why can't a leopard hide? Because he's always spotted.",
           "How many tickles does it take to make an octopus laugh? 10 tickles.","",
           "What do you call an illegally parked frog? Toad.","Where do baby cats learn to swim? The kitty pool.",
           "Why are spiders so smart? They can find everything on the web.","Can February March? No, but April May!",
           "How can you tell it's a dogwood tree? From the bark.","I could tell a joke about pizza, but it's a little cheesy.",
           "Don't trust atoms. They make up everything!","What's an astronaut's favorite part of a computer? The space bar.",
           "What rock group has four men that don't sing? Mount Rushmore.","How does a penguin build its house? Igloos it together!",
           "What do you call a lazy kangaroo? Pouch potato.","The rotation of the earth really makes my day.",
           "What's the best part about living in Switzerland? I don't know, but the flag is a big plus.",
           "Why did the invisible man turn down the job offer? He couldn't see himself doing it."]
    await ctx.send(random.choice(jokes))

#Command to give random facts
@client.command(aliases=["trivia","facts","Fact","Facts"])
async def fact(ctx):
    facts=["Polar bear fur is actually clear, and their skin is black.","Baby flamingos are born grey, not pink.","A woodpecker’s tongue actually wraps all the way around its brain, protecting it from damage when it’s hammering into a tree.",
" A shrimp’s heart is located in its head."," Elephants suck on their trunks for comfort.","Anteaters have no teeth.","Nine-banded armadillos always have quadruplets, and they’re always identical.",
"A flock of flamingos is called a flamboyance.", "Hippos and horses are actually distant relatives.","All clownfish are born male.","In the UK, The Queen legally owns all unmarked swans.",
"To keep from drifting apart, sea otters hold hands while they sleep.", "Goats have accents.","Dolphins give names to each other.","Gorillas can catch human colds — you’re probably still safe to go to the zoo with the sniffles, though.",
"Forget bald eagles. The turkey was once almost named the national bird.","A group of owls is called a parliament.","There are 32 muscles in a cat’s ear.""Snails can regenerate their eyes.",
"Want to know if your pet turtle is a boy or girl? Listen closely! Female turtles hiss and male turtles grunt.", "A starfish can turn its stomach inside out.","French Poodles are actually from Germany.",
"Seahorses mate for life and can often be seen holding each other’s tales.","A group of porcupines is called a prickle.","Andrew Jackson’s parrot had to be removed from his funeral because it wouldn’t stop swearing. Polly wants her mouth washed out.",
"Sloths can hold their breaths for up to 40 minutes.","Henry VIII knighted all four of his “Grooms of Stool” — the people in charge of wiping his butt for him.","Jeannette Rankin was elected to Congress four years before women could even vote.",
"Women couldn’t apply for credit at a bank until 1974.","Before the invention of modern false teeth, dentures were commonly made from the teeth of dead soldiers.","You can’t hum while plugging your nose.",
"In ancient Egypt, servants were smeared with honey so flies would flock to them instead of the pharaoh.","It was once considered sacrilegious to use a fork.","More than 100 baseballs are used during a typical professional baseball game.",
"Abe Lincoln was a champion wrestler. He was also a licensed bartender. Maybe they should call him an “Abe of all trades.”"," George Washington owned a whiskey distillery.",
"More than two percent of the American population was killed during the Civil War.","Joseph Stalin used to have people removed from photos after they died or were removed from office.",
"Since 1945, all British tanks have been equipped with the necessary items for making tea.","Pope Gregory IV once declared war on cats because he believed Satan used black cats. His declaration lead to the mass extermination of cats.",
"That lack of cats led to a rat infestation which led to the spread of the plague.","John Adams was the first president to live in the White House.","Go to bed! Chernobyl, the Exxon Valdez Oil Spill, and the Challenger explosion have all been attributed to a lack of sleep.",
"The average person living in Sweden eats about 22 pounds of chocolate a year.","While the Wright Brothers are famous as a pair, they actually only flew together once. They promised their father they’d always fly separately.",
"Montana has three times as many cows as it does people.","Parts of the Great Wall of China were made with sticky rice.","Ninety percent of the world’s population lives above the equator.","Finland has more saunas than cars.",
"Sixty percent of the World’s lakes (three million total) are located in Canada.","Virginia is the only state that has the same state flower and state tree, the Dogwood.","Think before you season. In Egypt, it’s considered incredibly rude to salt food that has been served to you.",
"Ninety percent of Libya is desert.","The height of the Eiffel Tour can vary up to six inches, depending on the temperature.","Spend too much on drinks when you eat out? A small town in Italy actually has a fountain that serves free wine.",
"Pilots and their co-pilots are required to eat different meals before flights so that they don’t both end up with food poisoning.","Roughly 600 Parisians work at the Eiffel Tower each day.",
"Want to go to Rome? Which one? There’s a city named Rome on six out of seven continents. (You really dropped the ball, Antarctica.)","When visiting Key West, you’re actually closer to Havana than you are to Miami.",
"Mary, of “Mary Had A Little Lamb” fame, was a real person and the song is based on a true story.","“Happy Birthday” was the first song ever played on Mars. Mars Rover Curiosity played the song to itself on its first anniversary on the planet.",
"While listening to music, your heart can sync to the rhythm.","President Nixon was an accomplished musician. He played five instruments, including the accordion.","Got a song stuck in your head? That’s called an “earworm.”",
"None of The Beatles could actually read music.","However, George Harrison could reportedly play 26 instruments.", "Barry Manilow did not, in fact, write “I Write The Songs.”","Metallica is the only band to perform on all seven continents.",
"Most department stores tend to play slower music, in order to slow down customers and keep them shopping longer. The opposite is true for restaurants.","Monaco’s orchestra is bigger than its army.",
"A concert promoter once sold a thousand tickets to a Spice Girls concert in Hawaii that was never actually booked. Maybe that’s where they got the idea for Fyre Fest.","Leo Fender, the inventor of the Stratocaster and the Telecaster, couldn’t play guitar.",
"In 2016, Mozart sold more albums than Beyoncé.","During a fundraiser for Hurricane Katrina relief efforts, someone donated $35,000 so that VH1 Classic would have to play “99 Luftballons” on repeat for an entire hour.",
"“A Boy Named Sue” wasn’t written by Johnny Cash. Shel Silverstein wrote it.","In 2015, Belfast police used ice cream truck music to deter teenage rioters.","Despite taking about three hours to play out, the average baseball game only has about 18 minutes of active playing time.",
"Gatorade was named after the University of Florida Gators.","China didn’t win its first Olympic medal until 1984.","The average golf ball has 336 dimples.","Tennis was originally played with bare hands.",
"The Cleveland Browns are the only team to neither play in or host a Super Bowl.","Wilt Chamberlain is in the Volleyball Hall of Fame.","Some golf balls are filled with honey.","MLB umpires are required to wear black underwear in case they split their pants.",
"Bo Jackson refused the teams that originally tried to draft him in both baseball and football.","Both volleyball and basketball were invented in Massachusetts.","Michael Jordan and the Chicago Bulls once went eight seasons (starting in 1990) without a three-game losing streak.",
"NFL refs also get Super Bowl rings.","President Hubert Hoover invented a game called “Hooverball” which was a cross between tennis and volleyball and was played with a medicine ball.","Only one city has won three major championships in one year. In 1935, the Detroit Lions won the Super Bowl, the Tigers won the world series, and the Red Wings won the Stanley Cup.",
"Tomatoes have more genes than humans.","We’re one to two centimeters taller in the morning than at night.","One quarter of all our bones are in our feet.","The human body contains enough fat to make about seven bars of soap.","You can’t lick your elbow.","You can’t tickle yourself.",
"By the time we die, we’ll have spent roughly a year sitting on the toilet.","You are always looking at your nose; your brain just chooses to ignore it.","Astronauts can grow up to two inches taller while they’re in space.","Some blood vessels in a blue whale are actually big enough for humans to swim through.",
"We’re the only species known to blush.","You only breathe out of one nostril at a time.","Babies are born with more bones than adults. (Babies have 300 bones while adults only have 206.)","Most newborns lose all the hair they were born with by the time they’re six months old.",
"It’s impossible to burp in space.","Everyone has their own unique smell, except identical twins.","Thumbs have their own pulse.","Goosebumps developed to make our ancestors’ hair stand up, making them appear more threatening to predators.","A sneeze shoots through the air at 100 miles per hour, sending 10,000 germs flying."
"Know how a bat or whale uses echolocation to communicate? Humans are also capable of echolocation.","Stomach acid is strong enough to dissolve metal.","The longest hiccuping spell lasted a whopping 68 years."]
    await ctx.send(random.choice(facts))

#Command to kick users
@client.command()
@has_permissions(administrator = True) #Making sure the users have permission to kick members
async def kick(ctx, member: discord.Member,*,reason = None ):
    await member.kick(reason=reason)
    await ctx.send(f"{member} has been kicked")
   
#We can now run the bot using its token
client.run(TOKEN)