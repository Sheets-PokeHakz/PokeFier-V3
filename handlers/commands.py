import time
import random
from discord.ext import commands
from main import OWNER_ID, POKETWO_ID, DELAY


class CommandsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        message = """
        **Commands**
`shard` - To Buy Shards
`help` - To View This Message
`incense` - To Start The Incense

`say` - To Make The Bot Say Something
`ping ` - To Check If The Bot Is Online
`trade` - To Request A Trade With A User
`config` - To View The Current Configuration
`solved` - To Confirm That The Captcha Was Solved
        
`channeladd` - To Add A Channel To The Whitelist
`channelremove` - To Remove A Channel From The Whitelist
        
`blacklistadd` - To Add A Pokemon To The Blacklist
`blacklistremove` - To Remove A Pokemon From The Blacklist
        
`languageadd` - To Add A Language To The Language List
`languageremove` - To Remove A Language From The Language List
        
        """

        time.sleep(random.choice(DELAY))
        await ctx.send(message)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")
        await ctx.send(f"Latency : {round(self.bot.latency * 1000)}ms")

    @commands.command()
    async def incense(self, ctx, time: str, inter: str):
        if ctx.author.id != OWNER_ID:
            if time in ["30m", "1h", "3h", "1d"] and inter in ["10s", "20s", "30s"]:
                await ctx.send(f"<@{POKETWO_ID}> incense buy {time} {inter} -y")

        else:
            await ctx.send(
                f"Invalid Usage. Correct Usage : `{self.bot.command_prefix}incense <time> <interval>`"
            )
            await ctx.send("Time : 30m, 1h, 3h, 1d")
            await ctx.send("Interval : 10s, 20s, 30s")

    @commands.command()
    async def channeladd(self, ctx, *channel_ids):
        if not channel_ids:
            await ctx.reply(
                "`You Must Provide Atleast One Channel ID. Separate Multiple IDs With Spaces.`"
            )
            return

        message = "```\n"

        for channel_id_str in channel_ids:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await ctx.reply(
                    f"Invalid Channel ID : `{channel_id_str}`. Please Provide A Valid Numeric Channel ID."
                )
                continue

            if channel_id in self.botwhitelisted_channels:
                message += f"Channel ID : {channel_id} Is Already Whitelisted\n"
            else:
                self.botwhitelisted_channels.append(channel_id)
                message += f"Channel ID : {channel_id} Whitelisted\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def channelremove(self, ctx, *channel_ids):
        if not channel_ids:
            await ctx.reply(
                "`You Must Provide Atleast One Channel ID. Separate Multiple IDs With Spaces.`"
            )
            return

        message = "```\n"

        for channel_id_str in channel_ids:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await ctx.reply(
                    f"Invalid Channel ID : `{channel_id_str}`. Please Provide A Valid Numeric Channel ID."
                )
                continue

            if channel_id in self.botwhitelisted_channels:
                self.botwhitelisted_channels = [
                    ch_id
                    for ch_id in self.botwhitelisted_channels
                    if ch_id != channel_id
                ]
                message += f"Channel ID : {channel_id} Removed From Whitelist\n"
            else:
                message += f"Channel ID : {channel_id} Is Not Whitelisted\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def languageadd(self, ctx, *languages):
        if not languages:
            await ctx.reply(
                "`You Must Provide Atleast One Language. Separate Multiple Languages With Spaces.`"
            )
            return

        message = "```\n"
        valid_languages = ["english", "french", "german", "japanese"]

        for language in languages:
            if language.lower() not in valid_languages:
                await ctx.reply(
                    f"Invalid Language : `{language}`. Please Provide A Valid Language Used By Poketwo."
                )
                continue

            if language.lower() in self.botlanguages:
                message += f"Language : {language} Is Already Added\n"
            else:
                self.botlanguages.append(language.lower())
                message += f"Language : {language} Added\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def languageremove(self, ctx, *languages):
        if not languages:
            await ctx.reply(
                "`You Must Provide Atleast One Language. Separate Multiple Languages With Spaces.`"
            )
            return

        message = "```\n"
        valid_languages = ["english", "french", "german", "japanese"]

        for language in languages:
            if language.lower() not in valid_languages:
                await ctx.reply(
                    f"Invalid Language : `{language}`. Please Provide A Valid Language Used By Poketwo."
                )
                continue

            if language.lower() in self.botlanguages:
                self.botlanguages = [
                    lang for lang in self.botlanguages if lang != language
                ]
                message += f"Language : {language} Removed\n"
            else:
                message += f"Language : {language} Is Not Added\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def blacklistadd(self, ctx, *pokemons):
        if not pokemons:
            await ctx.reply(
                "`You Must Provide Atleast One Pokemon. Separate Multiple Pokemons With Spaces.`"
            )
            return

        message = "```\n"
        self.botblacklisted_pokemons = [
            pokemon_name.lower() for pokemon_name in self.botblacklisted_pokemons
        ]

        for pokemon in pokemons:
            if pokemon.lower() in self.botblacklisted_pokemons:
                message += f"Pokemon: {pokemon} Is Already Blacklisted\n"
            else:
                self.botblacklisted_pokemons.append(pokemon.lower())
                message += f"Pokemon: {pokemon} Added To Blacklist\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def blacklistremove(self, ctx, *pokemons):
        if not pokemons:
            await ctx.reply(
                "`You Must Provide Atleast One Pokemon. Separate Multiple Pokemons With Spaces.`"
            )
            return

        message = "```\n"
        self.bot.blacklisted_pokemons = [
            pokemon_name.lower() for pokemon_name in self.bot.blacklisted_pokemons
        ]

        for pokemon in pokemons:
            if pokemon.lower() in self.bot.blacklisted_pokemons:
                self.bot.blacklisted_pokemons = [
                    poke for poke in self.bot.blacklisted_pokemons if poke != pokemon
                ]
                message += f"Pokemon : {pokemon} Removed From Blacklist\n"
            else:
                message += f"Pokemon : {pokemon} Is Not Blacklisted\n"

        message += "```"
        await ctx.send(message)

    @commands.command()
    async def config(self, ctx):
        message = f"```PREFIX: {self.bot.command_prefix}\nOWNER_ID: {OWNER_ID}\n\nWHITELISTED_CHANNELS = {self.bot.whitelisted_channels}\nBLACKLISTED_POKEMONS={self.bot.blacklisted_pokemons}\n\nLANGUAGES = {self.bot.languages}```"
        await ctx.reply(message)

    @commands.command()
    async def say(self, ctx, *, message):
        if ctx.message.author.id != OWNER_ID:
            return
        else:
            await ctx.send(message)


async def setup(bot):
    await bot.add_cog(CommandsHandler(bot))
