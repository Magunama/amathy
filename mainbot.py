import discord
from discord.ext import commands
from utils.converters import MemberNotFound
import os
import json
import sys
import traceback
import re


async def get_prefix(bot, message):
    for p in bot.prefixes:
        if bool(re.match(p, message.content, re.I)):
            return message.content[:len(p)]
    if message.guild:
        custom_prefix = await bot.funx.get_prefix(message.guild.id)
        if custom_prefix and re.match(custom_prefix, message.content, re.I):
            return message.content[:len(custom_prefix)]
    return commands.when_mentioned(bot, message)


def attach_cogs(bot):
    cog_blacklist = []
    cog_list = os.listdir("cogs/")
    for extension in cog_list:
        if not ".py" in extension:
            continue
        extension = extension[:-3]
        if not extension in cog_blacklist:
            try:
                bot.load_extension(f"cogs.{extension}")
                print(f"{extension}", end="; ")
            except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                return
            except Exception as e:
                print(f"\n[ERR] Failed to load extension {extension}. Reason: {e}")


intents = discord.Intents.default()
intents.members = True
bot = commands.AutoShardedBot(command_prefix=get_prefix, intents=intents, chunk_guilds_at_startup=False,
                              fetch_offline_members=False, max_messages=1000, case_insensitive=True)
bot.remove_command('help')
bot.commands_statistics = dict()


@bot.event
async def on_ready():
    print('[INFO] Using account {} with id {}'.format(bot.user.name, bot.user.id))
    print("[INFO] Using discord.py version " + str(discord.__version__))
    bot.invite_link = "https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=2117463255".format(bot.user.id)
    print("Loaded plugins: ", end="")
    attach_cogs(bot)
    print("\n>>> Ready to play!")


@bot.event
async def on_shard_ready(shard):
    info = "\u001b[0m[\u001b[32;1mINFO\u001b[0m]"
    print(f'{info} Shard number {shard} is ready.')


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return

    # todo: recheck as this method might be wrong
    ignored = (commands.CommandNotFound, commands.CheckFailure)
    error = getattr(error, 'original', error)
    if type(error) in ignored:
        return

    # checking for guild field
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Sorry, this command can only be used in a guild!")

    # checking for missing permissions
    elif isinstance(error, commands.MissingPermissions):
        missing = ", ".join(error.missing_perms)
        await ctx.send(f"Sorry, you can't use this command as you're missing the following permissions:\n`{missing}`.")
    elif isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(error.missing_perms)
        await ctx.send(f"Sorry, it seems I'm missing the following permissions for this command:\n`{missing}`.")

    # checking for errors from converters
    elif isinstance(error, MemberNotFound):
        await ctx.send(error.message)

    # checking for nsfw marked channel
    elif isinstance(error, commands.NSFWChannelRequired):
        desc = "NSFW commands can only be used in NSFW marked channels."
        emb = discord.Embed(title="You can't use this here!", description=desc)
        emb.set_image(url="https://i.imgur.com/oe4iK5i.gif")
        await ctx.send(embed=emb)

    # checking for commands on cooldown
    elif isinstance(error, commands.CommandOnCooldown):
        cool_time = int(error.retry_after)
        cool_time = bot.funx.seconds2delta(cool_time)
        cool_time = bot.funx.delta2string(cool_time)
        cool_text = "[`{}`]\nYou are on cooldown! Try again in **{}**.".format(ctx.command.name, cool_time)
        await ctx.send(cool_text)

    # checking for unexpected errors
    elif hasattr(error, "__traceback__"):
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    if "errored" not in bot.commands_statistics:
        bot.commands_statistics["errored"] = 0
    bot.commands_statistics["errored"] += 1


@bot.event
async def on_command_completion(ctx):
    author = ctx.author
    guild = ctx.guild
    if not guild:
        guild = "DM"
    print(f"[INFO]{author} completed command {ctx.command} in {guild}")

    # todo: save in db
    if "completed" not in bot.commands_statistics:
        bot.commands_statistics["completed"] = 0
    bot.commands_statistics["completed"] += 1


@bot.event
async def on_raw_reaction_add(payload):
    # todo: optimization
    m_id = payload.message_id
    g_id = payload.guild_id
    u_id = payload.user_id
    c_id = payload.channel_id
    emoji = payload.emoji
    if not u_id == bot.user.id:
        c_obj = bot.get_channel(c_id)
        if c_obj:
            try:
                m_obj = await c_obj.fetch_message(m_id)
            except Exception as e:
                m_obj = None
            if m_obj:
                if m_obj.author == bot.user:
                    folder = "data/reactrole/{}".format(g_id)
                    path = "{}/reactrole.json".format(folder)
                    if not os.path.isfile(path):
                        reactrole = {}
                    else:
                        with open(path, 'r') as fp:
                            reactrole = json.load(fp)
                    if str(m_id) in reactrole:
                        options = reactrole[str(m_id)]["opt"]
                        for i in range(0, len(options)):
                            if str(emoji) == options[i][0]:
                                role_id = options[i][1].replace("<@&", "").replace(">", "")
                                g_obj = c_obj.guild
                                member = g_obj.get_member(u_id)
                                role_obj = g_obj.get_role(int(role_id))
                                await member.add_roles(role_obj)
                                break


@bot.event
async def on_guild_join(guild):
    # time_utc = datetime.datetime.utcnow()
    # utc_diff = 3  # Ro = utc +3
    # time_result = time_utc + datetime.timedelta(hours=utc_diff)
    # time_result = time_result.strftime("%Y-%m-%d %H:%M:%S")
    # ownname = str(guild.get_member(guild.owner_id))
    # script = "INSERT INTO serverlist(guild_id, owner_id, owner_name, first_join, anc_chan_id, join_date, `left`) VALUES (\"{}\", \"{}\", \"{}\", \"1\", \"not_set\", \"{}\", \"0\") ON DUPLICATE KEY UPDATE anc_chan_id=\"not_set\", join_date=\"{}\""
    # await bot.funx.run_cq(script.format(guild.id, guild.owner_id, ownname, time_result, time_result), script.format(guild.id, guild.owner_id, "[Bad_Name]", time_result, time_result))

    botobj = guild.get_member(bot.user.id)
    chanlist = guild.channels
    print("Joined new guild {} with {} members. --- Now sending on_join message...".format(guild.name, guild.member_count))
    jointext = "[EN] Hello, everyone! I'm **Amathy**, your new bot. I'm __good__ at **playing music** and I have fun games. You can find my command list by using `ama help`. Please be patient with me as I am currently __under development__. For more information and bug reports, contact my developers on my __support server__, found in **the link section** of the help command. Thank you for choosing me~~ :smile:"
    for k in chanlist:
        if isinstance(k, discord.TextChannel):
            perms = k.permissions_for(botobj)
            if perms.send_messages:
                await k.send(jointext)
                break
    print("On_join message successfully sent to {}".format(guild.name))
    await bot.cogs["WebHook"].send_on_guild_join(guild)


@bot.event
async def on_guild_remove(guild):
    print("Left guild: ", guild.name)
    # script = "UPDATE serverlist SET `left`=\"1\" WHERE guild_id=\"{}\""
    # await bot.funx.run_cq(script.format(guild.id))
    await bot.cogs["WebHook"].send_on_guild_remove(guild)


@bot.event
async def on_member_join(member):
    pass


@bot.event
async def on_member_leave(member):
    pass


@bot.event
async def on_member_update(before, after):
    pass
