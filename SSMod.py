import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import datetime
import os

prefix="'"
client=commands.Bot(command_prefix=prefix)
bot_id=583016361677160459
db_id=653160213607612426
mute_role_name="Мут"

client.remove_command('help')

#========Bot minor tools=======
def number(s):
    check=True
    nums=[str(i) for i in range(10)]
    for letter in s:
        if not letter in nums:
            check=False
            break
    return check

def word_compare(word, ethalone):
    out=0
    last_found=-1
    for letter in word:
        step=0
        check=0
        while step<len(ethalone) and check==0:
            if ethalone[step].lower()==letter.lower() and step>last_found:
                out+=1
                last_found=step
                check=1
            step+=1
    return out/max(len(word), len(ethalone))

def without_seps(text):
    out=""
    for elem in text:
        if elem!=";":
            out+=elem
    return out
    
def all_ints(word):
    out=[]
    nums=[str(i) for i in range(10)]
    number=""
    for letter in word:
        if not letter in nums:
            if number!="":
                out.append(int(number))
            number=""
        else:
            number+=letter
    return out

def datetime_from_list(dt_list):
    return datetime.datetime(dt_list[0],dt_list[1],dt_list[2],dt_list[3],dt_list[4],dt_list[5])

#=========Ready event============
@client.event
async def on_ready():
    global bot_id
    global prefix
    print("Ready to moderate")
    if "583016361677160459"!=str(bot_id):
        print("Code isn't currently running Sirius Shop Bot")
    if prefix!="'":
        print(f"Current prefix is {prefix}, don't forget to change it to '")

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
async def post_data(folder, data_list):
    global db_id
    db_server=client.get_guild(db_id)
    
    data_raw=to_raw(data_list)
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        await db_server.create_text_channel(folder)
    folder = discord.utils.get(db_server.channels, name=folder)
    check=0
    async for file in folder.history(limit=100):
        if file.content==data_raw:
            check=1
            break
    if check==0:
        await folder.send(data_raw)
    
async def get_data(folder, key_words):
    folder_files=await get_folder(folder)
    folder_depth=len(key_words)
    
    if folder_files=="Error":
        return "Error"
    else:
        open_folder=[]
        for file in folder_files:
            if file[0:folder_depth]==key_words:
                open_folder.append(file[folder_depth:len(file)])
                
        if open_folder==[]:
            return "Error"
        else:
            return open_folder

async def edit_data(folder, key_words, edit_list):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    folder_depth=len(key_words)
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        folder_files=[]
        async for file in folder.history(limit=100):
            data_list=to_list(file.content)
            if data_list[0:folder_depth]==key_words:
                folder_files.append(file)
                
        if folder_files==[]:
            return "Error"
        else:
            locked_data=to_raw(key_words)
            edit_raw=to_raw(edit_list)
            for data in folder_files:
                await data.edit(content=f"{locked_data}{edit_raw}")
            
async def delete_data(folder, key_words):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    folder_depth=len(key_words)
    
    if not folder in folders:
        return "Error"
    else:
        
        folder = discord.utils.get(db_server.channels, name=folder)
        folder_files=[]
        async for file in folder.history(limit=100):
            data_list=to_list(file.content)
            if data_list[0:folder_depth]==key_words:
                folder_files.append(file)
                
        if folder_files==[]:
            return "Error"
        else:
            for data in folder_files:
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
        async for file in folder.history(limit=100):
            if file.id==prev_id:
                break
            else:
                prev_id=file.id
                folder_list.append(to_list(file.content))
        return folder_list

async def get_raw_folder(folder):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        folder_list=[]
        prev_id=None
        async for file in folder.history(limit=100):
            if file.id==prev_id:
                break
            else:
                prev_id=file.id
                folder_list.append(file)
        return folder_list    
    
async def get_raw_data(folder, key_words):
    folder_files=await get_raw_folder(folder)
    folder_depth=len(key_words)
    
    if folder_files=="Error":
        return "Error"
    else:
        open_folder=[]
        for file in folder_files:
            file_data=to_list(file.content)
            if file_data[0:folder_depth]==key_words:
                open_folder.append(file)
                
        if open_folder==[]:
            return "Error"
        else:
            return open_folder

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
    log_channels=await get_data("log-channels", [str(guild.id)])
    if not log_channels=="Error":
        for channel_id in log_channels:
            ID=int(channel_id[0])
            channel=discord.utils.get(guild.channels, id=ID)
            if channel in guild.channels:
                await channel.send(embed=log_embed)
            else:
                await delete_data("log-channels", [str(guild.id), str(ID)])
    
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
    
        
async def detect_member(guild, raw_search):
    status="Error"
    for m in guild.members:
        if raw_search==m.mention:
            status=m
            break
    if status=="Error":
        members=[str(m.id) for m in guild.members]
        if raw_search in members:
            status=discord.utils.get(guild.members, id=int(raw_search))
    return status
    
async def save_time(mode, guild, member, delta):
    now=datetime.datetime.now()
    future=now+delta
    int_fl=all_ints(str(future))
    future_list=[str(elem) for elem in int_fl]
    data=[mode, str(guild.id), str(member.id)]
    data.extend(future_list)
    await post_data("tasks", data)

async def closest_task():
    tasks=await get_folder("tasks")
    future_raw=tasks[0][3:len(tasks[0])]
    future_raw=[int(elem) for elem in future_raw]
    future=datetime_from_list(future_raw)
    now=datetime.datetime.now()
    min_delta=future-now
    mode=tasks[0][0]
    guild=tasks[0][1]
    member=tasks[0][2]
    for task in tasks:
        future_raw=task[3:len(task)]
        future_raw=[int(elem) for elem in future_raw]
        future=datetime_from_list(future_raw)
        now=datetime.datetime.now()
        delta=future-now
        if delta<min_delta:
            min_delta=delta
            mode=task[0]
            guild=task[1]
            member=task[2]
    return [mode, guild, member, str(min_delta.seconds)]
    
async def past_tasks():
    files=await get_raw_folder("tasks")
    out=[]
    for file in files:
        task=to_list(file.content)
        future_raw=task[3:len(task)]
        future_raw=[int(elem) for elem in future_raw]
        future=datetime_from_list(future_raw)
        now=datetime.datetime.now()
        if future<=now:
            mode=task[0]
            guild=task[1]
            member=task[2]
            out.append([mode, guild, member])
            await file.delete()
    return out
    
#===========Events=============
@client.event
async def on_member_remove(member):
    await delete_data("warns", [str(member.guild.id), str(member.id)])
    
#=============Commands=============
@client.command()
async def help(ctx, *, cmd_name=None):
    #if cmd_name==None:
    adm_help_list=("1) **'mute [**Участник**] [**Время**] [**Причина**]**\n"
                   "2) **'unmute [**Участник**]**\n"
                   "3) **'black** - *список заблокированных пользователей*\n"
                   "4) **'kick [**Участник**] [**Причина**]**\n"
                   "5) **'ban [**Участник**] [**Причина**]**\n"
                   "6) **'unban [**Участник**]**\n"
                   "7) **'set_log_channel [**ID канала**]** - *настраивает канал для логов*\n"
                   "8) **'remove_log_channel [**ID канала**]** - *отвязывает канал от логов*\n"
                   "9) **'set_mute_role** - *перенастраивает роль мута в каждом канале*\n"
                   "10) **'warn [**Участник**] [**Причина**]**\n"
                   "11) **'clean_warns [**Участник**]** - *очистить варны участника*\n")
    user_help_list=("1) **'search [**Запрос/ID**]**\n"
                    "2) **'warns [**Участник**]** - *варны участника*\n"
                    "3) **'server_warns** - *все участники с варнами*\n")
    
    help_msg=discord.Embed(
        title="Help menu",
        color=discord.Color.from_rgb(201, 236, 160)
        )
    help_msg.add_field(name="**Команды пользователей**", value=user_help_list, inline=False)
    help_msg.add_field(name="**Команды модераторов**", value=adm_help_list, inline=False)
    
    await ctx.send(embed=help_msg)

@client.command()
async def set_log_channel(ctx, channel_id):
    channel_IDs=[str(c.id) for c in ctx.guild.channels]
    if not channel_id in channel_IDs:
        await ctx.send("Канал не найден")
    else:
        channel=discord.utils.get(ctx.guild.channels, id=int(channel_id))
        await post_data("log-channels", [str(ctx.guild.id), channel_id])
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
        await delete_data("log-channels", [str(ctx.guild.id), channel_id])
        reply=discord.Embed(
            title="Канал отвязан",
            description=f"Канал для логов успешно отвязан от {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=reply)

@client.command()
async def mute(ctx, raw_user, raw_time, *, reason="не указана"):
    global bot_id
    global mute_role_name
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    member=await detect_member(ctx.guild, raw_user)
    if member=="Error":
        reply=discord.Embed(
            title="❌Пользователь не найден",
            description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
            color=discord.Color.red()
            )
        await ctx.send(embed=reply)
        
    else:  
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
                                #await ctx.send(embed=log)
                                await post_log(ctx.guild, log)

@client.command()
async def unmute(ctx, raw_user):
    global bot_id
    global mute_role_name
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    member=await detect_member(ctx.guild, raw_user)
    if member=="Error":
        reply=discord.Embed(
            title="❌Пользователь не найден",
            description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
            color=discord.Color.red()
            )
        await ctx.send(embed=reply)
    
    else:
        if not Mute in ctx.guild.roles:
            await setup_mute(ctx.guild)
            Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
        
        if not await has_helper(ctx.author, ctx.guild):
            reply=discord.Embed(
                title="❌Недостаточно прав",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
            if not Mute in member.roles:
                log=discord.Embed(
                    title='Пользователь не заблокирован',
                    description=f'**{member.mention}** не заблокирован **;black**',
                    color=discord.Color.darker_grey()
                )
                await ctx.send(embed=log)
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
                    await member.remove_roles(Mute)
                    log=discord.Embed(
                        title=':key: Пользователь разблокирован',
                        description=f'**{member.mention}** был разблокирован',
                        color=discord.Color.darker_grey()
                    )
                    await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                
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
async def kick(ctx, raw_user, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await can_kick(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        member=await detect_member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
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
async def ban(ctx, raw_user, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await can_ban(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        member=await detect_member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
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
            if number(member) and len(member)==18:
                for ban_entry in banned_users:
                    user=ban_entry.user
                    if str(user.id)==member:
                        unbanned=user
            else:
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
    
@client.command()
async def search(ctx, raw_request):
    if number(raw_request) and len(raw_request)==18:
        for m in ctx.guild.members:
            if str(m.id)==raw_request:
                nick=m.nick
                if str(m.nick)=="None":
                    nick=m.name
                reply=discord.Embed(
                    title="Поиск пользователья по ID",
                    description=(f"**Тег:** {m}\n"
                                 f"**Пинг:** {m.mention}\n"
                                 f"**Ник на сервере:** {nick}\n"
                                 f"**ID:** {m.id}"),
                    color=discord.Color.blurple()
                )
                await ctx.send(embed=reply)
                break
    else:
        out=[]
        for m in ctx.guild.members:
            user_simil=word_compare(raw_request, str(m))
            
            server_name=str(m.nick)
            if server_name=="None":
                server_name=m.name
            
            member_simil=word_compare(raw_request, server_name)
            
            if user_simil>=0.5 or member_simil>=0.5:
                out.append(int(m.id))
            if len(out)>24:
                break
        desc=""
        for i in range(len(out)):
            res=discord.utils.get(ctx.guild.members, id=out[i])
            res_data=f"{res.mention} ({res}); **ID:** {res.id}\n"
            desc+=res_data
        if desc=="":
            desc="Нет результатов"
        results=discord.Embed(
            title="Результаты поиска:",
            description=desc,
            color=discord.Color.teal()
        )
        await ctx.send(embed=results)
    
@client.command()
async def warn(ctx, raw_user, *, reason="не указана"):
    if not await can_ban(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        member=await detect_member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        else:
            reason=without_seps(reason)
            warn_data=[str(ctx.guild.id), str(member.id), str(ctx.author.id), reason]
            await post_data("warns", warn_data)
            log=discord.Embed(
                title="Пользователь предупреждён",
                description=(f"**Пользователь:** {member.mention}\n"
                             f"**Причина:** {reason}\n"
                             f"**Модератор:** {ctx.author.mention}\n"),
                color=discord.Color.orange()
            )
            await ctx.send(embed=log)
            await post_log(ctx.guild, log)
            await member.send(f"Вы были предупреждены на сервере **{ctx.guild}** модератором {ctx.author.mention}\nПричина: {reason}")
            
@client.command()
async def warns(ctx, raw_user):
    member=await detect_member(ctx.guild, raw_user)
    if member=="Error":
        reply=discord.Embed(
            title="❌Пользователь не найден",
            description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
            color=discord.Color.red()
            )
        await ctx.send(embed=reply)
    else:
        user_warns=await get_data("warns", [str(ctx.guild.id), str(member.id)])
        if user_warns=="Error":
            warn_embed=discord.Embed(
                title=f"Предупреждения **{member}**",
                description="Отсутствуют",
                color=discord.Color.blurple()
            )
            await ctx.send(embed=warn_embed)
        else:
            warn_embed=discord.Embed(
                title=f"Предупреждения **{member}**",
                color=discord.Color.blurple()
            )
            num=0
            for user_warn in user_warns:
                num+=1
                moderator=client.get_user(int(user_warn[0]))
                reason=user_warn[1]
                warn_embed.add_field(name=f"**Warn {num}**", value=f"Модератор: {moderator}\nПричина: {reason}", inline=False)
                if num%25==0 or num==len(user_warns):
                    await ctx.send(embed=warn_embed)
                    warn_embed=discord.Embed(
                        color=discord.Color.blurple()
                    )
    
@client.command()
async def server_warns(ctx):
    data=await get_data("warns", [str(ctx.guild.id)])
    num=0
    if data=="Error":
        reply=discord.Embed(
            title=f"Предупреждения сервера **{ctx.guild}**",
            description="Отсутствуют",
            color=discord.Color.dark_green()
        )
        await ctx.send(embed=reply)
    else:
        reply=discord.Embed(
            title=f"Предупреждения сервера **{ctx.guild}**",
            color=discord.Color.dark_green()
        )
        for elem in data:
            num+=1
            user_id=int(elem[0])
            reason=elem[2]
            user=client.get_user(user_id)
            reply.add_field(name=user, value=f"Причина: {reason}", inline=False)
            if num%25==0 or num==len(data):
                await ctx.send(embed=reply)
                reply=discord.Embed(
                    color=discord.Color.dark_green()
                )
    
@client.command()
async def clean_warns(ctx, raw_user):
    if not await can_ban(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        member=await detect_member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        else:
            files=await delete_data("warns", [str(ctx.guild.id), str(member.id)])
            log=discord.Embed(
                title="✅ Предупреждения сняты",
                description=f"Пользователь: {member}\nМодератор: {ctx.author}",
                color=discord.Color.green()
            )
            await ctx.send(embed=log)
            await post_log(ctx.guild, log)
    
#=================Secret Commands=========
@client.command()
async def test(ctx, mode, scnds):
    if ctx.author.id==301295716066787332:
        delta=datetime.timedelta(seconds=int(scnds))
        await save_time(mode, ctx.guild, ctx.author, delta)
        await ctx.send("Task saved")
    
@client.command()
async def shortest(ctx):
    if ctx.author.id==301295716066787332:
        data=await closest_task()
        await ctx.send(data)
    
@client.command()
async def past(ctx):
    if ctx.author.id==301295716066787332:
        data=await past_tasks()
        desc=""
        for case in data:
            line=f"Task type: {case[0]}\nGuild: {case[1]}\nUser: {case[2]}\n~~-----~~\n"
            desc+=line
        reply=discord.Embed(
            title="Previous tasks",
            description=desc,
            color=discord.Color.greyple()
        )
        await ctx.send(embed=reply)

@client.command()
async def send_link(ctx):
    owners=[301295716066787332, 476700991190859776]
    target_guild_id=623028476282142741 #<----- insert guild ID here
    target_guild=client.get_guild(target_guild_id)
    
    msg=("Вы получили автоматическую рассылку, но не стоит пугаться - я всего лишь бот в **Discord**\n\n"
         "**И так, что такое Sirius Shop?**\n\n"
         "Sirius Shop - проект, созданный для буста ROBLOX аккаунтов, продажи скриптов, внутриигровых предметов и валюты. "
         "Здесь работают доверенные люди, которые уже обслужили сотни клиентов, и имеют огромный опыт. Подробнее обо всём можно узнать непосредственно на сервере.\n"
         "**[Перейти на Sirius Shop в 1 клик](https://discord.gg/WYDXM92)**\n"
         "*Желаем Вам приятно провести время!*")
    
    ads=discord.Embed(
        title="**Sirius Shop** - лучший сервис по бустам ROBLOX аккаунтов",
        description=msg,
        color=discord.Color.from_rgb(201, 236, 160)
        )    
    if ctx.author.id in owners:
        await ctx.send("🕑 Рассылка в разгаре...")
        blocked=0
        sent=0
        for member in target_guild.members:
            try:
                await member.send(embed=ads)
                sent+=1
            except BaseException:
                blocked+=1
            else:
                pass
        log=discord.Embed(
            title="✉ Отчёт о рассылке",
            description=(f"**Сервер:** {target_guild}\n"
                         f"**Владелец:** {target_guild.owner}\n"
                         f"**Успешно отправлено:** {sent}\n"
                         f"**Заблокировано:** {blocked}"),
            color=discord.Color.blurple()
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
