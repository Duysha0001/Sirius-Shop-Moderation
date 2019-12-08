import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import os

client=commands.Bot(command_prefix="'")
bot_id=583016361677160459
db_id=653160213607612426
mute_role_name="Мут"

client.remove_command('help')

def number(s):
    check=True
    nums=[str(i) for i in range(10)]
    for letter in s:
        if not letter in nums:
            check=False
            break
    return check

@client.event
async def on_ready():
    global bot_id
    print("Ready to moderate")
    if "583016361677160459"!=str(bot_id):
        print("Code isn't currently running Sirius Shop Bot")

#========Minor tools=======
def to_raw(data_list):
    out=""
    for elem in data_list:
        out+=str(elem)+";"
    return out

def to_list(data_raw):
    out=[]
    elem=""
    for letter in data_raw:
        if letter==";":
            out.append(elem)
            elem=""
        else:
            elem+=letter
    return out
    
#========Databse functions=======
async def post_data(folder, key_word, data_list):
    global db_id
    db_server=client.get_guild(db_id)
    
    data_raw=to_raw(data_list)
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        await db_server.create_text_channel(folder)
    folder = discord.utils.get(db_server.channels, name=folder)
    check=0
    async for file in folder.history(limit=100):
        if file.content==f"{key_word};{data_raw}":
            check=1
            break
    if check==0:
        await folder.send(f"{key_word};{data_raw}")
    
async def get_data(folder, key_word):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        data=None
        async for file in folder.history(limit=100):
            data_list=to_list(file.content)
            if data_list[0]==key_word:
                data=data_list[1:len(data_list)]
                break
        if data==None:
            return "Error"
        else:
            return data

async def edit_data(folder, key_word, edit_list):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        data=None
        async for file in folder.history(limit=100):
            data_list=to_list(file.content)
            if data_list[0]==key_word:
                data=file
        if data==None:
            return "Error"
        else:
            edit_raw=to_raw(edit_list)
            await data.edit(content=f"{key_word};{edit_raw}")
            
async def delete_data(folder, key_word):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        data=None
        async for file in folder.history(limit=100):
            data_list=to_list(file.content)
            if data_list[0]==key_word:
                data=file
        if data==None:
            return "Error"
        else:
            await data.delete()
            
async def delete_folder(folder):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        await folder.delete()
        
async def get_folder(folder):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        folder_list=[]
        prev_id=None
        async for file in folder.message_history(limit=100):
            if file.id==prev_id:
                break
            else:
                prev_id=file.id
                folder_list.append(to_list(file.content))
        return folder_list

#============Bot async funcs==========
async def has_helper(user, guild):
    mmcheck=False
    if guild.owner.id==user.id:
        mmcheck=True
    for r in user.roles:
        if r.permissions.administrator or r.permissions.manage_messages:
            mmcheck=True
    return mmcheck

async def has_admin(user, guild):
    mmcheck=False
    if guild.owner.id==user.id:
        mmcheck=True
    for r in user.roles:
        if r.permissions.administrator:
            mmcheck=True
    return mmcheck

async def can_kick(user, guild):
    mmcheck=False
    if guild.owner.id==user.id:
        mmcheck=True
    for r in user.roles:
        if r.permissions.administrator or r.permissions.kick_members:
            mmcheck=True
    return mmcheck

async def can_ban(user, guild):
    mmcheck=False
    if guild.owner.id==user.id:
        mmcheck=True
    for r in user.roles:
        if r.permissions.administrator or r.permissions.ban_members:
            mmcheck=True
    return mmcheck

async def glob_pos(user):
    pos=0
    for r in user.roles:
        if r.position>pos:
            pos=r.position
    return pos

async def post_log(guild, log_embed):
    channel_id=await get_data("log-channels", str(guild.id))
    if not channel_id=="Error":
        channel_id=int(channel_id[0])
        channel=discord.utils.get(guild.channels, id=channel_id)
        if channel in guild.channels:
            await channel.send(embed=log_embed)
    
async def setup_mute(guild):
    global mute_role_name
    mute_role=discord.utils.get(guild.roles, name=mute_role_name)
    if not mute_role in guild.roles:
        await guild.create_role(name=mute_role_name, permissions=discord.Permissions.none())
        mute_role=discord.utils.get(guild.roles, name=mute_role_name)
    for channel in guild.text_channels:
        await channel.set_permissions(mute_role, send_messages=False)
    for channel in guild.voice_channels:
        await channel.set_permissions(mute_role, speak=False)
    
        
#=============Commands=============
@client.command()
async def help(ctx, *, cmd_name=None):
    #if cmd_name==None:
    adm_help_list=("1) **'mute [**Участник**] [**Время**] [**Причина**]**\n"
                   "2) **'unmute [**Участник**]**\n"
                   "3) **'kick [**Участник**] [**Причина**]**\n"
                   "4) **'ban [**Участник**] [**Причина**]**\n"
                   "5) **'unban [**Участник**]**\n"
                   "6) **'set_log_channel [**ID канала**]** - *настраивает канал для логов*\n"
                   "7) **'remove_log_channel [**ID канала**]** - *отвязывает канал от логов*\n"
                   "8) **'set_mute_role** - *перенастраивает роль мута в каждом канале*")
    user_help_list=""
    
    help_msg=discord.Embed(
        title="Help menu",
        color=discord.Color.from_rgb(201, 236, 160)
        )
    help_msg.add_field(name="**Moderator commands**", value=adm_help_list, inline=False)
    
    await ctx.send(embed=help_msg)

@client.command()
async def set_log_channel(ctx, channel_id):
    channel_IDs=[str(c.id) for c in ctx.guild.channels]
    if not channel_id in channel_IDs:
        await ctx.send("Канал не найден")
    else:
        channel=discord.utils.get(ctx.guild.channels, id=int(channel_id))
        await post_data("log-channels", str(ctx.guild.id), [channel_id])
        reply=discord.Embed(
            title="Настройка завершена",
            description=f"Канал для логов успешно настроен как {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=reply)

@client.command()
async def remove_log_channel(ctx, channel_id):
    channel_IDs=[str(c.id) for c in ctx.guild.channels]
    if not channel_id in channel_IDs:
        await ctx.send("Канал не найден")
    else:
        channel=discord.utils.get(ctx.guild.channels, id=int(channel_id))
        await delete_data("log-channels", str(ctx.guild.id))
        reply=discord.Embed(
            title="Канал отвязан",
            description=f"Канал для логов успешно отвязан от {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=reply)

@client.command()
async def mute(ctx, member: discord.Member, raw_time, *, reason="не указана"):
    global bot_id
    global mute_role_name
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    if not Mute in ctx.guild.roles:
        await setup_mute(ctx.guild)
        Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    if not await has_helper(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        AbrList=['s','m','h']
        DurList=[1,60,3600]
        Names=['сек.','мин.','ч.']
        if not raw_time[len(raw_time)-1] in AbrList:
            reply=discord.Embed(
                title="❌Неверный формат",
                description="Укажите время так: **[Число]m**\n\n**s** - секунды, **m** - минуты, **h** - часы",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            index=AbrList.index(raw_time[len(raw_time)-1])
            dur=DurList[index]
            raw_time=raw_time[0:len(raw_time)-1]
            stamp=Names[index]
            if not number(raw_time):
                reply=discord.Embed(
                    title="❌Неверный формат",
                    description=f"[{raw_time}] должно быть целым числом",
                    color=discord.Color.red()
                )
                await ctx.send(embed=reply)
            else:
                time=int(raw_time)*dur
                if time>86400:
                    await ctx.send("Мут не может быть осуществлён больше, чем на 24 часа")
                else:
                    if await glob_pos(member)>=await glob_pos(bot_user):
                        reply=discord.Embed(
                            title="⚠Ошибка",
                            description=(f"Моя роль не выше роли пользователя {member}\n"
                                         "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                            color=discord.Color.gold()
                        )
                        await ctx.send(embed=reply)
                    else:
                        await member.add_roles(Mute)
                        log=discord.Embed(
                            title=':lock: Пользователь заблокирован',
                            description=(f"**{member.mention}** был заблокирован на **{raw_time}** {stamp}\n"
                                         f"Мут наложен пользователем {ctx.author.mention}\n"
                                         f"**Причина:** {reason}"),
                            color=discord.Color.darker_grey()
                        )
                        await ctx.send(embed=log)
                        await post_log(ctx.guild, log)
                        await member.send(f"Вы были заглушены на сервере **{ctx.guild.name}** на **{raw_time}** {stamp}\nПричина: {reason}")
                        await asyncio.sleep(time)
                        if Mute in member.roles:
                            await member.remove_roles(Mute)
                            log=discord.Embed(
                                title=':key: Пользователь разблокирован',
                                description=(f"**{member.mention}** был разблокирован\n"
                                             f"Ранне был заблокирован пользователем {ctx.author.mention}\n"
                                             f"Причина: {reason}"),
                                color=discord.Color.darker_grey()
                            )
                            await ctx.send(embed=log)
                            await post_log(ctx.guild, log)

@client.command()
async def unmute(ctx, member: discord.Member):
    global bot_id
    global mute_role_name
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    if not Mute in ctx.guild.roles:
        await setup_mute(ctx.guild)
        Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    if not await has_helper(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        if Mute in member.roles:
            if await glob_pos(member)>=await glob_pos(bot_user):
                reply=discord.Embed(
                    title="⚠Ошибка",
                    description=(f"Моя роль не выше роли пользователя {member}\n"
                               "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                    color=discord.Color.gold()
                )
                await ctx.send(embed=reply)
            else:
                await member.remove_roles(Mute)
                log=discord.Embed(
                    title=':key: Пользователь разблокирован',
                    description=f'**{member.mention}** был разблокирован',
                    color=discord.Color.darker_grey()
                )
                await ctx.send(embed=log)
                await post_log(ctx.guild, log)
        else:
            log=discord.Embed(
                title='Пользователь не заблокирован',
                description=f'**{member.mention}** не заблокирован **;black**',
                color=discord.Color.darker_grey()
            )
            await ctx.send(embed=log)
                
@client.command(aliases=["blacklist"])
async def black(ctx):
    bl_role="Мут"
    Blist=""
    Muted=discord.utils.get(ctx.author.guild.roles, name=bl_role)
    if not Muted in ctx.guild.roles:
        await ctx.send(f"На этом сервере еще не создана роль с названием **{bl_role}**")
    else:
        for m in ctx.author.guild.members:
            if Muted in m.roles:
                Blist=f'{Blist}\n<@%s>' % (m.id)
        if Blist=='':
            BlackList=discord.Embed(title=':notebook: Список заблокированных пользователей :notebook:', description="Пуст", color=discord.Color.darker_grey())
        else:
            BlackList=discord.Embed(title=':notebook: Список заблокированных пользователей :notebook:', description=Blist, color=discord.Color.darker_grey())
        await ctx.send(embed=BlackList)

@client.command()
async def kick(ctx, member: discord.Member, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await can_kick(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        if await glob_pos(ctx.author) <= await glob_pos(member):
            reply=discord.Embed(
                title="❌Недостаточно прав",
                description=f"Вы не можете кикнуть **{member.name}**, его роль не ниже Вашей",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            if await glob_pos(member)>=await glob_pos(bot_user):
                reply=discord.Embed(
                    title="⚠Ошибка",
                    description=(f"Моя роль не выше роли пользователя {member}\n"
                                 "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                    color=discord.Color.gold()
                )
                await ctx.send(embed=reply)
            else:
                await member.kick(reason=reason)
                log=discord.Embed(
                    title=f"**{member}** был кикнут",
                    description=(f"**Причина:** {reason}\n"
                                 f"Кикнут пользователем: {ctx.author.mention}"),
                    color=discord.Color.blurple()
                )
                await ctx.send(embed=log)
                await post_log(ctx.guild, log)
                await member.send(f"Вы были кикнуты с сервера **{ctx.guild.name}**.\n**Причина:** {reason}")
                
@client.command()
async def ban(ctx, member: discord.Member, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await can_ban(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        if await glob_pos(ctx.author) <= await glob_pos(member):
            reply=discord.Embed(
                title="❌Недостаточно прав",
                description=f"Вы не можете забанить **{member.name}**, его роль не ниже Вашей",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            if await glob_pos(member)>=await glob_pos(bot_user):
                reply=discord.Embed(
                    title="⚠Ошибка",
                    description=(f"Моя роль не выше роли пользователя {member}\n"
                                 "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                    color=discord.Color.gold()
                )
                await ctx.send(embed=reply)
            else:
                await member.ban(reason=reason)
                log=discord.Embed(
                    title=f"**{member}** был забанен",
                    description=f"**Причина:** {reason}\n**Забанен пользователем:** {ctx.author.mention}",
                    color=discord.Color.dark_red()
                )
                await ctx.send(embed=log)
                await post_log(ctx.guild, log)
                await member.send(f"Вы были забанены на сервере **{ctx.guild.name}**.\n**Причина:** {reason}")

@client.command()
async def unban(ctx, *, member=None):
    if not await can_ban(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        if member==None:
            reply=discord.Embed(
            title="⚠Ошибка",
            description="Укажите тег пользователя",
            color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            unbanned=None
            banned_users=await ctx.guild.bans()
            member_name, member_discriminator=member.split('#')
            for ban_entry in banned_users:
                user=ban_entry.user
                if (user.name, user.discriminator)==(member_name, member_discriminator):
                    unbanned=user
            if unbanned==None:
                await ctx.send(f"**{member}** нет в списке банов")
            else:
                await ctx.guild.unban(user)        
                log=discord.Embed(
                    title=f"**{member}** был разбанен",
                    description=f"Пользователь был разбанен администратором **{ctx.author}**",
                    color=discord.Color.dark_green()
                )
                await ctx.send(embed=log)
                await post_log(ctx.guild, log)
                await unbanned.send(f"Вы были разбанены на сервере **{ctx.guild.name}**")

@client.command()
async def set_mute_role(ctx):
    await ctx.send("🕑 пожалуйста, подождите...")
    await setup_mute(ctx.guild)
    log=discord.Embed(
        title="✅Настройка завершена",
        description="Роль мута настроена во всех каналах без явных ошибок",
        color=discord.Color.green()
    )
    await ctx.send(embed=log)
    
#=====================Errors==========================
@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description="Формат: **'mute [**Упомянуть участника**] [**Время**] [**Причина**]**\nНапример:\n**'mute @Player#0000 5m**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description="Формат: **'unmute [**Упомянуть участника**]**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description="Попробуйте снова, следуя формату\n**'kick [**@Player#0000**] [**Причина**]**\nНапример:\n**'kick @Player#0000 спам**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description="Попробуйте снова, следуя формату\n**'ban [**@Player#0000**] [**Причина**]**\nНапример:\n**'ban @Player#0000 порнография**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)

@set_log_channel.error
async def set_log_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**'set_log_channel [**ID канала**]**\nНапример:\n**'set_log_channel {ctx.channel.id}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
        
@remove_log_channel.error
async def remove_log_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**'remove_log_channel [**ID канала**]**\nНапример:\n**'remove_log_channel {ctx.channel.id}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.MissingRequiredArgument):
        return
    
client.run(str(os.environ.get('SIRIUS_TOKEN')))
