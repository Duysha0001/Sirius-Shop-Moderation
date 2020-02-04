import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import requests
import datetime
import json
import os
from emoji import UNICODE_EMOJI
import random

prefix = "'"
client=commands.Bot(command_prefix = prefix)

db_id = 653160213607612426

users_timers={"small": {}, "big": {}}
message_buffer={}

mute_role_name="Мут"

client.remove_command('help')

#=========Events ready============
@client.event
async def on_ready():
    print(">> Bot is ready\n"
          f">> Current bot user: {client.user}\n"
          f">> Current prefix: {prefix}")

#========Backup functions===========
def role_to_dict(role):
    data = {
        "name": role.name,
        "color": role.color.value,
        "hoist": role.hoist,
        "mentionable": role.mentionable,
        "permissions": role.permissions.value
    }
    return data

def tc_to_dict(text_channel):
    data = {
        "name": text_channel.name,
        "topic": text_channel.topic,
        "slowmode_delay": text_channel.slowmode_delay,
        "is_nsfw": text_channel.is_nsfw(),
        "overwrites": overwrites_to_list(text_channel)
    }
    return data

def vc_to_dict(voice_channel):
    data = {
        "name": voice_channel.name,
        "user_limit": voice_channel.user_limit,
        "overwrites": overwrites_to_list(voice_channel)
    }
    return data

def category_to_dict(category):
    data = {
        "name": category.name,
        "overwrites": overwrites_to_list(category),
        "text_channels": [tc_to_dict(tc) for tc in category.text_channels],
        "voice_channels": [vc_to_dict(vc) for vc in category.voice_channels]
    }
    return data

def overwrites_to_list(channel):
    array = []
    overwrites = channel.overwrites
    for obj in overwrites:
        if obj in channel.guild.roles:
            array.append({"role": obj.name, "overwrites": perms_to_values(overwrites[obj])})
    return array

def perms_to_values(overwrite):
    raw_pair = overwrite.pair()
    pair = (raw_pair[0].value, raw_pair[1].value)
    return pair
    
def from_pair_values(value_pair):
    perm_1 = discord.Permissions(permissions = value_pair[0])
    perm_2 = discord.Permissions(permissions = value_pair[1])
    overwrite = discord.PermissionOverwrite.from_pair(perm_1, perm_2)
    return overwrite

def list_to_overwrites(List, guild):
    overwrites = {}
    pairs = []
    for payload in List:
        name = payload["role"]
        pair = payload["overwrites"]
        role = discord.utils.get(guild.roles, name = name)
        if role in guild.roles:
            pairs.append((role, from_pair_values(pair)))
    overwrites.update(pairs)
    return overwrites

async def restore_text_channels(special_list, guild, categ = None):
    if categ == None:
        categ = guild
    for tcd in special_list:
        name = tcd["name"]
        channel = discord.utils.get(guild.text_channels, name = name)
        if not channel in categ.text_channels:
            try:
                await categ.create_text_channel(
                    name = name,
                    topic = tcd["topic"],
                    slowmode_delay = tcd["slowmode_delay"],
                    is_nsfw = tcd["is_nsfw"],
                    overwrites = list_to_overwrites(tcd["overwrites"], guild)
                )
            except BaseException:
                pass
    return

async def restore_voice_channels(special_list, guild, categ = None):
    if categ == None:
        categ = guild    
    for vcd in special_list:
        name = vcd["name"]
        channel = discord.utils.get(guild.voice_channels, name = name)
        if not channel in categ.voice_channels:
            try:
                await categ.create_voice_channel(
                    name = name,
                    user_limit = vcd["user_limit"],
                    overwrites = list_to_overwrites(vcd["overwrites"], guild)
                )
            except BaseException:
                pass
    return

#========Token DEF functions=========
#========Token SYNC DEF functions=====
async def get_token(guild):
    results = await get_data("token-emojis", [str(guild.id)])
    if results == "Error":
        return "💰"
    else:
        return results[0][0]

async def role_review(member, bal):
    files = await get_raw_data("auto-pay-roles", [str(member.guild.id)])
    if files != "Error":
        for file in files:
            result = to_list(file.content)
            req_tokens = int(result[1])
            if bal >= req_tokens:
                role_id = int(result[2])
                role = discord.utils.get(member.guild.roles, id = role_id)
                if role == None:
                    await file.delete()
                elif not role in member.roles:
                    await member.add_roles(role)
    
    files = await get_raw_data("auto-remove-roles", [str(member.guild.id)])
    if files != "Error":
        for file in files:
            result = to_list(file.content)
            req_tokens = int(result[1])
            if bal >= req_tokens:
                role_id = int(result[2])
                role = discord.utils.get(member.guild.roles, id = role_id)
                if role == None:
                    await file.delete()
                elif role in member.roles:
                    await member.remove_roles(role)
    return
    
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
                await file.delete()
                
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

async def access_folder(folder):
    global db_id
    db_server=client.get_guild(db_id)
    
    folder = discord.utils.get(db_server.channels, name=folder)
    
    if not folder in db_server.channels:
        return "Error"
    else:
        return folder

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
    for letter in word:
        if letter.lower() in ethalone:
            out+=1
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

def list_sum(List, insert = "\n"):
    out=""
    for elem in List:
        out += str(insert) + str(elem)
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

def count(a_list, elem):
    out=0
    for e in a_list:
        if e==elem:
            out+=1
    return out

def compare(List, lower_bound, upper_bound):
    out=True
    for l in List:
        if not (l>=lower_bound and l<=upper_bound):
            out=False
            break
    return out

def pages(list_len, interval):
    out=list_len//interval
    return out+1 if list_len%interval>0 else out

def expand_delta(delta):
    delta_sec=delta.seconds
    sec=delta_sec%60
    delta_min=delta_sec//60
    mins=delta_min%60
    delta_hours=delta_min//60
    hours=delta_hours%24
    delta_days=delta.days
    days=delta_days%7
    weeks=delta_days//7
    return [weeks, days, hours, mins, sec]

def delta_to_words(delta):
    delta_list=expand_delta(delta)
    t=["нед.", "сут.", "ч.", "мин.", "сек."]
    to_print=""
    for elem in delta_list:
        if elem!=0:
            ind=delta_list.index(elem)
            to_print+=f" {elem} {t[ind]}"
    return to_print[1:len(to_print)]

def spamm(guild, user, message):
    global message_buffer
    
    text=message.content
    now=datetime.datetime.now()
    weight=len(text)
    
    new_user={
            "dust": {
                "sent": 0,
                "last_at": None,
                "messages": []
                },
            "blocks": {
                "sent": 0,
                "last_at": None,
                "messages": []         
                },
            "other": {
                "sent": 0,
                "last_at": None,
                "messages": []
                }
        }
    
    categs={
        "dust": {
            "timelim": 1,
            "numlim": 7
            },
        "blocks": {
            "timelim": 10,
            "numlim": 4
            },
        "other": {
            "timelim": 2,
            "numlim": 7
            }
    }
    
    if weight>500:
        categ="blocks"
    elif weight<7:
        categ="dust"
    else:
        categ="other"
        
    new_user[categ]["sent"]+=1
    new_user[categ]["ticks"]=now
    new_user[categ]["messages"].append({"id": message.id, "channel_id": message.channel.id})
    
    if not f"{guild.id}" in message_buffer:
        message_buffer.update([(f"{guild.id}", {f"{user.id}": new_user})])
        return [False]
    elif not f"{user.id}" in message_buffer[f"{guild.id}"]:
        message_buffer[f"{guild.id}"].update([(f"{user.id}", new_user)])
        return [False]
    else:
        
        spam=message_buffer[f"{guild.id}"][f"{user.id}"][categ]
        
        last_tick=spam["last_at"]
        if last_tick==None:
            last_tick=now
        delta = now-last_tick
        
        message_buffer[f"{guild.id}"][f"{user.id}"][categ]["last_at"]=now
        message_buffer[f"{guild.id}"][f"{user.id}"][categ]["messages"].append({"id": message.id, "channel_id": message.channel.id})
            
        if delta.seconds <= categs[categ]["timelim"]:
            if spam["sent"]>=categs[categ]["numlim"]:
                message_buffer[f"{guild.id}"][f"{user.id}"][categ]["sent"]=1
                to_delete=message_buffer[f"{guild.id}"][f"{user.id}"][categ]["messages"]
                message_buffer[f"{guild.id}"][f"{user.id}"][categ]["messages"]=[{"id": message.id, "channel_id": message.channel.id}]
                return [True, to_delete]
            
            else:
                message_buffer[f"{guild.id}"][f"{user.id}"][categ]["sent"]+=1
                return [False]
        else:
            if spam["sent"]>1:
                message_buffer[f"{guild.id}"][f"{user.id}"][categ]["sent"]-=1
            return [False]

def get_user(text):
    IDs=all_ints(text)
    if IDs==[]:
        ID=None
    else:
        ID=IDs[0]
    user=client.get_user(ID)
    return user

def perms_for(role):
    owned = {
    "create_instant_invite": role.permissions.create_instant_invite,
    "kick_members": role.permissions.kick_members,
    "ban_members": role.permissions.ban_members,
    "administrator": role.permissions.administrator,
    "manage_channels": role.permissions.manage_channels,
    "manage_roles": role.permissions.manage_roles,
    "manage_guild": role.permissions.manage_guild,
    "view_audit_log": role.permissions.view_audit_log,
    "change_nickname": role.permissions.change_nickname,
    "manage_nicknames": role.permissions.manage_nicknames,
    "manage_webhooks": role.permissions.manage_webhooks,
    "manage_messages": role.permissions.manage_messages,
    "manage_emojis": role.permissions.manage_emojis,
    "mention_everyone": role.permissions.mention_everyone
    }
    return owned

def has_permissions(member, perm_array):
    to_have = len(perm_array)
    if member.id == member.guild.owner_id:
        return True
    else:
        found_num = 0
        found = []
        for role in member.roles:
            owned = perms_for(role)
            if owned["administrator"]:
                found_num = to_have
            else:
                for perm in perm_array:
                    if not perm in found and owned[perm]:
                        found.append(perm)
                        found_num += 1
            if found_num >= to_have:
                break
                    
        return True if found_num >= to_have else False

def has_roles(member, role_array):
    has_them = True
    if not has_permissions(member, ["administrator"]):
        for role in role_array:
            if not role in member.roles:
                has_them = False
                break
    return has_them
    
def user_position(user):
    pos=0
    for r in user.roles:
        if r.position > pos:
            pos = r.position
    return pos

def to_member(guild, user_id):
    member = discord.utils.get(guild.members, id = user_id)
    return member
    
def lack_of_perms_msg(perm_name_list):
    reply = discord.Embed(
        title = "🛠 Недостаточно прав",
        description = ("**Требуемые права:**\n"
                       f"{list_sum(perm_name_list)}")
    )
    return reply
    
def paral_sort(names, values):
    length = len(values)
    for i in range(length):
        max_val = values[i]
        max_ind = i
        for j in range(i, length):
            if values[j] > max_val:
                max_val = values[j]
                max_ind = j
        max_name = names[max_ind]
        names[max_ind] = names[i]
        names[i] = max_name
        values[max_ind] = values[i]
        values[i] = max_val
    return (names, values)

class detect:
    #===========DEF=========я 
    def role(guild, raw_search):
        IDs = all_ints(raw_search)
        if IDs == []:
            r = discord.utils.get(guild.roles, name = raw_search)
        else:
            ID = IDs[0]
            r = discord.utils.get(guild.roles, id = ID)
        if r == None:
            return "Error"
        else:
            return r
    
    def channel(guild, raw_search):
        IDs = all_ints(raw_search)
        if IDs == []:
            c = discord.utils.get(guild.channels, name = raw_search)
        else:
            ID = IDs[0]
            c = discord.utils.get(guild.channels, id = ID)
        if c == None:
            return "Error"
        else:
            return c
    
    def member(guild, raw_search):
        IDs = all_ints(raw_search)
        if IDs == []:
            m = None
        else:
            ID = IDs[0]
            m = discord.utils.get(guild.members, id = ID)
        if m == None:
            return "Error"
        else:
            return m
    
    def emoji(guild, raw_search):
        out="Error"
        for emoji in guild.emojis:
            if raw_search==f"<:{emoji.name}:{emoji.id}>":
                out=emoji
                break
        if out=="Error":
            if is_emoji(raw_search):
                out=raw_search
        return out
    #======ASYNC DEF=======
    async def message(channel_id, message_id):
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

#============Bot async funcs==========
async def post_log(guild, log_embed):
    log_channels = await get_data("log-channels", [str(guild.id)])
    if log_channels != "Error":
        for channel_id in log_channels:
            ID=int(channel_id[0])
            channel=discord.utils.get(guild.channels, id=ID)
            if channel != None:
                await channel.send(embed = log_embed)
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
            guild_id=task[2]
            member_id=task[3]
            out.append([mode, guild_id, member_id])
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

async def polite_send(channel, msg, embed = None):
    try:
        if embed == None:
            await channel.send(content = msg)
        else:
            await channel.send(content = msg, embed = embed)
    except Exception:
        pass 

async def refresh_mute(member):
    global mute_role_name
    
    key_words=["None" ,"mute", str(member.guild.id), str(member.id)]
    results = await get_data("tasks", key_words)
    
    if results != "Error":
        Mute = discord.utils.get(member.guild.roles, name=mute_role_name)
        if not Mute in member.guild.roles:
            await setup_mute(member.guild)
            Mute = discord.utils.get(member.guild.roles, name=mute_role_name)
        await member.add_roles(Mute)
    return
    
async def send_welcome(member):
    bot_user = to_member(member.guild, client.user.id)
    
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
            if role!=None and role.position < user_position(bot_user):
                await member.add_roles(role)
    
    return

async def send_leave(member):
    bot_user=discord.utils.get(member.guild.members, id=client.user.id)
    
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
    return
    
async def read_message(channel, user, t_out):
    try:
        msg=await client.wait_for("message", check=lambda message: user.id==message.author.id and channel.id==message.channel.id, timeout=t_out)
    except asyncio.TimeoutError:
        reply=discord.Embed(
            title="🕑 Вы слишком долго не писали",
            description=f"Таймаут: {t_out}",
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
    message = await detect.message(message.channel.id, message.id)
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
        
        message = await detect.message(channel_id, message_id)
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
                
                message = await detect.message(channel_id, message_id)
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
                message = await detect.message(channel_id, message_id)
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
            if user.id != client.user.id:
                users.append(user.id)
        return users

async def update_stats(guild):
    everyone = discord.utils.get(guild.roles, name="@everyone")
    
    amounts={
        "Всего:": len(guild.members),
        "Ботов:": 0,
        "Людей:": 0
        }
    
    for m in guild.members:
        if m.bot:
            amounts["Ботов:"]+=1
    amounts["Людей:"]=amounts["Всего:"]-amounts["Ботов:"]
    
    channels = {
        "Всего:": None,
        "Ботов:": None,
        "Людей:": None
             }
    
    for vc in guild.voice_channels:
        for entity in channels:
            if vc.name.find(entity)!=-1 and channels[entity]==None:
                channels[entity] = vc
        
    for entity in channels:
        if channels[entity]==None:
            channels[entity] = await guild.create_voice_channel(f"{entity} {amounts[entity]}")
            await channels[entity].set_permissions(everyone, connect = False)
        else:
            await channels[entity].edit(name=f"{entity} {amounts[entity]}")
    
    return

async def warn_review(guild, member):
    files = await get_raw_data("warns", [str(guild.id), str(member.id)])
    if files == "Error":
        files = []
    if len(files) > 4:
        ban_case = discord.Embed(
            title = "Список варнов",
            description = f"**Пользователь:** {member} ({member.mention})",
            color = discord.Color.dark_red()
        )
        num = 0
        for file in files:
            num += 1
            
            data = to_list(file.content)
            mod_id = int(data[2])
            
            mod = client.get_user(mod_id)
            reason = data[3]
            
            full_desc = (f"**Модератор:** {mod} ({mod.mention})\n"
                         f"**Причина:** {reason}")
            ban_case.add_field(name = f"**Warn {num}**", value = full_desc, inline = False)
            
            await file.delete()
        
        client.loop.create_task(do_action.tempban(guild, member, client.user, 3600 * 24, "набрал 5 или более варнов"))
        await post_log(guild, ban_case)

async def do_delete(obj):
    try:
        await obj.delete()
    except Exception:
        pass
    return
    
class do_action:
    async def mute(guild, member, moderator, sec, reason = "не указана"):
        global mute_role_name
        
        Mute = discord.utils.get(guild.roles, name=mute_role_name)
        if Mute==None:
            await setup_mute(guild)
            Mute = discord.utils.get(guild.roles, name=mute_role_name)
        if not has_permissions(member, ["manage_messages"]):
            await member.add_roles(Mute)
            await save_task("mute", guild, member, sec)
            
            visual_time = delta_to_words(datetime.timedelta(seconds=sec))
            
            log=discord.Embed(
                title=':lock: Пользователь заблокирован',
                description=(f"**Пользователь:** {member} ({member.mention})\n"
                             f"**Модератор:** {moderator} ({moderator.mention})\n"
                             f"**Причина:** {reason}\n"
                             f"**Длительность:** {visual_time}"),
                color=discord.Color.darker_grey()
            )
            await post_log(guild, log)
            await polite_send(member, "", log)
            
            await asyncio.sleep(sec)
            
            was_muted = (Mute in member.roles)
            
            await withdraw.mute(guild.id, member.id)
            
            if was_muted:
                log=discord.Embed(
                    title='🔑 Пользователь разблокирован',
                    description=(f"**{member.mention}** был разблокирован\n"
                                 f"**Модератор:** {client.user} ({client.user.mention})\n"
                                 f"**Причина:** истёк срок наказания"),
                    color=discord.Color.darker_grey()
                )
                await post_log(guild, log)
                await polite_send(member, "", log)
        return
    async def tempban(guild, user, moderator, sec, reason = "не указана"):
        await save_task("ban", guild, user, sec)
        await guild.ban(user, reason = reason)
        
        watch = delta_to_words(datetime.timedelta(seconds = sec))
        
        log = discord.Embed(
            title = f"⛔ {user} забанен",
            description = (f"**Причина:** {reason}\n"
                           f"**Модератор:** {moderator} ({moderator.mention})\n"
                           f"**Длительность:** {watch}"),
            color = discord.Color.dark_red()
        )
            
        await post_log(guild, log)
        
        await polite_send(user, "", log)
        
        await asyncio.sleep(sec)
        
        banned_ids = [ban_entry.user.id for ban_entry in await guild.bans()]
        was_banned = (user.id in banned_ids)
        
        await withdraw.ban(guild.id, user.id)
        
        if was_banned:
            log=discord.Embed(
                title=f"🟢 {user} был разбанен",
                description=("**Причина:** истёк срок бана\n"
                             f"**Модератор:** {client.user} ({client.user.mention})"),
                color = discord.Color.dark_green()
            )
            await post_log(guild, log)
            
            await polite_send(user, "", log)
        return

class withdraw:
    async def mute(guild_id, user_id):
        global mute_role_name
        
        guild_id = int(guild_id)
        user_id = int(user_id)
        guild = client.get_guild(guild_id)
        user = to_member(guild, user_id)
        bot_user = to_member(guild, client.user.id)
        
        was_muted = False
        
        if guild == None or user == None:
            await delete_data("tasks", ["None", "None", str(guild_id), str(user_id)])
        else:
            await delete_task("mute", guild, user)
            
            Mute = discord.utils.get(guild.roles, name=mute_role_name)
            if Mute == None:
                await setup_mute(guild)
            elif user_position(bot_user) > user_position(user) and Mute in user.roles:
                was_muted = True
                await user.remove_roles(Mute)
                
        return was_muted
            
    async def ban(guild_id, user_id):
        await delete_data("tasks", ["None", "None", str(guild_id), str(user_id)])
        
        guild_id = int(guild_id)
        user_id = int(user_id)
        guild = client.get_guild(guild_id)
        
        unbanned = None
        banned_users = await guild.bans()
        for ban_entry in banned_users:
            banned = ban_entry.user
            if banned.id == user_id:
                unbanned = banned
                break
        
        if unbanned != None:
            await guild.unban(unbanned)
            return True
        else:
            return False
    
#=============Commands=============
@client.command()
async def help(ctx, cmd_name=None):
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
                        f"18) **{p}set_leave [**Раздел**] [**Аргумент / delete**]** - ***{p}help set_leave** для подробностей*\n"
                        f"19) **{p}save** - *сохраняет сервер, чтобы его можно было восстановить*\n"
                        f"20) **{p}backup <**ID сервера**>**\n"
                        f"21) **{p}add_tokens [**Участник**] [**Кол-во**]** - *добавляет токены участнику*\n"
                        f"22) **{p}remove_tokens [**Участник**] [**Кол-во**]**\n"
                        f"23) **{p}set_token [**Эмодзи**]** - *настраивает валюту*\n"
                        f"24) **{p}auto_pay_role [**Со скольки токенов давать / delete**] [**Роль**]** - *настраивает авто-роль за токены*\n"
                        f"25) **{p}auto_remove_role [**Со скольки токенов снимать / delete**] [**Роль**]** - *настраивает авто снятие роли за токены*\n"
                        f"26) **{p}auto_role_info** - *список настроенных ролей*\n")
        user_help_list=(f"1) **{p}search [**Запрос/ID**]**\n"
                        f"2) **{p}warns [**Участник**]** - *варны участника*\n"
                        f"3) **{p}server_warns** - *все участники с варнами*\n"
                        f"4) **{p}embed [**Текст**]** - ***{p}help embed** для подробностей*\n"
                        f"5) **{p}altshift [**Текст**]** - *переключает раскладку для написанного текста*\n"
                        f"6) **{p}avatar <**Пользователь**>** - *рассмотреть свою/чужую аватарку*\n"
                        f"7) **{p}set_giveaway** - *начинает настройку розыгрыша*\n"
                        f"8) **{p}bannahoy [**Пользователь/ID**] <**Модератор**> <**Причина**>**\n"
                        f"9) **{p}bal <**Участник**>** - *проверить баланс*\n"
                        f"10) **{p}top <**Страница**>** - *топ участников*\n")
        
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
             "**Список цветов:** `[red, blue, green, gold, teal, magenta, purple, blurple, dark_blue, dark_red, black, white]`\n"
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
             f"**Как     удалить уже настроенные действия?**\n**{p}set_welcome [**Раздел**] delete**\n"),
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
    if not has_permissions(ctx.author, ["manage_channels"]):
        reply = lack_of_perms_msg(["Управлять каналами"])
        await ctx.send(embed = reply)
    else:
        channel = detect.channel(ctx.guild, raw_channel)
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
    if not has_permissions(ctx.author, ["manage_channels"]):
        reply = lack_of_perms_msg(["Управлять каналами"])
        await ctx.send(embed = reply)
    else:
        channel = detect.channel(ctx.guild, raw_channel)
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
    global mute_role_name
    bot_user = to_member(ctx.guild, client.user.id)
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    if not has_permissions(ctx.author, ["manage_messages"]):
        reply = lack_of_perms_msg(["Управлять сообщениями"])
        await ctx.send(embed = reply)
        
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
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
                        if user_position(member) >= user_position(bot_user):
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
                                log=discord.Embed(
                                    title=':lock: Пользователь заблокирован',
                                    description=(f"**{member.mention}** был заблокирован на **{raw_time}** {stamp}\n"
                                                 f"Мут наложен пользователем {ctx.author.mention}\n"
                                                 f"**Причина:** {reason}"),
                                    color=discord.Color.darker_grey()
                                )
                                
                                temp_msg = await ctx.send(embed = log)
                                await temp_msg.edit(delete_after = 3)
                                await ctx.message.delete()
                                
                                client.loop.create_task(do_action.mute(ctx.guild, member, ctx.author, time, reason))

@client.command()
async def unmute(ctx, raw_user):
    global mute_role_name
    bot_user = to_member(ctx.guild, client.user.id)
    Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
    
    if not has_permissions(ctx.author, ["manage_messages"]):
        reply = lack_of_perms_msg(["Управлять сообщениями"])
        await ctx.send(embed = reply)
    
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        
        else:
            if Mute == None:
                await setup_mute(ctx.guild)
                Mute = discord.utils.get(ctx.author.guild.roles, name=mute_role_name)
            
            if not Mute in member.roles:
                log=discord.Embed(
                    title='Пользователь не заблокирован',
                    description=f'**{member.mention}** не заблокирован **;black**',
                    color=discord.Color.darker_grey()
                )
                await ctx.send(embed=log)
            else:
                if user_position(member) >= user_position(bot_user):
                    reply=discord.Embed(
                        title="⚠Ошибка",
                        description=(f"Моя роль не выше роли пользователя {member}\n"
                                   "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=reply)
                else:
                    case = await delete_task("mute", ctx.guild, member)
                    
                    await withdraw.mute(ctx.guild.id, member.id)
                    
                    log=discord.Embed(
                        title=':key: Пользователь разблокирован',
                        description=(f"**Пользователь:** {member} ({member.mention})\n"
                                     f"**Модератор:** {ctx.author} ({ctx.author.mention})"),
                        color=discord.Color.darker_grey()
                    )
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    await polite_send(member, "", log)
                    
                    await temp_log.edit(delete_after=3)
                    await ctx.message.delete()
                
@client.command(aliases=["blacklist"])
async def black(ctx):
    global mute_role_name
    bl_role = mute_role_name
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
    bot_user=discord.utils.get(ctx.guild.members, id=client.user.id)
    
    if not has_permissions(ctx.author, ["kick_members"]):
        reply = lack_of_perms_msg(["Кикать участников"])
        await ctx.send(embed=reply)
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        
        else:
            if user_position(ctx.author) <= user_position(member):
                reply=discord.Embed(
                    title="❌Недостаточно прав",
                    description=f"Вы не можете кикнуть **{member.name}**, его роль не ниже Вашей",
                    color=discord.Color.red()
                )
                await ctx.send(embed=reply)
            else:
                if user_position(member) >= user_position(bot_user):
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
                    await ctx.message.delete()
                
@client.command()
async def ban(ctx, raw_user, *, reason="не указана"):
    bot_user = to_member(ctx.guild, client.user.id)
    
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
        await ctx.send(embed=reply)
    else:
        member = get_user(raw_user)
        if member==None:
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая пользователя, но он не был найден",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
            
        else:
            member_pos = -1
            if member in ctx.guild.members:
                member=discord.utils.get(ctx.guild.members, id=member.id)
                member_pos = user_position(member)
            if user_position(ctx.author) <= member_pos:
                reply=discord.Embed(
                    title="❌Недостаточно прав",
                    description=f"Вы не можете забанить **{member}**, его роль не ниже Вашей",
                    color=discord.Color.red()
                )
                await ctx.send(embed=reply)
            else:
                if member_pos >= user_position(bot_user):
                    reply=discord.Embed(
                        title="⚠Ошибка",
                        description=(f"Моя роль не выше роли пользователя {member}\n"
                                     "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                        color=discord.Color.gold()
                    )
                    await ctx.send(embed=reply)
                else:
                    await ctx.guild.ban(member, reason=reason)
                    log=discord.Embed(
                        title=f"{member} был забанен",
                        description=(f"**Причина:** {reason}\n"
                                     f"**Модератор:** {ctx.author} ({ctx.author.mention})"),
                        color=discord.Color.dark_red()
                    )
                    temp_log=await ctx.send(embed=log)
                    await post_log(ctx.guild, log)
                    await polite_send(member, "", log)
                    
                    await temp_log.edit(delete_after=3)
                    await ctx.message.delete()

@client.command()
async def unban(ctx, *, member=None):
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
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
            #to_unban = get_user(member)
            unbanned=None
            banned_users=await ctx.guild.bans()
            for ban_entry in banned_users:
                user=ban_entry.user
                if f"{user.id}" == member or f"<@!{user.id}>"==member or f"{user}"==member:
                    unbanned=user
                    break
            if unbanned==None:
                reply = discord.Embed(
                    title = f"{member} нет в списке банов",
                    description = "Возможно Вы ввели ошибочный или неполный тег / ID"
                )
                await ctx.send(embed = reply)
            else:
                case=await delete_task("ban", ctx.guild, unbanned)
                
                await withdraw.ban(ctx.guild.id, unbanned.id)
                
                log=discord.Embed(
                    title=f"{unbanned} был разбанен",
                    description=(f"**Модератор:** {ctx.author} ({ctx.author.mention})"),
                    color=discord.Color.dark_green()
                )
                temp_log=await ctx.send(embed=log)
                await post_log(ctx.guild, log)
                await polite_send(unbanned, "", log)
                
                await temp_log.edit(delete_after=3)
                await ctx.message.delete()

@client.command()
async def tempban(ctx, raw_user, raw_time, *, reason = "не указана"):
    bot_user = to_member(ctx.guild, client.user.id)
    
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
        await ctx.send(embed = reply)
    else:
        member = get_user(raw_user)
        if member==None:
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая пользователя, но он не был найден",
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
                        member_pos = -1
                        if member in ctx.guild.members:
                            member = to_member(ctx.guild, member.id)
                            member_pos = user_position(member)
                        
                        if member_pos >= user_position(ctx.author):
                            reply=discord.Embed(
                                title="⚠Ошибка",
                                description=(f"Ваша роль не выше роли пользователя {member}\n"),
                                color=discord.Color.gold()                            
                            )
                            await ctx.send(embed=reply)
                        else:
                            if member_pos >= user_position(bot_user):
                                reply=discord.Embed(
                                    title="⚠Ошибка",
                                    description=(f"Моя роль не выше роли пользователя {member}\n"
                                                 "Чтобы исправить это, перетащите какую-либо из моих ролей выше"),
                                    color=discord.Color.gold()
                                )
                                await ctx.send(embed=reply)
                            else:
                                log = discord.Embed(
                                    title = f"⛔ {member} забанен",
                                    description = (f"**Причина:** {reason}\n"
                                                   f"**Модератор:** {ctx.author} ({ctx.author.mention})\n"
                                                   f"**Длительность:** {delta_to_words(datetime.timedelta(seconds = time))}"),
                                    color= discord.Color.dark_red()
                                )
                                
                                client.loop.create_task(do_action.tempban(ctx.guild, member, ctx.author, time, reason))
                                
                                temp_msg = await ctx.send(embed = log)
                                await temp_msg.edit(delete_after = 3)
                                await ctx.message.delete()
    
@client.command()
async def set_mute_role(ctx):
    if not has_permissions(ctx.author, ["manage_channels"]):
        reply = lack_of_perms_msg(["Управлять каналами"])
        await ctx.send(embed = reply)
    else:
        await ctx.send("🕑 пожалуйста, подождите...")
        await setup_mute(ctx.guild)
        log=discord.Embed(
            title="✅Настройка завершена",
            description="Роль мута настроена во всех каналах без явных ошибок",
            color=discord.Color.green()
        )
        await ctx.send(embed=log)
    
@client.command()
async def search(ctx, *, raw_request):
    raw_request = raw_request.lower()
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
            user_simil = word_compare(raw_request, str(m).lower())
            
            member_simil_1 = word_compare(raw_request, str(m.name).lower())
            member_simil_2 = word_compare(raw_request, str(m.nick).lower())
            member_simil = max(member_simil_1, member_simil_2)
            
            if user_simil>=0.8 or member_simil>=0.5:
                out.append(m.id)
            if len(out)>24:
                break
        desc=""
        for i in range(len(out)):
            res=discord.utils.get(ctx.guild.members, id=out[i])
            res_data=f"{res} (<@!{res.id}>); **ID:** {res.id}\n"
            desc+=res_data
        if desc=="":
            desc="Нет результатов"
        results=discord.Embed(
            title="Результаты поиска:",
            description=desc,
            color=discord.Color.teal()
        )
        await ctx.send(embed=results)
    
@commands.cooldown(1, 5, commands.BucketType.member)
@client.command()
async def warn(ctx, raw_user, *, reason="не указана"):
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
        await ctx.send(embed=reply)
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        else:
            if user_position(ctx.author) <= user_position(member):
                reply = discord.Embed(
                    title = "❌ Вы не уполномочены",
                    description = f"Ваша роль не выше роли **{member}**"
                )
                await ctx.send(embed = reply)
            else:
                bot_user = to_member(ctx.guild, client.user.id)
                
                if user_position(bot_user) <= user_position(member):
                    reply = discord.Embed(
                        title = "⚠ Моя роль ниже",
                        description = f"Перетащите мою роль выше ролей **{member}**"
                    )
                    await ctx.send(embed = reply)
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
                    await polite_send(member, "", log)
                    
                    await temp_log.edit(delete_after=3)
                    await ctx.message.delete()                    
                    
                    await warn_review(ctx.guild, member)
            
@client.command()
async def warns(ctx, raw_user):
    member = detect.member(ctx.guild, raw_user)
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
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
        await ctx.send(embed=reply)
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        else:
            if user_position(ctx.author) <= user_position(member):
                reply = discord.Embed(
                    title = "❌ Вы не уполномочены",
                    description = f"Ваша роль не выше роли **{member}**"
                )
                await ctx.send(embed = reply)
            else:
                bot_user = to_member(ctx.guild, client.user.id)
                
                if user_position(bot_user) <= user_position(member):
                    reply = discord.Embed(
                        title = "⚠ Моя роль ниже",
                        description = f"Перетащите мою роль выше ролей **{member}**"
                    )
                    await ctx.send(embed = reply)
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
                    await ctx.message.delete()
    
@client.command()
async def clean_warn(ctx, raw_user, num):
    if not has_permissions(ctx.author, ["ban_members"]):
        reply = lack_of_perms_msg(["Банить участников"])
        await ctx.send(embed=reply)
    else:
        member = detect.member(ctx.guild, raw_user)
        if member=="Error":
            reply=discord.Embed(
                title="❌Пользователь не найден",
                description=f"Вы ввели **{raw_user}** подразумевая участника сервера, но он не был найден",
                color=discord.Color.red()
                )
            await ctx.send(embed=reply)
        else:
            if user_position(ctx.author) <= user_position(member):
                reply = discord.Embed(
                    title = "❌ Вы не уполномочены",
                    description = f"Ваша роль не выше роли **{member}**"
                )
                await ctx.send(embed = reply)
            else:
                bot_user = to_member(ctx.guild, client.user.id)
                
                if user_position(bot_user) <= user_position(member):
                    reply = discord.Embed(
                        title = "⚠ Моя роль ниже",
                        description = f"Перетащите мою роль выше ролей **{member}**"
                                )
                    await ctx.send(embed = reply)
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
                            await ctx.message.delete()
    
@client.command(aliases=['clear','del'])
async def clean(ctx, n="1"):
    if has_permissions(ctx.author, ["manage_messages"]):
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
        NotAllowed = lack_of_perms_msg(["Управлять сообщениями"])
        await ctx.send(embed=NotAllowed)

@client.command()
async def embed(ctx, *, raw_text):
    args=c_split(raw_text, " ")
    mode="None"
    ID_str="None"
    if len(args)>0:
        mode=args[0]
    if len(args)>1:
        ID_str=args[1]
    
    head=detect_isolation(raw_text, "==")
    desc=detect_isolation(raw_text, "=")
    col=detect_isolation(raw_text, "##")
    thumb=detect_isolation(raw_text, "+")
    img=detect_isolation(raw_text, "++")
    fields=detect_isolation(raw_text, "&&")
    if col!=[]:
        col=col[0].lower()
    else:
        col="None"
    
    col_names=["red", "blue", "green", "gold", "teal", "magenta", "purple", "blurple", "dark_blue", "dark_red", "black", "white"]
    colors=[discord.Color.red(),
            discord.Color.blue(),
            discord.Color.green(),
            discord.Color.gold(),
            discord.Color.teal(),
            discord.Color.magenta(),
            discord.Color.purple(),
            discord.Color.blurple(),
            discord.Color.dark_blue(),
            discord.Color.dark_red(),
            discord.Color.from_rgb(0, 0, 0),
            discord.Color.from_rgb(254, 254, 254)
            ]
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
    if fields!=[]:
        for field in fields:
            f_name=detect_isolation(field, "$$")
            f_value=detect_isolation(field, ",,")
            msg.add_field(name=list_sum(f_name), value=list_sum(f_value))
    
    wrong_syntax=False
    if mode.lower()!="edit":
        await ctx.send(embed=msg)
    else:
        if not has_permissions(ctx.author, ["manage_messages"]):
            wrong_syntax=True
            reply=discord.Embed(title="Ошибка", description="Недостаточно прав")
            await ctx.send(embed=reply)
        else:
            if not number(ID_str):
                wrong_syntax=True
                reply=discord.Embed(title="Ошибка", description="Укажите **ID** сообщения в данном канале")
                await ctx.send(embed=reply)
            else:
                ID=int(ID_str)
                message = await detect.message(ctx.channel.id, ID)
                if message=="Error":
                    wrong_syntax=True
                    reply=discord.Embed(title="Ошибка", description=f"Сообщение с **ID** {ID} не найдено в этом канале")
                    await ctx.send(embed=reply)
                else:
                    if message.author.id != client.user.id:
                        wrong_syntax=True
                        reply=discord.Embed(title="Ошибка", description=f"Я не могу редактировать это сообщение, так не я его автор")
                        await ctx.send(embed=reply)
                    else:
                        await message.edit(embed=msg)
                
    if not wrong_syntax:
        backup_txt=f"Сырой текст команды, на всякий случай\n`{ctx.message.content}`"
        await polite_send(ctx.author, backup_txt)
        await ctx.message.delete()

@client.command()
async def set_welcome(ctx, categ, *, text="None"):
    bot_user = to_member(ctx.guild, client.user.id)
    
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
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
                channel = detect.channel(ctx.guild, text)
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
                            role = detect.role(ctx.guild, raw_role)
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
                    role = detect.role(ctx.guild, raw_role)
                    if not role in new_roles and role!="Error":
                        new_roles.append(role)
                        new_roles_id.append(str(role.id))
                        if role.position >= user_position(bot_user):
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
    bot_user = to_member(ctx.guild, client.user.id)
    
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
                if role.position >= user_position(bot_user):
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
    
    bot_user=discord.utils.get(ctx.guild.members, id=client.user.id)
    
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
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
                channel = detect.channel(ctx.guild, text)
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
    
    
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
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
                channel = detect.channel(ctx.guild, raw_search)
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
                    emoji = detect.emoji(ctx.guild, raw_emoji)
                    role = detect.role(ctx.guild, raw_role)
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
                        if role.position >= user_position(ctx.author):
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
        user = detect.member(ctx.guild, raw_user)
    reply=discord.Embed(
        title=f"Аватарка {user}",
        color=discord.Color.greyple()
    )
    reply.set_image(url=str(user.avatar_url))
    await ctx.send(embed=reply)
    
@client.command(aliases=["sg", "gcreate", "create"])
async def set_giveaway(ctx):
    
    
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
                channel = detect.channel(ctx.guild, raw_channel)
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

@client.command()
async def save(ctx):
    
    if ctx.author.id != ctx.guild.owner_id and ctx.author.id != 301295716066787332:
        reply = discord.Embed(
            title = "Только для создателя сервера",
            description = "Никто другой не имеет права сохранять сервер",
        )
        await ctx.send(embed = reply)
    else:
        reply = discord.Embed(
            title = "💾 Сохранение сервера",
            description = "В процессе...",
        )
        msg = await ctx.send(embed = reply)
        
        utc = []
        uvc = []
        for tc in ctx.guild.text_channels:
            if tc.category == None:
                utc.append(tc_to_dict(tc))
        for vc in ctx.guild.voice_channels:
            if vc.category == None:
                uvc.append(vc_to_dict(vc))
        
        roles = ctx.guild.roles
        roles.reverse()
        data = {
            "roles": [role_to_dict(role) for role in roles],
            "unsorted_tc": utc,
            "unsorted_vc": uvc,
            "categories": [category_to_dict(c) for c in ctx.guild.categories]
        }
        
        file_name = f"{ctx.guild.id}.json"
        
        with open(file_name, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps(data, ensure_ascii=False))
        
        #bruh = str(data).encode("utf-8")
        #open(file_name, 'wb').write(bruh)
        
        channel = await access_folder("server-backups")
        
        async for m in channel.history(limit = None):
            if m.content == f"{ctx.guild.id}":
                await m.delete()
                break
        
        await channel.send(content = f"{ctx.guild.id}", file = discord.File(file_name))
        os.remove(file_name)
        data = {}
        
        reply = discord.Embed(
            title = "💾 Сервер сохранён",
            description = ("Вы можете загрузить его сюда, или на любой другой свой сервер\n"
                           f"**{prefix}backup <**ID сервера**>**"),
        )
        await msg.edit(embed = reply)

@client.command(aliases = ["load"])
async def backup(ctx, str_ID = None):
    if ctx.author.id != ctx.guild.owner_id and ctx.author.id != 301295716066787332:
        reply = discord.Embed(
            title = "Только для создателя сервера",
            description = "Никто другой не имеет права загружать сохранения сервера",
        )
        await ctx.send(embed = reply)
    else:
        channel = await access_folder("server-backups")
        
        msg = None
        if str_ID == None:
            ID = ctx.guild.id
        else:
            ID = int(str_ID)
        
        async for m in channel.history(limit = None):
            if m.content == f"{ID}":
                msg = m
                break
        
        if msg == None:
            reply = discord.Embed(
                title = "❌ Сервер не сохранён",
                description = "Похоже, вы не сохраняли сервер",
                color = discord.Color.red()
            )
            await ctx.send(embed = reply)
        else:
            ats = msg.attachments
            url = ats[0].url
            
            download = requests.get(url)
            buffer_name = f'{ctx.guild.id}.json'
            
            open(buffer_name, 'wb').write(download.content)
            
            with open(buffer_name, "r", encoding="utf-8") as file:
                data = json.load(file)
            #========/\ Loaded to dictionary /\=======
            
            prog_menu = [
                "⬛ Роли",
                "⬛ Несортированные каналы",
                "⬛ Категории и каналы"
            ]
            bar = discord.Embed(
                title = "Загрузка сервера",
                description = f"Это займёт немного времени\n\n{list_sum(prog_menu)}",
                color = discord.Color.from_rgb(255, 196, 139)
            )
            bar.set_thumbnail(url = "https://cdn.discordapp.com/attachments/664230839399481364/670609557801926666/progressbar_cat.gif")
            msg = await ctx.send(embed = bar)
            
            #========Restoration=============
            Errors = 0
            #=====Stage 1=====
            for rd in data["roles"]:
                name = rd["name"]
                role = discord.utils.get(ctx.guild.roles, name = name)
                if not role in ctx.guild.roles:
                    try:
                        await ctx.guild.create_role(
                            name = name,
                            color = discord.Color(value = rd["color"]),
                            hoist = rd["hoist"],
                            mentionable = rd["mentionable"],
                            permissions = discord.Permissions(permissions = rd["permissions"])
                        )
                    except BaseException:
                        Errors += 1
                        pass
            
            prog_menu[0] = "✅" + prog_menu[0][1:len(prog_menu[0])]
            
            bar = discord.Embed(
                title = "Загрузка сервера",
                description = f"Это займёт немного времени\n\n{list_sum(prog_menu)}",
                color = discord.Color.from_rgb(255, 196, 139)
            )
            bar.set_thumbnail(url = "https://cdn.discordapp.com/attachments/664230839399481364/670609557801926666/progressbar_cat.gif")
            await msg.edit(embed = bar)
            
            #=====Stage 2=====
            client.loop.create_task(restore_text_channels(data["unsorted_tc"], ctx.guild))
            client.loop.create_task(restore_voice_channels(data["unsorted_vc"], ctx.guild))
            
            prog_menu[1] = "✅" + prog_menu[1][1:len(prog_menu[1])]
            
            bar = discord.Embed(
                title = "Загрузка сервера",
                description = f"Это займёт немного времени\n\n{list_sum(prog_menu)}",
                color = discord.Color.from_rgb(255, 196, 139)
            )
            bar.set_thumbnail(url = "https://cdn.discordapp.com/attachments/664230839399481364/670609557801926666/progressbar_cat.gif")
            await msg.edit(embed = bar)
            
            #=====Stage 3=====
            last = len(data["categories"])
            num = 0
            for cd in data["categories"]:
                num += 1
                name = cd["name"]
                category = discord.utils.get(ctx.guild.categories, name = name)
                if not category in ctx.guild.categories:
                    try:
                        category = await ctx.guild.create_category(
                            name = name,
                            overwrites = list_to_overwrites(cd["overwrites"], ctx.guild)
                        )
                        client.loop.create_task(restore_text_channels(cd["text_channels"], ctx.guild, category))
                        if num >= last:
                            await restore_voice_channels(cd["voice_channels"], ctx.guild, category)
                        else:
                            client.loop.create_task(restore_voice_channels(cd["voice_channels"], ctx.guild, category))
                    except BaseException:
                        Errors += 1
                        pass
            
            prog_menu[2] = "✅" + prog_menu[2][1:len(prog_menu[2])]
            
            bar = discord.Embed(
                title = "Загрузка сервера",
                description = f"Сервер загружен\n\n{list_sum(prog_menu)}",
                color = discord.Color.from_rgb(255, 196, 139)
            )
            if Errors > 0:
                bar.add_field(name = "Некоторые данные могли быть не восстановлены в силу нехватки прав", value = "⚠")
            await msg.edit(embed = bar)

@client.command()
async def bannahoy(ctx, raw_user=None, raw_mod=None, *, reason="не указана"):
    if raw_user==None:
        reply=discord.Embed(
            title="❌ Кого банитьнахой?",
            description="Пожалуйста, попробуйте снова, указав того, кого банитенахой",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
    elif raw_mod==None:
        raw_mod=str(ctx.author.id)
    else:
        user = detect.member(ctx.guild, raw_user)
        if user=="Error":
            reply=discord.Embed(
                title="❌ Ошибка",
                description=f"Вы написали {raw_user}, подразумевая пользователя, но он не был найден",
                color=discord.Color.red()
            )
            await ctx.send(embed=reply)
        else:
            moder = detect.member(ctx.guild, raw_mod)
            if moder=="Error":
                reply=discord.Embed(
                    title="❌Ошибка",
                    description=f"Вы написали {raw_mod}, подразумевая пользователя, но он не был найден",
                    color=discord.Color.red()
                )
                await ctx.send(embed=reply)
            else:
                log=discord.Embed(
                    title=f"❗ Пользователь {user} был забанен",
                    description=(f"**Пользователь:** {user.mention}, **ID:** `{user.id}`\n"
                                 f"**Причина:** {reason}\n"
                                 f"**Модератор:** {moder.mention}"),
                    color=discord.Color.dark_red()
                )
                await ctx.send(embed=log)
    

    
@client.command()
async def msg(ctx, *, text="None"): #new
    await ctx.send(text)
    await ctx.message.delete()

@client.command()
async def antispam(ctx, mode = "o"):
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
        await ctx.send(embed = reply)
    else:
        names = ["выключен", "включен"]
        modes = ["off", "on"]
        mode = mode.lower()
        if not mode in modes:
            reply = discord.Embed(
                title = "⚠ Неверный аргумент",
                description = ("Пожалуйста, введите **on** или **off**\n"
                               "Например **'antispam on**")
            )
            await ctx.send(embed = reply)
        else:
            changed = False
            
            mode = modes.index(mode)
            
            prev_set = await get_raw_data("on-off", [str(ctx.guild.id), "antispam"])
            
            data = [str(ctx.guild.id), "antispam", str(mode)]
            to_edit = to_raw(data)
            
            if prev_set != "Error":
                file = prev_set[0]
                f_data = to_list(file.content)
                prev_mode = int(f_data[2])
                
                if prev_mode == mode:
                    reply = discord.Embed(
                        title = "Ошибка",
                        description = ("Эта опция уже настроена")
                    )
                    await ctx.send(embed = reply)
                else:
                    changed = True
                    await file.edit(content = to_edit)
                    
            else:
                changed = True
                await post_data("on-off", data)
            
            if changed:
                reply = discord.Embed(
                    title = f"💾 Антиспам {names[mode]}")
                await ctx.send(embed = reply)
    
#=============Token commands=========
@client.command(aliases = ["bal"])
async def balance(ctx, u_search = None):
    if u_search == None:
        member = ctx.author
    else:
        member = detect.member(ctx.guild, u_search)
    if member == "Error":
        reply = discord.Embed(
            title = "💢 Пользователь не найден",
            description = f"Вы ввели {u_search}, подразумевая участника сервера, но он не был найден"
        )
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        token_emoji = await get_token(ctx.guild)
        
        results = await get_data("balances", [str(ctx.guild.id), str(member.id)])
        if results == "Error":
            tokens = 0
        else:
            data = results[0]
            tokens = int(data[0])
            
        bal_embed = discord.Embed(
            title = f"Баланс {member}",
            description = f"{tokens} {token_emoji}",
            color = discord.Color.teal()
        )
        bal_embed.set_thumbnail(url = member.avatar_url)
        
        await ctx.send(embed = bal_embed)
        
@client.command()
async def set_token(ctx, raw_emoji):
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        emoji = detect.emoji(ctx.guild, raw_emoji)
        if emoji == "Error":
            reply = discord.Embed(
                title = "❌ Ошибка",
                description = f"{raw_emoji} не является эмодзи сервера или юникод-эмодзи"
            )
            await ctx.send(embed = reply)
        else:
            files = await get_raw_data("token-emojis", [str(ctx.guild.id)])
            data = [ctx.guild.id, emoji]
            if files == "Error":
                await post_data("token-emojis", data)
            else:
                file = files[0]
                await file.edit(content = to_raw(data))
            reply = discord.Embed(
                title = "✅ Настроено",
                description = f"Значок токена успешно настроен как {emoji}",
                color = discord.Color.green()
            )
            await ctx.send(embed = reply)

@client.command(aliases = ["add_money", "addmoney", "addtokens", "addm", "addt"])
async def add_tokens(ctx, u_search, amount):
    seller_id = 635432513753579541
    seller = discord.utils.get(ctx.guild.roles, id = seller_id)
    
    if not has_roles(ctx.author, [seller]):
        reply = lack_of_perms_msg([f"Иметь роль <@&{seller_id}> или быть администратором"])
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        if u_search == None:
            member = ctx.author
        else:
            member = detect.member(ctx.guild, u_search)
        if member == "Error":
            reply = discord.Embed(
                title = "💢 Пользователь не найден",
                description = f"Вы ввели {u_search}, подразумевая участника сервера, но он не был найден"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            if not number(amount):
                reply = discord.Embed(
                    title = "💢 Ошибка",
                    description = f"{amount} должно быть целым числом"
                )
                reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
                await ctx.send(embed = reply)
            else:
                amount = int(amount)
                files = await get_raw_data("balances", [str(ctx.guild.id), str(member.id)])
                if files == "Error":
                    new_bal = amount
                    await post_data("balances", [ctx.guild.id, member.id, amount])
                else:
                    file = files[0]
                    data = to_list(file.content)
                    new_bal = int(data[2]) + amount
                    
                    data = [ctx.guild.id, member.id, new_bal]
                    raw_data = to_raw(data)
                    await file.edit(content = raw_data)
                    
                reply = discord.Embed(
                    title = "✅ Начислено",
                    description = f"Пользователю {member} добавлено {amount} токенов",
                    color = discord.Color.green()
                )
                await ctx.send(embed = reply)
                
                await role_review(member, new_bal)

@client.command(aliases = ["remove_money", "removemoney", "removetokens", "remm", "remt"])
async def remove_tokens(ctx, u_search, amount):
    seller_id = 635432513753579541
    seller = discord.utils.get(ctx.guild.roles, id = seller_id)
    
    if not has_roles(ctx.author, [seller]):
        reply = lack_of_perms_msg([f"Иметь роль <@&{seller_id}> или быть администратором"])
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        if u_search == None:
            member = ctx.author
        else:
            member = detect.member(ctx.guild, u_search)
        if member == "Error":
            reply = discord.Embed(
                title = "💢 Пользователь не найден",
                description = f"Вы ввели {u_search}, подразумевая участника сервера, но он не был найден"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            if not number(amount):
                reply = discord.Embed(
                    title = "💢 Ошибка",
                    description = f"{amount} должно быть целым числом"
                )
                reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
                await ctx.send(embed = reply)
            else:
                amount = 0-int(amount)
                files = await get_raw_data("balances", [str(ctx.guild.id), str(member.id)])
                if files == "Error":
                    new_bal = amount
                    await post_data("balances", [ctx.guild.id, member.id, amount])
                else:
                    file = files[0]
                    data = to_list(file.content)
                    new_bal = int(data[2]) + amount
                    
                    data = [ctx.guild.id, member.id, new_bal]
                    raw_data = to_raw(data)
                    await file.edit(content = raw_data)
                    
                reply = discord.Embed(
                    title = "✅ Списано",
                    description = f"У пользователя {member} теперь на {-amount} токенов меньше",
                    color = discord.Color.green()
                )
                await ctx.send(embed = reply)
                
                await role_review(member, new_bal)

@client.command(aliases = ["leaderboard", "lb"])
async def top(ctx, page = "1"):
    interval = 10
    
    if not number(page):
        reply = discord.Embed(
            title = "💢 Ошибка",
            description = f"{page} должно быть целым числом"
        )
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        page = int(page)
        balances = await get_data("balances", [str(ctx.guild.id)])
        
        if balances == "Error":
            top_msg = discord.Embed(
                title = "📊 Топ участников",
                description = "Пуст",
                color = discord.Color.magenta()
            )
            await ctx.send(embed = top_msg)
        else:
            token = await get_token(ctx.guild)
            
            IDs = [int(twin[0]) for twin in balances]
            bals = [int(twin[1]) for twin in balances]
            
            pairs = paral_sort(IDs, bals)
            users = pairs[0]
            bals = pairs[1]
            
            page_num = pages(len(users), interval)
            
            if page < 1 or page > page_num:
                reply = discord.Embed(
                    title = "💢 Не найдена страница",
                    description = f"Максимальный номер страницы: {page_num}"
                )
                reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
                await ctx.send(embed = reply)
            else:
                i = (page-1)*interval
                puncts = 0
                desc = ""
                while puncts < interval and i < len(users):
                    puncts += 1
                    user = discord.utils.get(ctx.guild.members, id = users[i])
                    desc += f"**{i+1})** {user} • {bals[i]} {token}\n"
                    i += 1
                    
                top_msg = discord.Embed(
                    title = "📊 Топ участников",
                    description = desc,
                    color = discord.Color.blue()
                )
                
                top_msg.set_footer(text = f"Page {page}/{page_num}")
                await ctx.send(embed = top_msg)

@client.command(aliases = ["apr"])
async def auto_pay_role(ctx, req_tokens, r_search):
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    elif req_tokens.lower() == "delete":
        IDs = all_ints(r_search)
        if IDs == []:
            str_ID = "wrong_id"
        else:
            str_ID = f"{IDs[0]}"
        files = await get_raw_data("auto-pay-roles", [str(ctx.guild.id), "None", str_ID])
        if files == "Error":
            reply = discord.Embed(
                title = "💢 Ошибка",
                description = f"По запросу {r_search} не найдено настроенной роли"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            for file in files:
                client.loop.create_task(do_delete(file))
            reply = discord.Embed(
                title = "✅ Выполнено",
                description = f"Указанные роли больше не будут выдаваться автоматически",
                color = discord.Color.green()
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
            
    elif not number(req_tokens):
        reply = discord.Embed(
            title = "💢 Ошибка",
            description = f"{req_tokens} должно быть целым числом или словом **delete**, если Вы хотите убрать роль с авто-выдачи"
        )
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        role = detect.role(ctx.guild, r_search)
        if role == "Error":
            reply = discord.Embed(
                title = "💢 Ошибка",
                description = f"Вы ввели {r_search}, подразумевая роль, но она не была найдена"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            await post_data("auto-pay-roles", [ctx.guild.id, req_tokens, role.id])
            reply = discord.Embed(
                title = "✅ Настроено",
                description = f"Роль <@&{role.id}> теперь будет даваться тем, у кого {req_tokens}+ токенов",
                color = discord.Color.green()
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
    
@client.command(aliases = ["arr"])
async def auto_remove_role(ctx, req_tokens, r_search):
    if not has_permissions(ctx.author, ["administrator"]):
        reply = lack_of_perms_msg(["Администратор"])
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    elif req_tokens.lower() == "delete":
        IDs = all_ints(r_search)
        if IDs == []:
            str_ID = "wrong_id"
        else:
            str_ID = f"{IDs[0]}"
        files = await get_raw_data("auto-remove-roles", [str(ctx.guild.id), "None", str_ID])
        if files == "Error":
            reply = discord.Embed(
                title = "💢 Ошибка",
                description = f"По запросу {r_search} не найдено настроенной роли"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            for file in files:
                client.loop.create_task(do_delete(file))
            reply = discord.Embed(
                title = "✅ Выполнено",
                description = f"Указанные роли больше не будут сниматься автоматически",
                color = discord.Color.green()
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
            
    elif not number(req_tokens):
        reply = discord.Embed(
            title = "💢 Ошибка",
            description = f"{req_tokens} должно быть целым числом или словом **delete**, если Вы хотите убрать роль с авто-снятия"
        )
        reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = reply)
    else:
        role = detect.role(ctx.guild, r_search)
        if role == "Error":
            reply = discord.Embed(
                title = "💢 Ошибка",
                description = f"Вы ввели {r_search}, подразумевая роль, но она не была найдена"
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
        else:
            await post_data("auto-remove-roles", [ctx.guild.id, req_tokens, role.id])
            reply = discord.Embed(
                title = "✅ Настроено",
                description = f"Роль <@&{role.id}> теперь будет сниматься с тех, у кого {req_tokens}+ токенов",
                color = discord.Color.green()
            )
            reply.set_footer(text = f"{ctx.author}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed = reply)
    
@client.command(aliases = ["ari"])
async def auto_role_info(ctx):
    add_results = await get_data("auto-pay-roles", [str(ctx.guild.id)])
    rem_results = await get_data("auto-remove-roles", [str(ctx.guild.id)])
    
    token_emoji = await get_token(ctx.guild)
    
    add_desc = ""
    for result in add_results:
        req_tok = result[0]
        role_id = result[1]
        add_desc += f"-> <@&{role_id}> • {req_tok}+ {token_emoji}\n"
        
    rem_desc = ""
    for result in rem_results:
        req_tok = result[0]
        role_id = result[1]
        rem_desc += f"<- <@&{role_id}> • {req_tok}+ {token_emoji}\n"
    
    if add_desc == "":
        add_desc = "Не настроено"
    if rem_desc == "":
        rem_desc = "Не настроено"
    
    screen = discord.Embed(
        title = "📑 Настроенные роли",
        description = (f"**Выдаются:**\n{add_desc}\n"
                       f"**Снимаются:**\n{rem_desc}\n"),
        color = discord.Color.blue()
    )
    await ctx.send(embed = screen)
    
#===================Events==================
@client.event
async def on_member_join(member):
    client.loop.create_task(refresh_mute(member))
    client.loop.create_task(send_welcome(member))
    client.loop.create_task(update_stats(member.guild))
    
@client.event
async def on_member_remove(member):
    client.loop.create_task(update_stats(member.guild))
    await send_leave(member)

@client.event
async def on_raw_reaction_add(data):
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
        if emoji in es and data.user_id!=client.user.id:
            member=discord.utils.get(guild.members, id=data.user_id)
            
            ind=es.index(emoji)
            ID=int(rs[ind])
            role=discord.utils.get(guild.roles, id=ID)
            if role!=None:
                await member.add_roles(role)
                await polite_send(member, f"Вам была выдана роль **{role}** на сервере **{guild}**")
            
@client.event
async def on_raw_reaction_remove(data):
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
        if emoji in es and data.user_id != client.user.id:
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

@client.event
async def on_message(message):
    
    await client.process_commands(message)
    
    if not message.author.bot:
        modes = await get_data("on-off", [str(message.guild), "antispam"])
        if modes == "Error":
            mode = 1
        else:
            mode = int(modes[0][0])
        
        if mode == 1:
            res=spamm(message.guild, message.author, message)
        
            if res[0]:
                client.loop.create_task(do_mute(message.guild, message.author, client.user, 3600, "спам"))
                
                async def go_delete(db_msg):
                    msg_id=db_msg["id"]
                    channel_id=db_msg["channel_id"]
                    message = await detect.message(channel_id, msg_id)
                    if message!="Error":
                        await message.delete()
                    return
                
                messages=res[1]
                
                for message in messages:
                    client.loop.create_task(go_delete(message))
            
            spammed=False

#=====================Errors==========================
@mute.error
async def mute_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}mute [**Участник**] [**Время**] [**Причина**]**\n"
                         f"Например: **{prefix}mute @Player#0000 5m**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@unmute.error
async def unmute_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=f"Формат: **{prefix}unmute [**Участник**]**",
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)
        
@kick.error
async def kick_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=(f"Формат: **{prefix}kick [**Участник**] [**Причина**]**\n"
                         f"Например: **{prefix}kick @Player#0000 спам**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
@ban.error
async def ban_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=(f"Формат: **{prefix}ban [**Участник**] [**Причина**]**\n"
                         f"Например: **{prefix}ban @Player#0000 грубое нарушение правил**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)

@set_log_channel.error
async def set_log_channel_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=(f"Формат: **{prefix}set_log_channel [**Канал**]**\n"
                         f"Например: **{prefix}set_log_channel {ctx.channel.mention}**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)
        
@remove_log_channel.error
async def remove_log_channel_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        Miss=discord.Embed(
            title=':hourglass: Недостаточно аргументов :hourglass:',
            description=(f"Формат: **{prefix}remove_log_channel [**Канал**]**\n"
                         f"Например: **{prefix}remove_log_channel {ctx.channel.mention}**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=Miss)

@tempban.error
async def tempban_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}tempban [**Участник**] [**Время**] [**Причина**]**\n"
                         f"Например: **{prefix}tempban @Player#0000 5m нарушение правил**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@clean_warn.error
async def clean_warn_error(ctx, error):
    
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}clean_warn [**Участник**] [**Номер варна**]**\n"
                         f"Например: **{prefix}clean_warn @Player#0000 1**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        
        def TimeExpand(time):
            if time//60!=0:
                return str(time//60)+'m '+str(time%60)+'s'
            else:
                return str(time)+'s'
        
        cool_notify = discord.Embed(
                title='⏳ Попробуйте позже',
                description = f"Не торопитесь с варнами, осталось **{TimeExpand(int(error.retry_after))}**"
            )
        await ctx.send(embed=cool_notify)    
#=
@set_token.error
async def set_token_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}set_token [**Эмодзи**]**\n"
                         f"Например: **{prefix}set_token 💰**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@add_tokens.error
async def add_tokens_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}add_tokens [**Участник**] [**Кол-во**]**\n"
                         f"Например: **{prefix}add_tokens @Player#0000 1**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@remove_tokens.error
async def remove_tokens_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}remove_tokens [**Участник**] [**Кол-во**]**\n"
                         f"Например: **{prefix}remove_tokens @Player#0000 1**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@auto_pay_role.error
async def auto_pay_role_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}auto_pay_role [**Со скольки токенов выдавать / delete**] [**Роль**]**\n"
                         f"Например: **{prefix}auto_pay_role 2 @Роль**\n"
                         f"Удалить: **{prefix}auto_pay_role delete @Роль**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

@auto_remove_role.error
async def auto_remove_role_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        reply=discord.Embed(
            title="❌Недостаточно аргументов",
            description=(f"Формат: **{prefix}auto_remove_role [**Со скольки токенов выдавать \ delete**] [**Роль**]**\n"
                         f"Например: **{prefix}auto_remove_role 2 @Роль**\n"
                         f"Удалить: **{prefix}auto_remove_role delete @Роль**"),
            color=discord.Color.red()
        )
        await ctx.send(embed=reply)

#===========Tasks=========
async def task_refresh():
    await client.wait_until_ready()
    await reset_tasks()
    while True:
        cases = await clean_past_tasks()
        for case in cases:
            guild = client.get_guild(int(case[1]))
            member = client.get_user(int(case[2]))
            
            if case[0]=="mute":
                was_muted = await withdraw.mute(case[1], case[2])
                if was_muted:
                    log=discord.Embed(
                        title=':key: Пользователь разблокирован',
                        description=(f"**Пользователь:** {member} ({member.mention})\n"
                                     f"**Модератор:** {client.user} ({client.user.mention})\n"
                                     "**Причина:** итсёк срок наказания"),
                        color=discord.Color.darker_grey()
                    )
                    await post_log(guild, log)
                
            elif case[0]=="ban":
                unbanned = None
                banned_users = await guild.bans()
                for ban_entry in banned_users:
                    banned = ban_entry.user
                    if banned.id == int(case[2]):
                        unbanned = banned
                        break
                
                was_banned = await withdraw.ban(case[1], case[2])
                
                if was_banned:
                    log=discord.Embed(
                        title=f"{unbanned} был разбанен",
                        description = (f"**Модератор:** {client.user} ({client.user.mention})\n"
                                       "**Причина:** истёк срок временного бана"),
                        color=discord.Color.dark_green()
                    )
                    await post_log(guild, log)
                    await polite_send(member, f"Вы были разбанены на сервере **{guild.name}**")
        
        data = await closest_inactive_task()
        
        if data!="Error":
            delay=data[1]
            case=data[0]
            
            await asyncio.sleep(delay)
            
            guild = client.get_guild(int(case[1]))
            member = client.get_user(int(case[2]))
            
            case = await delete_task(case[0], guild, member)
            
            if case[0]=="mute":
                was_muted = await withdraw.mute(case[1], case[2])
                if was_muted:
                    log=discord.Embed(
                        title=':key: Пользователь разблокирован',
                        description=(f"**Пользователь:** {member} ({member.mention})\n"
                                     f"**Модератор:** {client.user} ({client.user.mention})\n"
                                     "**Причина:** итсёк срок наказания"),
                        color=discord.Color.darker_grey()
                    )
                    await post_log(guild, log)
                
            elif case[0]=="ban":
                was_banned = await withdraw.ban(case[1], case[2])
                if was_banned:
                    log=discord.Embed(
                        title=f"{member} был разбанен",
                        description = (f"**Модератор:** {client.user} ({client.user.mention})\n"
                                       "**Причина:** истёк срок временного бана"),
                        color=discord.Color.dark_green()
                    )
                    await post_log(guild, log)
                    await polite_send(member, f"Вы были разбанены на сервере **{guild.name}**")
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
