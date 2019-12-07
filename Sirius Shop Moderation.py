import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import os

client=commands.Bot(command_prefix="'")
bot_id=583016361677160459

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
    print("Ready to moderate")

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
    
async def glob_pos(user):
    pos=0
    for r in user.roles:
        if r.position>pos:
            pos=r.position
    return pos

#=============Commands=============
@client.command()
async def mute(ctx, member: discord.Member, raw_time, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    Blacklist="Мут"
    Mute = discord.utils.get(ctx.author.guild.roles, name=Blacklist)
    if not Mute in ctx.guild.roles:
        await ctx.guild.create_role(name=Blacklist, permissions=discord.Permissions.none())
        Mute = discord.utils.get(ctx.author.guild.roles, name=Blacklist)
    
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

@client.command()
async def unmute(ctx, member: discord.Member):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    Blacklist="Мут"
    
    Mute = discord.utils.get(ctx.author.guild.roles, name=Blacklist)
    if not Mute in ctx.guild.roles:
        await ctx.guild.create_role(name=Blacklist, permissions=discord.Permissions.none())
        Mute = discord.utils.get(ctx.author.guild.roles, name=Blacklist)
    
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
        await ctx.send(f"There're no any roles named **{bl_role}**")
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
    
    if not await has_admin(ctx.author, ctx.guild):
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
                await member.send(f"Вы были кикнуты с сервера **{ctx.guild.name}**.\n**Причина:** {reason}")
                
@client.command()
async def ban(ctx, member: discord.Member, *, reason="не указана"):
    global bot_id
    bot_user=discord.utils.get(ctx.guild.members, id=bot_id)
    
    if not await has_admin(ctx.author, ctx.guild):
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
                await member.send(f"Вы были забанены на сервере **{ctx.guild.name}**.\n**Причина:** {reason}")

@client.command()
async def unban(ctx, *, member=None):
    if not await has_admin(ctx.author, ctx.guild):
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
                await unbanned.send(f"Вы были разбанены на сервере **{ctx.guild.name}**")

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
        
@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.MissingRequiredArgument):
        return

client.run(str(os.environ.get("Sirius_token")))
