import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import datetime
import os
from emoji import UNICODE_EMOJI
import random

prefix="'"
client=commands.Bot(command_prefix=prefix)
bot_id=583016361677160459
db_id=653160213607612426
mute_role_name="Мут"

client.remove_command('help')

#=========Events ready============
@client.event
async def on_ready():
    global bot_id
    global prefix
    print("Ready to moderate")
    if "589922044720709656"!=str(bot_id):
        print("Code isn't currently running TASPA Moderation Bot")
    if prefix!="t!":
        print(f"Current prefix is {prefix}, don't forget to change it to t!")

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
    if number!="":
        out.append(int(number))
    return out

def datetime_from_list(dt_list):
    dt_list=[int(elem) for elem in dt_list]
    return datetime.datetime(dt_list[0],dt_list[1],dt_list[2],dt_list[3],dt_list[4],dt_list[5])

def detect_isolation(text, lll):
    wid=len(lll)
    iso=False
    out=[]
    for i in range(len(text)-wid+1):
        piece=text[i:i+wid]
        if piece==lll:
            if iso==True:
                iso=False
                end=i
                if start<end:
                    out.append(text[start:end])
            else:
                iso=True
                start=i+wid
    return out

def list_sum(List):
    out=""
    for elem in List:
        out+="\n"+str(elem)
    return out[1:len(out)]

def detect_args(text, lll):
    wid=len(lll)
    iso=False
    out=[]
    for i in range(len(text)-wid+1):
        piece=text[i:i+wid]
        if piece==lll:
            if iso==True:
                iso=False
                end=i+wid
                if start<end:
                    out.append([text[start+wid:end-wid], start, end])
            else:
                iso=True
                start=i
    return out

def c_split(text, lll):
    out=[]
    wid=len(lll)
    text_l=len(text)
    start=0
    end=-1
    for i in range(text_l-wid+1):
        if text[i:i+wid]==lll:
            end=i
            if start<end:
                out.append(text[start:end])
            start=i+wid
    if end!=text_l-wid:
        out.append(text[start:text_l])
    return out

def is_emoji(s):
    count = 0
    for emoji in UNICODE_EMOJI:
        count += s.count(emoji)
        if count > 1:
            return False
    return bool(count)

#========Database Minor tools=======
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
    
def c_partially(data_1, ethalone):
    depth=len(ethalone)
    buffer=[elem for elem in ethalone]
    for i in range(len(data_1)):
        if data_1[i]=="None":
            if i<depth:
                buffer[i]="None"
    return True if data_1==buffer else False

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
    async for file in folder.history(limit=None):
        if file.content==data_raw:
            check=1
            break
    if check==0:
        await folder.send(data_raw)
    
async def get_data(folder, key_words):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        open_folder=[]
        folder_depth=len(key_words)
        async for file in folder.history(limit=None):
            data=to_list(file.content)
            if c_partially(key_words, data[0:folder_depth]):
                open_folder.append(data[folder_depth:len(data)])
                
        if open_folder==[]:
            return "Error"
        else:
            return open_folder

async def edit_data(folder_name, key_words, full_edit_list):
    global db_id
    db_server=client.get_guild(db_id)
    edit_raw=to_raw(full_edit_list)
    
    folder_names=[c.name for c in db_server.channels]
    folder_depth=len(key_words)
    
    if not folder_name in folder_names:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder_name)
        exist=False
        async for file in folder.history(limit=None):
            data_list=to_list(file.content)
            if c_partially(key_words, data_list[0:folder_depth]):
                exist=True
                await file.edit(content=edit_raw)
                
        if exist==False:
            return "Error"
            
async def delete_data(folder, key_words):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    folder_depth=len(key_words)
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        found=False
        async for file in folder.history(limit=None):
            data_list=to_list(file.content)
            if c_partially(key_words, data_list[0:folder_depth]):
                found=True
                file.delete()
                
        if found==False:
            return "Error"
            
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
        async for file in folder.history(limit=None):
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
        async for file in folder.history(limit=None):
            folder_list.append(file)
        return folder_list    
    
async def get_raw_data(folder, key_words):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    
    if not folder in folders:
        return "Error"
    else:
        folder = discord.utils.get(db_server.channels, name=folder)
        open_folder=[]
        folder_depth=len(key_words)
        async for file in folder.history(limit=None):
            data=to_list(file.content)
            if c_partially(key_words, data[0:folder_depth]):
                open_folder.append(file)
                
        if open_folder==[]:
            return "Error"
        else:
            return open_folder

#============Bot async funcs==========
async def users(server):
    await client.wait_until_ready()
    summ=0
    bots=0
    for user in server.members:
        summ+=1
        if user.bot==1:
            bots+=1
    channel=discord.utils.get(server.channels, name='stats')
    if channel in server.channels:
        stats=discord.Embed(
            title=':bar_chart: __**Server stats**__ :bar_chart:',
            color=discord.Color.green()
        )
        stats.add_field(name='Total users:', value=f'**{summ}**')
        stats.add_field(name='Total bots:', value=f'**{bots}**')
        stats.add_field(name='Total humans:', value=f'**{summ-bots}**')
        await channel.purge(limit=1)
        await channel.send(embed=stats)

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
    
async def save_task(mode, guild, member, raw_delta):
    delta=datetime.timedelta(seconds=raw_delta)
    now=datetime.datetime.now()
    future=now+delta
    int_fl=all_ints(str(future))
    future_list=[str(elem) for elem in int_fl[0:len(int_fl)-1]]
    data=["on", mode, str(guild.id), str(member.id)]
    data.extend(future_list)
    await post_data("tasks", data)

async def closest_inactive_task():
    raw_tasks=await get_raw_data("tasks", ["off"])
    
    if raw_tasks=="Error":
        return "Error"
    else:
        task_file=raw_tasks[0]
        
        first_task=to_list(task_file.content)
        last=len(first_task)
        
        future_raw_str=first_task[last-6:last]
        future_raw=[int(elem) for elem in future_raw_str]
        
        future=datetime_from_list(future_raw)
        now=datetime.datetime.now()
        min_delta=future-now
        
        for file in raw_tasks:
            task=to_list(file.content)
            
            future_raw_str=task[last-6:last]
            future_raw=[int(elem) for elem in future_raw_str]
            future=datetime_from_list(future_raw)
            delta=future-now
            
            if delta<min_delta and future>now:
                min_delta=delta
                task_file=file
        
        task=to_list(task_file.content)
        task[0]="on"
        task_edit=to_raw(task)
        await task_file.edit(content=task_edit)
        return [task[1:4], min_delta.seconds]

async def clean_past_tasks():
    files=await get_raw_folder("tasks")
    out=[]
    for file in files:
        task=to_list(file.content)
        last=len(task)
        future_raw=task[last-6: last]
        
        future=datetime_from_list(future_raw)
        now=datetime.datetime.now()
        if future<=now:
            mode=task[1]
            guild=task[2]
            member=task[3]
            out.append([mode, guild, member])
            await file.delete()
    return out
    
async def reset_tasks():
    active_tasks=await get_raw_data("tasks", ["on"])
    if active_tasks!="Error":
        for task in active_tasks:
            task_data=to_list(task.content)
            task_data[0]="off"
            task_edit=to_raw(task_data)
            await task.edit(content=task_edit)
    
async def delete_task(mode, guild, member):
    global db_id
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    if not "tasks" in folders:
        return "Error"
    else:
        out="Error"
        folder = discord.utils.get(db_server.channels, name="tasks")
        open_folder=[]
        key_words=[mode, str(guild.id), str(member.id)]
        prev_id=None
        
        async for file in folder.history(limit=100):
            if file.id==prev_id:
                break
            else:
                prev_id=file.id
                data=to_list(file.content)
                if data[1:4]==key_words:
                    out=[data[1], data[2], data[3]]
                    await file.delete()
                
        return out
    
async def recharge(case):
    global bot_id
    global mute_role_name
    mode=case[0]
    guild_id=int(case[1])
    member_id=int(case[2])
    guild=client.get_guild(guild_id)
    member=discord.utils.get(guild.members, id=member_id)
    bot_user=discord.utils.get(guild.members, id=bot_id)
    if mode=="mute":
        Mute = discord.utils.get(guild.roles, name=mute_role_name)
        if not Mute in guild.roles:
            await setup_mute(guild)
            Mute = discord.utils.get(guild.roles, name=mute_role_name)
        if await glob_pos(bot_user)>await glob_pos(member):
            await member.remove_roles(Mute)
        
    elif mode=="ban":
        unbanned=None
        banned_users=await guild.bans()
        for ban_entry in banned_users:
            user=ban_entry.user
            if user.id==member_id:
                unbanned=user
        if unbanned!=None:
            await guild.unban(unbanned)

async def polite_send(user, msg):
    try:
        await user.send(msg)
    except BaseException:
        return "Error"
    else:
        pass    

async def refresh_mute(member):
    global db_id
    global mute_role_name
    db_server=client.get_guild(db_id)
    
    folders=[c.name for c in db_server.channels]
    if "tasks" in folders:
        folder = discord.utils.get(db_server.channels, name="tasks")
        key_words=["mute", str(member.guild.id), str(member.id)]
        prev_id=None
        
        Mute = discord.utils.get(member.guild.roles, name=mute_role_name)
        if not Mute in member.guild.roles:
            await setup_mute(member.guild)
            Mute = discord.utils.get(member.guild.roles, name=mute_role_name)        
        
        async for file in folder.history(limit=100):
            if file.id==prev_id:
                break
            else:
                prev_id=file.id
                data=to_list(file.content)
                if data[1:4]==key_words:
                    await member.add_roles(Mute)
                    break    
    
async def send_welcome(member):
    global bot_id
    bot_user=discord.utils.get(member.guild.members, id=bot_id)
    
    channels=await get_data("welcome-channels", [str(member.guild.id)])
    if channels!="Error":
        ID=int(channels[0][0])
        channel=discord.utils.get(member.guild.channels, id=ID)
        messages=await get_data("welcome-msg", [str(member.guild.id)])
        if messages!="Error":
            arg_names=["server", "user"]
            arg_values=[member.guild, member.mention]
            message=messages[0][0]
            arg_data=detect_args(message, "==")
            text=""
            prev_end=0
            for triplet in arg_data:
                if triplet[0].lower() in arg_names:
                    ind=arg_names.index(triplet[0].lower())
                    start=triplet[1]
                    end=triplet[2]
                    text+=f"{message[prev_end:start]}{arg_values[ind]}"
                    prev_end=end
            text+=f"{message[prev_end:len(message)]}"
            await polite_send(channel, text)
    roles=await get_data("welcome-roles", [str(member.guild.id)])
    if roles!="Error":
        for str_ID in roles[0]:
            role=discord.utils.get(member.guild.roles, id=int(str_ID))
            if role!=None and role.position<await glob_pos(bot_user):
                await member.add_roles(role)

async def send_leave(member):
    global bot_id
    bot_user=discord.utils.get(member.guild.members, id=bot_id)
    
    channels=await get_data("leave-channels", [str(member.guild.id)])
    if channels!="Error":
        ID=int(channels[0][0])
        channel=discord.utils.get(member.guild.channels, id=ID)
        messages=await get_data("leave-msg", [str(member.guild.id)])
        if messages!="Error":
            arg_names=["server", "user"]
            arg_values=[member.guild, member.mention]
            message=messages[0][0]
            arg_data=detect_args(message, "==")
            text=""
            prev_end=0
            for triplet in arg_data:
                if triplet[0].lower() in arg_names:
                    ind=arg_names.index(triplet[0].lower())
                    start=triplet[1]
                    end=triplet[2]
                    text+=f"{message[prev_end:start]}{arg_values[ind]}"
                    prev_end=end
            text+=f"{message[prev_end:len(message)]}"
            await polite_send(channel, text)

async def detect_role(guild, raw_search):
    out="Error"
    for r in guild.roles:
        if raw_search==f"<@&{r.id}>" or raw_search==str(r.id):
            out=r
            break
    return out

async def detect_channel(guild, raw_search):
    out="Error"
    for channel in guild.channels:
        if raw_search==f"<#{channel.id}>" or raw_search==str(channel.id):
            out=channel
            break
    return out

async def detect_member(guild, raw_search):
    status="Error"
    for m in guild.members:
        if raw_search==m.mention or raw_search==f"<@!{m.id}>" or raw_search==str(m.id) or raw_search==f"<@{m.id}>":
            status=m
            break
    return status

async def detect_emoji(guild, raw_search):
    out="Error"
    for emoji in guild.emojis:
        if raw_search==f"<:{emoji.name}:{emoji.id}>":
            out=emoji
            break
    if out=="Error":
        if is_emoji(raw_search):
            out=raw_search
    return out

async def detect_message(channel_id, message_id):
    channel=client.get_channel(int(channel_id))
    if channel==None:
        return "Error"
    else:
        try:
            message=await channel.fetch_message(int(message_id))
        except BaseException:
            return "Error"
        else:
            return message
    
async def read_message(channel, user, t_out):
    try:
        msg=await client.wait_for("message", check=lambda message: user.id==message.author.id and channel.id==message.channel.id, timeout=t_out)
    except asyncio.TimeoutError:
        reply=discord.Embed(
            title="🕑 Вы слишком долго не писали",
            description=f"Настройка прервана",
            color=discord.Color.blurple()
        )
        await channel.send(content=user.mention, embed=reply)
        return "Timeout"
    else:
        return msg

async def save_giveaway(guild, message, winner_num, host_user, prize, raw_delta):
    delta=datetime.timedelta(seconds=raw_delta)
    now=datetime.datetime.now()
    future=now+delta
    int_fl=all_ints(str(future))
    future_list=[str(elem) for elem in int_fl[0:len(int_fl)-1]]
    data=["on", str(guild.id), str(message.id), str(winner_num), str(host_user.id), str(message.channel.id), prize]
    data.extend(future_list)
    await post_data("giveaways", data)

async def finish_giveaway(message):
    guild=message.guild
    files=await get_raw_data("giveaways", ["None", str(guild.id), str(message.id)])
    message=await detect_message(message.channel.id, message.id)
    #files = [on/off, guild_id, message_id, winner_num, host_id, channel_id, prize, yyyy, mm, dd, hh, mm, ss]
    if files!="Error":
        file=files[0]
        users=await reacted(message)
        
        await file.delete()
        
        data=to_list(file.content)
        winner_num=int(data[3])
        g_name=data[6]
        host_user_id=int(data[4])
        host_user=discord.utils.get(guild.members, id=host_user_id)
        channel=message.channel
        
        winners=[]
        for i in range(winner_num):
            if users!=[]:
                winner_id=random.choice(users)
                users.remove(winner_id)
                
                winner=discord.utils.get(guild.members, id=winner_id)
                if winner!=None:
                    winners.append(winner)
            else:
                break
            
        if winners==[]:
            error_embed=discord.Embed(
                title="⚠ Сбой",
                description=(f"**Приз:** {g_name}\n"
                             "Не могу распознать победителей"),
                color=discord.Color.gold()
            )
            await channel.send(embed=error_embed)
        else:
            winner_table=""
            for w in winners:
                winner_table+=f"{w.mention}\n"
            if host_user==None:
                host_ment="не найден"
            else:
                host_ment=host_user.mention
            g_end_embed=discord.Embed(
                title="🎉 Результаты",
                description=(f"**Приз:** {g_name}\n"
                             f"**Хост:** {host_ment}\n"
                             f"**Победители:**\n{winner_table}"),
                color=discord.Color.gold()
            )
            await channel.send(embed=g_end_embed)

async def closest_giveaway():
    files=await get_raw_data("giveaways", ["off"])
    out="Error"
    if files!="Error":
        now=datetime.datetime.now()
        
        data=to_list(files[0].content)
        future_str=data[len(data)-6:len(data)]
        future=datetime_from_list(future_str)
        min_delta=future-now
        
        guild_id=int(data[1])
        channel_id=int(data[5])
        message_id=int(data[2])
        
        message=await detect_message(channel_id, message_id)
        out=[message, min_delta.seconds]
        
        pinned=files[0]
        
        for file in files:
            data=to_list(file.content)
            
            future_str=data[len(data)-6:len(data)]
            future=datetime_from_list(future_str)
            delta=future-now
            
            if delta<min_delta:
                min_delta=delta
                
                channel_id=int(data[5])
                message_id=int(data[2])
                
                message=await detect_message(channel_id, message_id)
                out=[message, min_delta.seconds]
                
                pinned=file
                
        data=to_list(pinned.content)
        data[0]="on"
        await pinned.edit(content=to_raw(data))
    return out
    
async def clean_past_giveaways():
    files=await get_raw_folder("giveaways")
    out=[]
    if files!="Error":
        now=datetime.datetime.now()
        for file in files:
            data=to_list(file.content)
            
            last=len(data)
            future_raw=data[last-6:last]
            future=datetime_from_list(future_raw)
            
            if future<=now:
                message_id=int(data[2])
                channel_id=int(data[5])
                message=await detect_message(channel_id, message_id)
                if message!="Error":
                    out.append(message)
    return out
    
async def reset_giveaways():
    files=await get_raw_data("giveaways", ["on"])
    if files!="Error":
        for file in files:
            data=to_list(file.content)
            data[0]="off"
            await file.edit(content=to_raw(data))
    
async def reacted(message):
    bot_id=client.user.id
    reaction=None
    rs=message.reactions
    for r in rs:
        if r.emoji=='🎉':
            reaction=r
            break
    if reaction==None:
        return []
    else:
        users=[]
        async for user in reaction.users():
            if user.id!=bot_id:
                users.append(user.id)
        return users

#=============Commands=============
@client.command()
async def help(ctx, *, cmd_name=None):
    global prefix
    p=prefix
    if cmd_name==None:
        adm_help_list1=(f"1) **{p}mute [**Участник**] [**Время**] <**Причина**>**\n"
                       f"2) **{p}unmute [**Участник**]**\n"
                       f"3) **{p}black** - *список заблокированных пользователей*\n"
                       f"4) **{p}kick [**Участник**] <**Причина**>**\n"
                       f"5) **{p}ban [**Участник**] <**Причина**>**\n"
                       f"6) **{p}tempban [**Участник**] [**Время**] <**Причина**>**\n"
                       f"7) **{p}unban [**Участник**]**\n"
                       f"8) **{p}set_log_channel [**ID канала**]** - *настраивает канал для логов*\n"
                       f"9) **{p}remove_log_channel [**ID канала**]** - *отвязывает канал от логов*\n"
                       f"10) **{p}set_mute_role** - *перенастраивает роль мута в каждом канале*\n"
                       f"11) **{p}warn [**Участник**] <**Причина**>**\n"
                       f"12) **{p}clean_warns [**Участник**]** - *очистить варны участника*\n"
                       f"13) **{p}clean_warn [**Участник**] [**Номер варна**]** - *снять конкретный варн*\n"
                       f"14) **{p}del [**Кол-во сообщений**]** - *удаляет указанное кол-во сообщений*\n"
                       f"15) **{p}set_welcome [**Раздел**] [**Аргументы / delete**]** - ***{p}help set_welcome** для подробностей*\n"
                       f"16) **{p}welcome_info** - *отображает текущие настройки автоматических действий с новичками*\n")
        adm_help_list2=(f"17) **{p}reaction_roles <**Заголовок**>** - *начинает создание вывески с раздачей ролей за реакции*\n"
                        f"18) **{p}set_leave [**Раздел**] [**Аргумент / delete**]** - ***{p}help set_leave** для подробностей*\n")
        user_help_list=(f"1) **{p}search [**Запрос/ID**]**\n"
                        f"2) **{p}warns [**Участник**]** - *варны участника*\n"
                        f"3) **{p}server_warns** - *все участники с варнами*\n"
                        f"4) **{p}embed [**Текст**]** - ***{p}help embed** для подробностей*\n"
                        f"5) **{p}altshift [**Текст**]** - *переключает раскладку для написанного текста*\n"
                        f"6) **{p}avatar <**Пользователь**>** - *рассмотреть свою/чужую аватарку*\n"
                        f"7) **{p}set_giveaway** - *начинает настройку розыгрыша*\n")
        
        help_msg=discord.Embed(
            title="Help menu",
            color=discord.Color.from_rgb(201, 236, 160)
            )
        help_msg.add_field(name="**Команды пользователей**", value=user_help_list, inline=False)
        help_msg.add_field(name="**Команды модераторов**", value=adm_help_list1, inline=False)
        help_msg.add_field(name="Страница 2", value=adm_help_list2, inline=False)
        help_msg.set_footer(text="В скобках [] - обязательный аргумент\nВ скобках <> - необязательный")
        
        await ctx.send(embed=help_msg)
    else:
        cmd_name=cmd_name.lower()
        command_names=["embed", "set_welcome", "set_leave"]
        command_descs=[
            ("**Описание:** позволяет отправить сообщение в рамке, имеет ряд настроек кастомизации такого сообщения.\n"
             "**Применение:**\n"
             "> `==Заголовок==` - *создаёт заголовок*\n"
             "> `=Текст=` - *создаёт основной текст под заголовком*\n"
             "> `+URL+` - *добавляет мал. картинку в правый верхний угол*\n"
             "> `++URL++` - *добавляет большую картинку под текстом*\n"
             "> `##Цвет из списка##` - *подкрашивает рамку цветом из списка*\n"
             "**Список цветов:** `[red, blue, green, gold, teal, magenta]`\n"
             "**Все эти опции не обязательны, можно отправить хоть пустую рамку**\n"
             f"**Пример:** {p}embed\n==Server update!==\n=Added **Moderator** role!=\n"),
            ("**Описание:** позволяет настроить приветственные действия с только что присоединившимся участником, имеет 3 раздела настроек\n"
             f"**Применение:** **{p}set_welcome [**раздел**] [**аргументы / delete**]**\n"
             "**Разделы:** `message, channel, roles`\n"
             "Раздел `message`:\n"
             "> Этот раздел требует ввести сообщение, которым будет приветствоваться каждый прибывший на сервер\n"
             "> Чтобы в сообщении упоминался прибывший, напишите `==user==` в том месте, где он должен быть упомянут\n"
             "> Чтобы отображалось название сервера, напишите `==server==` в нужном Вам месте\n"
             f"*Пример: {p}set_welcome message Добро пожаловать на сервер ==server==, ==user==!*\n"
             "Раздел `channel`:\n"
             "> Этот раздел требует канал (или его ID) для приветствий\n"
             f"*Пример: {p}set_welcome channel {ctx.channel.id}*\n"
             "Раздел `roles`\n"
             "> Этот раздел требует список ролей (или их ID), которые будут выдаваться каждому участнику при входе\n"
             "> Для удаления конкретных ролей из уже настроенных таким образом, напишите `delete` вместо списка ID\n"
             f"*Пример: {p}set_welcome roles {'123'*6}*\n\n"
             f"**Как удалить уже настроенные действия?**\n**{p}set_welcome [**Раздел**] delete**\n"),
            ("**Описание:** позволяет настроить отчёт о выходе участника с сервера, имеет 2 раздела настроек\n"
             f"**Применение:** **{p}set_leave [**раздел**] [**аргумент / delete**]**\n"
             "**Разделы:** `message, channel`\n"
             "Раздел `message`:\n"
             "> Этот раздел требует ввести сообщение, которое будет отправляться в случае выхода участника с сервера\n"
             "> Чтобы в сообщении упоминался вышедший, напишите `==user==` в том месте, где он должен быть упомянут\n"
             "> Чтобы отображалось название сервера, напишите `==server==` в нужном Вам месте\n"
             f"*Пример: {p}set_leave message ==user== вышел с сервера ==server==*\n"
             "Раздел `channel`:\n"
             "> Этот раздел требует канал (или его ID) для приветствий\n"
             f"*Пример: {p}set_leave channel {ctx.channel.id}*\n\n"
             f"**Как удалить уже настроенные действия?**\n**{p}set_leave [**Раздел**] delete**\n")
                       ]
        
        if not cmd_name in command_names:
            reply=discord.Embed(
                title="❌Не найден модуль",
                description="Возможно для этого модуля нет подробного описания, или же он не существует",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            cmd_num=command_names.index(cmd_name)
            help_msg=discord.Embed(
                title=f"Описание {p}{cmd_name}",
                description=command_descs[cmd_num],
                color=discord.Color.from_rgb(201, 236, 160)
            )
            await ctx.send(embed=help_msg)

@client.command()
async def set_log_channel(ctx, raw_channel):
    channel=await detect_channel(ctx.guild, raw_channel)
    if channel=="Error":
        await ctx.send("Канал не найден")
    else:
        await post_data("log-channels", [str(ctx.guild.id), str(channel.id)])
        reply=discord.Embed(
            title="Настройка завершена",
            description=f"Канал для логов успешно настроен как {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=reply)

@client.command()
async def remove_log_channel(ctx, raw_channel):
    channel=await detect_channel(ctx.guild, raw_channel)
    if channel=="Error":
        await ctx.send("Канал не найден")
    else:
        await delete_data("log-channels", [str(ctx.guild.id), str(channel.id)])
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
            AbrList=['s','m','h','d']
            DurList=[1,60,3600,3600*24]
            Names=['сек.','мин.','ч.','сут.']
            
            if not raw_time[len(raw_time)-1] in AbrList:
                reply=discord.Embed(
                    title="❌Неверный формат",
                    description="Укажите время так: **[Число]m**\n\n**s** - секунды, **m** - минуты, **h** - часы, **d** - дни",
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
                    if time>86400*7:
                        await ctx.send("Мут не может быть осуществлён больше, чем на неделю")
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
                            if Mute in member.roles:
                                reply=discord.Embed(
                                    title="⚠Ошибка",
                                    description=f"Пользователь {member} уже заблокирован",
                                    color=discord.Color.gold()
                                )
                                await ctx.send(embed=reply)
                            else:
                                await member.add_roles(Mute)
                                await save_task("mute", ctx.guild, member, time)
                                
                                log=discord.Embed(
                                    title=':lock: Пользователь заблокирован',
                                    description=(f"**{member.mention}** был заблокирован на **{raw_time}** {stamp}\n"
                                                 f"Мут наложен пользователем {ctx.author.mention}\n"
                                                 f"**Причина:** {reason}"),
                                    color=discord.Color.darker_grey()
                                )
                                temp_log=await ctx.send(embed=log)
                                await post_log(ctx.guild, log)
                                await polite_send(member, f"Вам ограничили отправку сообщений на сервере **{ctx.guild.name}** на **{raw_time}** {stamp}\nПричина: {reason}")
                                
                                await temp_log.edit(delete_after=3)
                                
                                await asyncio.sleep(time)
                                
                                case=await delete_task("mute", ctx.guild, member)
                                if Mute in member.roles:
                                    await recharge(case)
                                    log=discord.Embed(
                                        title=':key: Пользователь разблокирован',
                                        description=(f"**{member.mention}** был разблокирован\n"
                                                     f"Ранне был заблокирован пользователем {ctx.author.mention}\n"
                                                     f"Причина: {reason}"),
                                        color=discord.Color.darker_grey()
                                    )
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
        else:
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
                    case=await delete_task("mute", ctx.guild, member)
                    await recharge(case)
                    log=discord.Embed(
                        title=':key: Пользователь разблокирован',
                        description=f'**{member.mention}** был разблокирован',
                        color=discord.Color.darker_grey()
                    )
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    
                    await temp_log.edit(delete_after=3)
                
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
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    await polite_send(member, f"Вы были кикнуты с сервера **{ctx.guild.name}**.\n**Причина:** {reason}")
                    
                    await temp_log.edit(delete_after=3)
                
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
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    await polite_send(member, f"Вы были забанены на сервере **{ctx.guild.name}**.\n**Причина:** {reason}")
                    
                    await temp_log.edit(delete_after=3)

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
            description="Укажите тег/ID пользователя",
            color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            unbanned=None
            banned_users=await ctx.guild.bans()
            for ban_entry in banned_users:
                user=ban_entry.user
                if str(user.id)==member or f"{user.name}#{user.discriminator}"==member:
                    unbanned=user
                    break
            if unbanned==None:
                await ctx.send(f"**{member}** нет в списке банов")
            else:
                case=await delete_task("ban", ctx.guild, unbanned)
                if case=="Error":
                    await ctx.guild.unban(user)
                else:
                    await recharge(case)
                log=discord.Embed(
                    title=f"**{member}** был разбанен",
                    description=f"Пользователь был разбанен администратором **{ctx.author}**",
                    color=discord.Color.dark_green()
                )
                temp_log=await ctx.send(embed=log)
                await post_log(ctx.guild, log)
                await polite_send(unbanned, f"Вы были разбанены на сервере **{ctx.guild.name}**")
                
                await temp_log.edit(delete_after=3)

@client.command()
async def tempban(ctx, raw_user, raw_time, *, reason=""):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    member=await detect_member(ctx.guild, raw_user)
    if member=="Error":
        reply=discord.Embed(
            title="❌Пользователь не найден",
            description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
            color=discord.Color.red()
            )
        await ctx.send(embed=reply)
        
    else:  
        if not await can_ban(ctx.author, ctx.guild):
            reply=discord.Embed(
                title="❌Недостаточно прав",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            AbrList=['s','m','h','d','w']
            DurList=[1,60,3600,86400,604800]
            Names=['сек.','мин.','ч.','сут.','нед.']
            
            if not raw_time[len(raw_time)-1] in AbrList:
                reply=discord.Embed(
                    title="❌Неверный формат",
                    description="Укажите время так: **[Число]m**\n\n**s** - секунды, **m** - минуты, **h** - часы, **d** - дни",
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
                    if time>604800*7:
                        await ctx.send("Бан не может быть осуществлён больше, чем на 7 недель")
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
                            await save_task("ban", ctx.guild, member, time)
                            await member.ban(reason=reason)
                            
                            log=discord.Embed(
                                title=f"**{member}** был забанен",
                                description=f"**Причина:** {reason}\n**Забанен пользователем:** {ctx.author.mention}\n**Длительность:** {raw_time} {stamp}",
                                color=discord.Color.dark_red()
                            )
                            temp_log=await ctx.send(embed=log)
                            await post_log(ctx.guild, log)
                            await polite_send(member, f"Вы были забанены на сервере **{ctx.guild.name}**.\n**Причина:** {reason}\n**Длительность:** {raw_time} {stamp}")
                            
                            await temp_log.edit(delete_after=3)
                            
                            await asyncio.sleep(time)
                            
                            case=await delete_task("ban", ctx.guild, member)
                            await recharge(case)
                            log=discord.Embed(
                                title=f"**{member}** был разбанен",
                                description=f"**Ранее был забанен модератором:** {ctx.author.mention}\n**Длительность:** {raw_time} {stamp}",
                                color=discord.Color.dark_green()
                            )
                            await post_log(ctx.guild, log)
                            await polite_send(member, f"Вы были разбанены на сервере **{ctx.guild.name}**")
    
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
    if not await has_helper(ctx.author, ctx.guild):
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
            temp_log=await ctx.send(embed=log)
            await post_log(ctx.guild, log)
            await polite_send(member, f"Вы были предупреждены на сервере **{ctx.guild}** модератором {ctx.author.mention}\nПричина: {reason}")
            
            await temp_log.edit(delete_after=3)
            
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
            reply.add_field(name=f"{user}\nID: {user_id}", value=f"Причина: {reason}", inline=False)
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
            temp_log=await ctx.send(embed=log)
            await post_log(ctx.guild, log)
            
            await temp_log.edit(delete_after=3)
    
@client.command()
async def clean_warn(ctx, raw_user, num):
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
            files=await get_raw_data("warns", [str(ctx.guild.id), str(member.id)])
            if not number(num):
                reply=discord.Embed(
                    title="❌Неверный номер варна",
                    description=f"Вы ввели **{num}**, но это не целое число",
                    color=discord.Color.red()
                )
                await ctx.send(embed=reply)
            else:
                num=int(num)
                if num<1 or num>len(files):
                    reply=discord.Embed(
                        title="❌Неверный номер варна",
                        description=f"Вы ввели **{num}**, но он слишком большой или меньше 1. Список варнов вызывается командой **'warns [**User**]**",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    raw_warn=files[num-1]
                    await raw_warn.delete()
                    reason=to_list(raw_warn.content)[3]
                    
                    log=discord.Embed(
                        title=f"✅ Предупреждение {num} снято",
                        description=f"Пользователь: {member}\nМодератор: {ctx.author}\nОписание: {reason}",
                        color=discord.Color.green()
                    )
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    
                    await temp_log.edit(delete_after=3)
    
@client.command(aliases=['clear','del'])
async def clean(ctx, n="1"):
    if await has_helper(ctx.author, ctx.guild):
        if not number(n):
            reply=discord.Embed(
                title='❌Неверно введено кол-во сообщений',
                description=f"Вы ввели **{n}**, подразумевая кол-во сообщений, но это не целое число",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            amount=int(n)+1
            await ctx.channel.purge(limit=amount)
            Deleted=discord.Embed(
                title=f':wastebasket: Удалены сообщения :wastebasket:',
                description=f'Удалено {n} последних сообщений',
                color=discord.Color.light_grey()
            )
            msg=await ctx.send(embed=Deleted)
            await asyncio.sleep(3)
            await msg.delete()
    else:
        NotAllowed=discord.Embed(
            title='❌Недостаточно прав',
            color=discord.Color.red()
        )
        await ctx.send(embed=NotAllowed)

@client.command(aliases=["raid", "post"])
async def post_raid(ctx, *, reqs="not provided"):
    channel=discord.utils.get(ctx.guild.channels, name="💳vip-server💳")
    raid_role=discord.utils.get(ctx.guild.roles, name="Raid Pings")
    if not channel in ctx.guild.channels:
        channel=ctx.message.channel
    if not raid_role in ctx.guild.roles:
        ment="@everyone"
    else:
        ment=f"{raid_role.mention}"
    msg=discord.Embed(
        title="🔔Raid notification🔔",
        description=(f"**Host:** {ctx.author.mention}\n"
                     f"**Requirements:** {reqs}\n"
                     f"**VIP:** {channel.mention}"),
        color=discord.Color.dark_red()
    )
    await ctx.send(content=ment, embed=msg)
    
@client.command()
async def embed(ctx, *, raw_text):
    head=detect_isolation(raw_text, "==")
    desc=detect_isolation(raw_text, "=")
    col=detect_isolation(raw_text, "##")
    thumb=detect_isolation(raw_text, "+")
    img=detect_isolation(raw_text, "++")
    if col!=[]:
        col=col[0].lower()
    else:
        col="None"
    
    col_names=["red", "blue", "green", "gold", "teal", "magenta"]
    colors=[discord.Color.red(), discord.Color.blue(), discord.Color.green(), discord.Color.gold(), discord.Color.teal(), discord.Color.magenta()]
    col_chosen=discord.Color.dark_grey()
    
    for i in range(len(col_names)):
        c=col_names[i]
        if col.find(c)!=-1:
            col_chosen=colors[i]
            break
    msg=discord.Embed(
        title=list_sum(head),
        description=list_sum(desc),
        color=col_chosen
    )
    if thumb!=[]:
        msg.set_thumbnail(url=thumb[0])
    if img!=[]:
        msg.set_image(url=img[0])
    await ctx.message.delete()
    await ctx.send(embed=msg)

@client.command()
async def set_welcome(ctx, categ, *, text="None"):
    global prefix
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await has_admin(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Ошибка",
            description="Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        
    else:
        #==========================Message========================
        if categ.lower()=="message":
            messages=await get_data("welcome-msg", [str(ctx.guild.id)])
            if text.lower()=="delete":
                if messages=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Приветственное сообщение не настроено",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await delete_data("welcome-msg", [str(ctx.guild.id)])
                    reply=discord.Embed(
                        title="✅ Приветственное сообщение удалено",
                        description=f"**Бывшее сообщение:** {messages[0][0]}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
            
            else:
                if messages!="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Приветственное сообщение уже есть:\n{messages[0][0]}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    if text==None:
                        text="Здравствуй, ==user==, добро пожаловать в ==server==!"
                    text=without_seps(text)
                    await post_data("welcome-msg", [str(ctx.guild.id), text])
                    reply=discord.Embed(
                        title="✅ Сообщение успешно настроено",
                        description=f"**Текст:** {text}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
        #========================Channel========================
        elif categ.lower()=="channel":
            if text.lower()=="delete":
                data=await get_raw_data("welcome-channels", [str(ctx.guild.id)])
                if data=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Канал для приветствий не настроен",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await data[0].delete()
                    data_list=to_list(data[0].content)
                    channel=discord.utils.get(ctx.guild.channels, id=int(data_list[1]))
                    reply=discord.Embed(
                        title="✅Канал отвязан",
                        description=f"Приветствия больше не присылаются в канал {channel.mention}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
                
            else:
                channel=await detect_channel(ctx.guild, text)
                if channel=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=(f"Вы указали {text} в качестве канала, но он не был найден. Попробуйте снова, указав канал\n"
                                     "Или напишите `delete`, чтобы удалить существующий"),
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await post_data("welcome-channels", [str(ctx.guild.id), str(channel.id)])
                    reply=discord.Embed(
                        title="✅ Канал успешно настроен",
                        description=f"Канал приветствий: {channel.mention}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
        #===================Roles======================
        elif categ.lower()=="roles":
            roles=await get_data("welcome-roles", [str(ctx.guild.id)])
            if text.lower().startswith("delete"):
                if roles=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Нет настроенных ролей",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    raw_roles=c_split(text, " ")
                    raw_roles.pop(0)
                    if raw_roles==[]:
                        await delete_data("welcome-roles", [str(ctx.guild.id)])
                        reply=discord.Embed(
                            title="✅ Роли не будут выдаваться",
                            description=f"Больше не будут выдаваться роли при приветствии",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=reply)
                    else:
                        deleted=[]
                        for raw_role in raw_roles:
                            role=await detect_role(ctx.guild, raw_role)
                            if str(role.id) in roles[0] and not role in deleted:
                                deleted.append(role)
                                await delete_data("welcome-roles", [str(ctx.guild.id), str(role.id)])
                        head="✅ Убраны роли из списка выдаваемых"
                        if deleted==[]:
                            head="❌Ошибка"
                        reply=discord.Embed(
                            title=head,
                            description=list_sum(deleted),
                            color=discord.Color.light_grey()
                        )
                        await ctx.send(embed=reply)
            else:
                if roles!="Error":
                    new_roles_id=roles[0]
                    new_roles=[discord.utils.get(ctx.guild.roles, id=int(elem)) for elem in new_roles_id]
                else:
                    roles=[]
                    new_roles=[]
                    new_roles_id=[]
                
                cant_add=[]
                raw_roles=c_split(text, " ")
                for raw_role in raw_roles:
                    role=await detect_role(ctx.guild, raw_role)
                    if not role in new_roles and role!="Error":
                        new_roles.append(role)
                        new_roles_id.append(str(role.id))
                        if role.position>=await glob_pos(bot_user):
                            if cant_add==[]:
                                cant_add.append("**Роли, которые я не в праве добавлять:**")
                            cant_add.append(f"> {role.name}; **ID:** {role.id}")
                if len(new_roles)==len(roles):
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description="Не распознано ни одной роли в списке, который Вы указали",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    new_data=[str(ctx.guild.id)]
                    new_data.extend(new_roles_id)
                    if roles==[]:
                        await post_data("welcome-roles", new_data)
                    else:
                        await edit_data("welcome-roles", [str(ctx.guild.id)], new_data)
                    reply=discord.Embed(
                        title="✅ Добавлены новые стартовые роли",
                        description=f"**Даются при входе:**\n{list_sum(new_roles)}\n{list_sum(cant_add)}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
            
        else:
            reply=discord.Embed(
                title="❌Ошибка",
                description=(f"Настройки **{categ}** нет. Список доступных настроек:\n"
                             "> `message`\n"
                             "> `channel`\n"
                             "> `roles`\n"
                             f"**Подробнее:** {prefix}help set_welcome"),
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)

@client.command()
async def welcome_info(ctx):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    str_ID_list=await get_data("welcome-roles", [str(ctx.guild.id)])
    if str_ID_list=="Error":
        role_list=["Не настроены"]
        cant_add=[]
    else:
        role_list=[]
        cant_add=["**Роли, выдавать которые я не имею права:**"]
        for str_ID in str_ID_list:
            ID=int(str_ID[0])
            role=discord.utils.get(ctx.guild.roles, id=ID)
            if role==None:
                await delete_data("welcome-roles", [str(ctx.guild.id), str_ID[0]])
            else:
                role_list.append(f"1) **{role.name}**")
                if role.position>=await glob_pos(bot_user):
                    cant_add.append(f"> {role.name}")
        if len(cant_add)<2:
            cant_add=[]
    
    w_channel_str_ID=await get_data("welcome-channels", [str(ctx.guild.id)])
    if w_channel_str_ID=="Error":
        channel_name="Не настроен"
    else:
        w_channel_ID=int(w_channel_str_ID[0][0])
        channel=discord.utils.get(ctx.guild.channels, id=w_channel_ID)
        if channel==None:
            await delete_data("welcome-channels", [str(ctx.guild.id), w_channel_str_ID[0][0]])
            channel_name="Удалён"
        else:
            channel_name=channel.mention
    
    w_message=await get_data("welcome-msg", [str(ctx.guild.id)])
    if w_message=="Error":
        msg_info="Не настроено"
    else:
        msg_info=w_message[0][0]
    reply=discord.Embed(
        title="Автоматические действия с пользователем",
        description=(f"**Роли:** {list_sum(role_list)}\n{list_sum(cant_add)}"
                     f"**Канал приветствий:** {channel_name}\n"
                     f"**Приветственное сообщение:**\n{msg_info}"),
        color=discord.Color.green()
    )
    await ctx.send(embed=reply)

@client.command()
async def set_leave(ctx, categ, *, text="None"):
    global prefix
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await has_admin(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Ошибка",
            description="Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        
    else:
        #==========================Message========================
        if categ.lower()=="message":
            messages=await get_data("leave-msg", [str(ctx.guild.id)])
            if text.lower()=="delete":
                if messages=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Сообщение для выхода участника не настроено",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await delete_data("leave-msg", [str(ctx.guild.id)])
                    reply=discord.Embed(
                        title="✅ Сообщение на выход участника удалено",
                        description=f"**Бывшее сообщение:** {messages[0][0]}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
            
            else:
                if messages!="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Сообщение для выхода участника уже есть:\n{messages[0][0]}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    if text==None:
                        text="==user== вышел с сервера"
                    text=without_seps(text)
                    await post_data("leave-msg", [str(ctx.guild.id), text])
                    reply=discord.Embed(
                        title="✅ Сообщение успешно настроено",
                        description=f"**Текст:** {text}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
        #========================Channel========================
        elif categ.lower()=="channel":
            if text.lower()=="delete":
                data=await get_raw_data("leave-channels", [str(ctx.guild.id)])
                if data=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=f"Канал для отчётов о выходе не настроен",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await data[0].delete()
                    data_list=to_list(data[0].content)
                    channel=discord.utils.get(ctx.guild.channels, id=int(data_list[1]))
                    reply=discord.Embed(
                        title="✅Канал отвязан",
                        description=f"Отчёты о выходе больше не присылаются в канал {channel.mention}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
                
            else:
                channel=await detect_channel(ctx.guild, text)
                if channel=="Error":
                    reply=discord.Embed(
                        title="❌Ошибка",
                        description=(f"Вы указали {text} в качестве канала, но он не был найден. Попробуйте снова, указав канал\n"
                                     "Или напишите `delete`, чтобы удалить существующий"),
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    await post_data("leave-channels", [str(ctx.guild.id), str(channel.id)])
                    reply=discord.Embed(
                        title="✅ Канал успешно настроен",
                        description=f"Канал для отчёта о выходах: {channel.mention}",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
        else:
            reply=discord.Embed(
                title="❌Ошибка",
                description=(f"Настройки **{categ}** нет. Список доступных настроек:\n"
                             "> `message`\n"
                             "> `channel`\n"
                             f"**Подробнее:** {prefix}help set_leave"),
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)

@client.command(aliases=["rr"])
async def reaction_roles(ctx, *, heading="Получите роли"):
    global prefix
    
    if not await has_admin(ctx.author, ctx.guild):
        reply=discord.Embed(
            title="❌Ошибка",
            description="Недостаточно прав",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    else:
        reply=discord.Embed(
            title="Настройка роли за реакцию: канал",
            description="Пожалуйста, укажите канал, в котором я должен опубликовать объявление",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=reply)
        read_status="active"
        
        channel=None
        emoji_role=[]
        
        while read_status!="stop":
            msg=await read_message(ctx.channel, ctx.author, 60)
            if msg=="Timeout":
                msg="stop"
            else:
                msg=msg.content
            if msg.lower()=="stop" or msg.lower()==prefix:
                read_status="stop"
            else:
                raw_search=c_split(msg, " ")[0]
                channel=await detect_channel(ctx.guild, raw_search)
                if channel=="Error":
                    reply=discord.Embed(
                        title="Настройка роли за реакцию: канал",
                        description=f"Вы указали **{raw_search}** в качестве канала, но он не был найден. Попробуйте снова, или напишите `stop` для отмены",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=reply)
                else:
                    read_status="stop"
                    
        if channel!=None:
            reply=discord.Embed(
                title="Настройка роли за реакцию: реакция и роль",
                description="Пожалуйста, напишите 1 **эмодзи** (для реакции) и 1 **роль** (или ID) через пробел\nКогда закончите, напишите `stop`",
                color=discord.Color.blurple()
            )
            await ctx.send(embed=reply)
            read_status="active"
            
            while read_status!="stop":
                msg=await read_message(ctx.channel, ctx.author, 60)
                if msg=="Timeout":
                    msg="stop"
                else:
                    msg=msg.content
                if msg.lower()=="stop" or msg.lower()==prefix:
                    read_status="stop"
                else:
                    data=c_split(msg, " ")
                    raw_emoji=data[0]
                    raw_role=data[1]
                    emoji=await detect_emoji(ctx.guild, raw_emoji)
                    role=await detect_role(ctx.guild, raw_role)
                    if emoji=="Error":
                        reply=discord.Embed(
                            title="Настройка роли за реакцию: реакция",
                            description=f"Вы указали {raw_emoji} в качестве эмодзи, но оно не было найдено. Попробуйте снова, или напишите `stop` для отмены",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=reply)
                    elif role=="Error":
                        reply=discord.Embed(
                            title="Настройка роли за реакцию: роль",
                            description=f"Вы указали {raw_role} в качестве роли, но она не была найдена. Попробуйте снова, или напишите `stop` для отмены",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=reply)
                    else:
                        if role.position>=await glob_pos(ctx.author):
                            reply=discord.Embed(
                                title="❌ Эта роль выше Вашей",
                                description=f"Роль <@&{role.id}> выше вашей максимальной роли на этом сервере. Попробуйте снова с другой ролью, или напишите `stop` для отмены",
                                color=discord.Color.red()
                            )
                            await ctx.send(embed=reply)
                        else:
                            emoji_role.append([emoji, role])
                            reply=discord.Embed(
                                title="✅ Добавлено",
                                description=f"Роль <@&{role.id}> за нажатие на {emoji}. Продолжайте добавлять роли, или напишите `stop` для отмены",
                                color=discord.Color.green()
                            )
                            await ctx.send(embed=reply)
                            
            #============After cycle=============
            if emoji_role!=[]:
                half_to_post=[]
                desc=""
                for twin in emoji_role:
                    desc+=f"{twin[0]} - **<@&{twin[1].id}>**\n"
                    half_to_post.extend([twin[0], str(twin[1].id)])
                
                table=discord.Embed(
                    title=heading,
                    description=desc,
                    color=discord.Color.gold()
                )
                frame=await channel.send(embed=table)
                for twin in emoji_role:
                    emoji=twin[0]
                    await frame.add_reaction(emoji)
                
                to_post=[str(ctx.guild.id), str(frame.id)]
                to_post.extend(half_to_post)
                
                await post_data("reaction-roles", to_post)
                
                reply=discord.Embed(
                    title="✅ Вы успешно настроили реакции за роли",
                    description=f"Посмотрите на результат: {channel.mention}",
                    color=discord.Color.green()
                )
                await ctx.send(embed=reply)
    
@client.command(aliases=["as", "translit", "t"])
async def altshift(ctx, *, text=None):
    global prefix
    if text==None:
        reply=discord.Embed(
            title="Введите текст",
            description=f"Например **{prefix}altshift ytgkj[j lf&",
            color=discord.Color.teal()
        )
        await ctx.send(embed=reply)
    else:
        rus="йцукенгшщзхъфывапролджэячсмитьбю.ё1234567890-=ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,Ё!'№;%:?*()_+"
        eng="qwertyuiop[]asdfghjkl;'zxcvbnm,./`1234567890-=QWERTYUIOP{}ASDFGHJKL:'|ZXCVBNM<>?~!@#$%^&*()_+"
        out=""
        rus_amount=0
        eng_amount=0
        for letter in text:
            if (letter in rus) and (letter in eng):
                if rus_amount>eng_amount:
                    out+=eng[rus.index(letter)]
                else:
                    out+=rus[eng.index(letter)]
            elif letter in rus:
                ind=rus.index(letter)
                out+=eng[ind]
                rus_amount+=1
            elif letter in eng:
                ind=eng.index(letter)
                out+=rus[ind]
                eng_amount+=1
            else:
                out+=letter
        result=discord.Embed(
            title="Alt+Shift",
            description=out,
            color=discord.Color.blue()
        )
        await ctx.send(embed=result)
        
@client.command(aliases=["av", "pfp"])
async def avatar(ctx, *, raw_user=None):
    if raw_user==None:
        user=ctx.author
    else:
        user=await detect_member(ctx.guild, raw_user)
    reply=discord.Embed(
        title=f"Аватарка {user}",
        color=discord.Color.greyple()
    )
    reply.set_image(url=str(user.avatar_url))
    await ctx.send(embed=reply)
    
@client.command(aliases=["sg", "gcreate", "create"])
async def set_giveaway(ctx):
    global prefix
    
    channel="Error"
    lets_start=discord.Embed(
        title="🎉 Настройка giveaway",
        description="Пожалуйста, укажите канал, в котором будет опубликована раздача",
        color=discord.Color.magenta()
    )
    await ctx.send(embed=lets_start)
    
    while True:
        msg=await read_message(ctx.channel, ctx.author, 60)
        if msg=="Timeout":
            break
        else:
            raw_channel=msg.content
            if raw_channel.lower()=="stop" or raw_channel==prefix:
                break
            else:
                channel=await detect_channel(ctx.guild, raw_channel)
                if channel=="Error":
                    reply=discord.Embed(
                        title="⚠ Канал не найден",
                        description=f"Вы указали {raw_channel}, подразумевая канал, но он не был найден. Попробуйте снова, или напишите `stop` для отмены",
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=reply)
                else:
                    reply=discord.Embed(
                        title="✅ Канал выбран",
                        description=f"Когда Вы закончите настройку, раздача начнётся в канале {channel.mention}. Теперь, пожалуйста, укажите время. Пример правильного формата: **5m**",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=reply)
                    break
    
    if channel!="Error":
        time=None
        headings=["сек.", "мин.", "ч.", "сут.", "нед."]
        names=["s", "m", "h", "d", "w"]
        weights=[1, 60, 3600, 86400, 604800]
        while True:
            msg=await read_message(ctx.channel, ctx.author, 60)
            if msg=="Timeout":
                break
            else:
                raw_time=msg.content.lower()
                if raw_time=="stop" or raw_time==prefix:
                    break
                else:
                    raw_name=raw_time[len(raw_time)-1]
                    if not raw_name in names:
                        reply=discord.Embed(
                            title="⚠ Нарушен формат времени",
                            description=(f"Время должно быть в таком формате, как здесь: **5m**\n"
                                         "s - секунда, m - минута, h - час, d - день, w - неделя. Попробуйте снова, или напишите `stop` для отмены"),
                            color=discord.Color.gold()
                        )
                        await ctx.send(embed=reply)
                    else:
                        name=names.index(raw_name)
                        raw_weight=raw_time[0:len(raw_time)-1]
                        if not number(raw_weight):
                            reply=discord.Embed(
                                title="⚠ Нарушен формат времени",
                                description=(f"**{raw_weight}** должно быть целым числом. Попробуйте снова, или напишите `stop` для отмены"),
                                color=discord.Color.gold()
                            )
                            await ctx.send(embed=reply)
                        else:
                            weight=int(raw_weight)
                            time=weight*weights[name]
                            if time<0 or time>3.1E6:
                                reply=discord.Embed(
                                    title="⚠ Превышен лимит",
                                    description=(f"Длительность раздачи не может быть дольше, чем 5 недель. Попробуйте снова, или напишите `stop` для отмены"),
                                    color=discord.Color.gold()
                                )
                                await ctx.send(embed=reply)
                                time=None
                            else:
                                reply=discord.Embed(
                                    title="✅ Время настроено",
                                    description=f"Раздача будет длиться **{weight} {headings[name]}**. Теперь, пожалуйста, укажите число победителей от 1 до 20",
                                    color=discord.Color.green()
                                )
                                await ctx.send(embed=reply)
                                break
                            
        if time!=None:
            winner_num=None
            while True:
                msg=await read_message(ctx.channel, ctx.author, 60)
                if msg=="Timeout":
                    break
                else:
                    raw_num=msg.content.lower()
                    if raw_num=="stop" or raw_num==prefix:
                        break
                    else:
                        if not number(raw_num):
                            reply=discord.Embed(
                                title="⚠ Ошибка",
                                description=(f"**{raw_num}** должно быть целым числом. Попробуйте снова, или напишите `stop` для отмены"),
                                color=discord.Color.gold()
                            )
                            await ctx.send(embed=reply)
                            winner_num=None
                        else:
                            winner_num=int(raw_num)
                            if winner_num<1 or winner_num>20:
                                reply=discord.Embed(
                                    title="⚠ Ошибка",
                                    description=(f"Кол-во победителей не должно превышать 20, а еще не быть отрицательным :). Попробуйте снова, или напишите `stop` для отмены"),
                                    color=discord.Color.gold()
                                )
                                await ctx.send(embed=reply)
                                winner_num=None
                            else:
                                reply=discord.Embed(
                                    title="✅ Количество победителей настроено",
                                    description=f"Теперь можете написать, что именно Вы разыгрываете, не стесняйтесь",
                                    color=discord.Color.green()
                                )
                                await ctx.send(embed=reply)
                                break
            
            if winner_num!=None:
                prize=None
                msg=await read_message(ctx.channel, ctx.author, 120)
                if msg=="Timeout":
                    return
                else:
                    prize=msg.content
                    if prize.lower()=="stop" or prize.lower()==prefix:
                        return
                    else:
                        give_embed=discord.Embed(
                            title="🎉 Конкурс 🎉",
                            description=(f"**Приз:** {prize}\n"
                                         f"**Кол-во победителей:** {winner_num}\n"
                                         f"**Длительность:** {weight} {headings[name]}\n"
                                         f"**Хост:** {ctx.author.mention}"),
                            color=discord.Color.magenta()
                        )
                        give_msg=await channel.send(embed=give_embed)
                        await give_msg.add_reaction("🎉")
                        await save_giveaway(ctx.guild, give_msg, winner_num, ctx.author, prize, time)
                        
                        reply=discord.Embed(
                            title="🎉 Вы начали раздачу!",
                            description=(f"Посмотрите на результат в {channel.mention}"),
                            color=discord.Color.magenta()
                        )
                        await ctx.send(embed=reply)
                        
                        await asyncio.sleep(time)
                        await finish_giveaway(give_msg)

#===================Events==================
@client.event
async def on_member_join(member):
    await refresh_mute(member)
    await send_welcome(member)
    await users(member.guild)
    
@client.event
async def on_member_remove(member):
    await users(member.guild)
    await send_leave(member)

@client.event
async def on_raw_reaction_add(data):
    global bot_id
    
    pairs=await get_data("reaction-roles", [str(data.guild_id), str(data.message_id)])
    if pairs!="Error":
        pairs=pairs[0]
        es=[]
        rs=[]
        emoji=str(data.emoji)
        guild=client.get_guild(data.guild_id)
        for i in range(0, len(pairs), 2):
            es.append(pairs[i])
            rs.append(pairs[i+1])
        if emoji in es and data.user_id!=bot_id:
            member=discord.utils.get(guild.members, id=data.user_id)
            
            ind=es.index(emoji)
            ID=int(rs[ind])
            role=discord.utils.get(guild.roles, id=ID)
            if role!=None:
                await member.add_roles(role)
                await polite_send(member, f"Вам была выдана роль **{role}** на сервере **{guild}**")
            
@client.event
async def on_raw_reaction_remove(data):
    global bot_id
    
    pairs=await get_data("reaction-roles", [str(data.guild_id), str(data.message_id)])
    if pairs!="Error":
        pairs=pairs[0]
        es=[]
        rs=[]
        emoji=str(data.emoji)
        guild=client.get_guild(data.guild_id)
        for i in range(0, len(pairs), 2):
            es.append(pairs[i])
            rs.append(pairs[i+1])
        if emoji in es and data.user_id!=bot_id:
            member=discord.utils.get(guild.members, id=data.user_id)
            
            ind=es.index(emoji)
            ID=int(rs[ind])
            role=discord.utils.get(guild.roles, id=ID)
            if role!=None:
                if role in member.roles:
                    await member.remove_roles(role)
                    await polite_send(member, f"У Вас была снята роль **{role}** на сервере **{guild}**")

@client.event
async def on_raw_message_delete(data):
    files=await get_raw_data("reaction-roles", [str(data.guild_id), str(data.message_id)])
    if files!="Error":
        for file in files:
            await file.delete()
    
    g_files=await get_raw_data("giveaways", ["None", str(data.guild_id), str(data.message_id)])
    if g_files!="Error":
        for g_file in g_files:
            g_file.delete()

#=====================Errors==========================
@mute.error
async def mute_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=f"Формат: **{prefix}mute [**Упомянуть участника**] [**Время**] [**Причина**]**\nНапример:\n**'mute @Player#0000 5m**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@unmute.error
async def unmute_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=f"Формат: **{prefix}unmute [**Упомянуть участника**]**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        
@kick.error
async def kick_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**{prefix}kick [**@Player#0000**] [**Причина**]**\nНапример:\n**'kick @Player#0000 спам**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
@ban.error
async def ban_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**{prefix}ban [**@Player#0000**] [**Причина**]**\nНапример:\n**'ban @Player#0000 порнография**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)

@set_log_channel.error
async def set_log_channel_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**{prefix}set_log_channel [**ID канала**]**\nНапример:\n**'set_log_channel {ctx.channel.id}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
        
@remove_log_channel.error
async def remove_log_channel_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=f"Попробуйте снова, следуя формату\n**{prefix}remove_log_channel [**ID канала**]**\nНапример:\n**'remove_log_channel {ctx.channel.id}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)

@tempban.error
async def tempban_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=f"Формат: **{prefix}tempban [**Упомянуть участника/ID**] [**Время**] [**Причина**]**\nНапример:\n**'tempban @Player#0000 5m спам**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
@clean_warn.error
async def clean_warn_error(ctx, error):
    global prefix
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=f"Формат: **{prefix}clean_warn [**Упомянуть участника/ID**] [**Номер варна**]**\nНапример:\n**'clean_warn @Player#0000 1**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
#===========Tasks=========
async def task_refresh():
    while True:
        await client.wait_until_ready()
        cases=await clean_past_tasks()
        for case in cases:
            await recharge(case)
            guild=client.get_guild(int(case[1]))
            member=client.get_user(int(case[2]))
            if case[0]=="mute":
                log=discord.Embed(
                    title=':key: Пользователь разблокирован',
                    description=f'**{member.mention}** был разблокирован',
                    color=discord.Color.darker_grey()
                )
                await post_log(guild, log)
            elif case[0]=="ban":
                log=discord.Embed(
                    title=f"**{member}** был разбанен",
                    color=discord.Color.dark_green()
                )
                await post_log(guild, log)
                await polite_send(member, f"Вы были разбанены на сервере **{guild.name}**")
        await reset_tasks()
        data=await closest_inactive_task()
        
        if data!="Error":
            delay=data[1]
            case=data[0]
            await asyncio.sleep(delay)
            guild=client.get_guild(int(case[1]))
            member=client.get_user(int(case[2]))
            case=await delete_task(case[0], guild, member)
            await recharge(case)
            if case[0]=="mute":
                log=discord.Embed(
                    title=':key: Пользователь разблокирован',
                    description=f'**{member.mention}** был разблокирован',
                    color=discord.Color.darker_grey()
                )
                await post_log(guild, log)
            elif case[0]=="ban":
                log=discord.Embed(
                    title=f"**{member}** был разбанен",
                    color=discord.Color.dark_green()
                )
                await post_log(guild, log)
                await member.send(f"Вы были разбанены на сервере **{guild.name}**")
        else:
            break
    return
    
client.loop.create_task(task_refresh())

async def giveaway_refresh():
    await client.wait_until_ready()
    await reset_giveaways()
    while True:
        messages=await clean_past_giveaways()
        for msg in messages:
            await finish_giveaway(msg)
        
        active_g=await closest_giveaway()
        if active_g=="Error":
            break
        else:
            message=active_g[0]
            time=active_g[1]
            
            await asyncio.sleep(time)
            
            await finish_giveaway(message)
    return
    
client.loop.create_task(giveaway_refresh())

@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.MissingRequiredArgument):
        return

client.run(str(os.environ.get('SIRIUS_TOKEN')))
