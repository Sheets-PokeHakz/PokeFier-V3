from discord.ext import commands
from Main import OWNER_ID, POKETWO_ID


class CommandsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @bot.command()
        async def ping(ctx):
            await ctx.send("Pong!")
            await ctx.send(f"Latency : {round(bot.latency * 1000)}ms")

        @bot.command()
        async def incense(ctx, time: str, inter: str):
            if ctx.author.id != OWNER_ID:
                if time in ["30m", "1h", "3h", "1d"] and inter in ["10s", "20s", "30s"]:
                    await ctx.send(f"<@{POKETWO_ID}> incense buy {time} {inter} -y")

            else:
                await ctx.send(
                    f"Invalid Usage. Correct Usage : `{bot.command_prefix}incense <time> <interval>`"
                )
                await ctx.send("Time : 30m, 1h, 3h, 1d")
                await ctx.send("Interval : 10s, 20s, 30s")

        @bot.command()
        async def shardbuy(ctx, amt: int):
            if ctx.author.id == OWNER_ID:
                if amt > 0:
                    await ctx.send(f"<@{POKETWO_ID}> buy shards {amt}")
            else:
                await ctx.send(
                    f"Invalid Usage. Correct Usage : `{bot.command_prefix}shardbuy <amount>`"
                )

        @bot.command()
        async def channeladd(ctx, *channel_ids):
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

                if channel_id in bot.whitelisted_channels:
                    message += f"Channel ID : {channel_id} Is Already Whitelisted\n"
                else:
                    bot.whitelisted_channels.append(channel_id)
                    message += f"Channel ID : {channel_id} Whitelisted\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def channelremove(ctx, *channel_ids):
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

                if channel_id in bot.whitelisted_channels:
                    bot.whitelisted_channels = [
                        ch_id
                        for ch_id in bot.whitelisted_channels
                        if ch_id != channel_id
                    ]
                    message += f"Channel ID : {channel_id} Removed From Whitelist\n"
                else:
                    message += f"Channel ID : {channel_id} Is Not Whitelisted\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def languageadd(ctx, *languages):
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

                if language.lower() in bot.languages:
                    message += f"Language : {language} Is Already Added\n"
                else:
                    bot.languages.append(language.lower())
                    message += f"Language : {language} Added\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def languageremove(ctx, *languages):
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

                if language.lower() in bot.languages:
                    bot.languages = [lang for lang in bot.languages if lang != language]
                    message += f"Language : {language} Removed\n"
                else:
                    message += f"Language : {language} Is Not Added\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def blacklistadd(ctx, *pokemons):
            if not pokemons:
                await ctx.reply(
                    "`You Must Provide Atleast One Pokemon. Separate Multiple Pokemons With Spaces.`"
                )
                return

            message = "```\n"
            bot.blacklisted_pokemons = [
                pokemon_name.lower() for pokemon_name in bot.blacklisted_pokemons
            ]

            for pokemon in pokemons:
                if pokemon.lower() in bot.blacklisted_pokemons:
                    message += f"Pokemon: {pokemon} Is Already Blacklisted\n"
                else:
                    bot.blacklisted_pokemons.append(pokemon.lower())
                    message += f"Pokemon: {pokemon} Added To Blacklist\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def blacklistremove(ctx, *pokemons):
            if not pokemons:
                await ctx.reply(
                    "`You Must Provide Atleast One Pokemon. Separate Multiple Pokemons With Spaces.`"
                )
                return

            message = "```\n"
            bot.blacklisted_pokemons = [
                pokemon_name.lower() for pokemon_name in bot.blacklisted_pokemons
            ]

            for pokemon in pokemons:
                if pokemon.lower() in bot.blacklisted_pokemons:
                    bot.blacklisted_pokemons = [
                        poke for poke in bot.blacklisted_pokemons if poke != pokemon
                    ]
                    message += f"Pokemon : {pokemon} Removed From Blacklist\n"
                else:
                    message += f"Pokemon : {pokemon} Is Not Blacklisted\n"

            message += "```"
            await ctx.send(message)

        @bot.command()
        async def config(ctx):
            message = f"```PREFIX: {bot.command_prefix}\nOWNER_ID: {OWNER_ID}\n\nWHITELISTED_CHANNELS = {bot.whitelisted_channels}\nBLACKLISTED_POKEMONS={bot.blacklisted_pokemons}\n\nLANGUAGES = {bot.languages}```"
            await ctx.reply(message)

        @bot.command()
        async def say(ctx, *, message):
            if ctx.message.author.id != OWNER_ID:
                return
            else:
                await ctx.send(message)


async def setup(bot):
    await bot.add_cog(CommandsHandler(bot))
