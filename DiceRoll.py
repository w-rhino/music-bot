# インストールした discord.py を読み込む
import discord
from discord.ext import commands
import os
import traceback
from collections import deque
import itertools

#正規表現用ライブラリ
import re
import random

#csv読み込みライブラリ
import csv

#Googleドライブ認証
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.CommandLineAuth()
#driveにアクセスするためのオブジェクト
drive = GoogleDrive(gauth)

dir_id = drive.ListFile({'q': 'title = "music-bot"'}).GetList()[0]['id']
music_fulllist = drive.ListFile({'q': '"{}" in parents'.format(dir_id)}).GetList()

#ダイス用正規表現
pattern = '\d{1,3}d\d{1,3}|\d{1,3}D\d{1,3}'
split_pattern = 'd|D'

#威力表用正規表現
pattern_power = '\d{1,2}'
pattern_poweradj = '\d{1}'

#音楽用キュー
music_path = ''
current_music = []
music_queue = deque()
voice_client = None
loopflg = False

#TRPG用データ
powerlist = {}
chara_datalist = {}

#威力表読み込み
with open('./sw25_power.csv', newline='', encoding='utf-8-sig') as csvfile:
    read = csv.DictReader(csvfile)
    for row in read:
        tmp = {}
        tmp = row
        powerlist[row.get('power')] = tmp

#bot用トークン
bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']

##########
#TRPG関連
##########

def load_charadata():
    drive = GoogleDrive(gauth)

    dir_id = drive.ListFile({'q': 'title = "sword_world"'}).GetList()[0]['id']
    chara_metadata = drive.ListFile({'q': '"{}" in parents and title = "charadata"'.format(dir_id)}).GetList()
    data_id = chara_metadata[0]['id']
    
    f = drive.CreateFile({'id': data_id})
    data_path = os.path.join('/tmp', 'chara.csv')
    f.GetContentFile(data_path, mimetype='text/csv')
    
    with open(data_path, newline='', encoding='utf-8-sig') as csvfile:
        readdata = csv.DictReader(csvfile)
        for row in readdata:
            tmp = {}
            tmp = row
            tmp['DEX_bonus'] = bonus(int(row.get('DEX')))
            tmp['AGI_bonus'] = bonus(int(row.get('AGI')))
            tmp['STR_bonus'] = bonus(int(row.get('STR')))
            tmp['VIT_bonus'] = bonus(int(row.get('VIT')))
            tmp['INT_bonus'] = bonus(int(row.get('INT')))
            tmp['MND_bonus'] = bonus(int(row.get('MND')))
            chara_datalist[row.get('discord_user_name')] = tmp
            
    os.remove(data_path)
    
    
def bonus(parameter):
    return int(parameter//6)

#####
#ダイスロール関連
#####

#入力した文字がnDnに合致するか
def judge_nDn(src):
    repatter = re.compile(pattern)
    result = repatter.fullmatch(src)
    if result is not None:
        return True
    return False

#nDnの数字を前半と後半に分ける
def split_nDn(src):
    return re.split(split_pattern,src)

#ダイスロール
def roll_nDn(src):
    result = []
    sum_dice = 0
    roll_index = split_nDn(src)
    roll_count = int(roll_index[0])
    nDice = int(roll_index[1])
    
    for i in range(roll_count):
        tmp = random.randint(1,nDice)
        result.append(tmp)
        sum_dice = sum_dice + tmp
    
    is1dice = True if roll_count == 1 else False
    
    return result,sum_dice,is1dice

#入力と出力
def nDn(text):
    if judge_nDn(text):
        result,sum_dice,is1dice = roll_nDn(text)
        spl = split_nDn(text)
        return spl[1],spl[0],result,sum_dice
    else:
        return 0,0,[],0
    
    
###威力表
def culcPower(value, sum_dice):
    pwr = powerlist.get(str(value))
    damage = pwr.get(str(sum_dice))

    return damage

def culcPowerInv(value, sum_dice):
    pwr = powerlist.get(str(value))
    damageInv = pwr.get(str(14 - sum_dice))

    return damageInv

def adjestPower(value, sum_dice):
    if sum_dice != 2 and sum_dice != 12:
        sum_dice = sum_dice + value
        if sum_dice > 12:
            sum_dice = 12
    return sum_dice
    

def judge_Power(src):
    repatter = re.compile(pattern_power)
    result = repatter.fullmatch(src)
    if result is not None:
        if int(result.group()) <= 80:
            return True
    return False

def judge_adjest(src):
    repatter = re.compile(pattern_power)
    result = repatter.fullmatch(src)
    if result is not None:
        return True
    return False

#キューの確認、再帰的に連続再生 
def check_queue(e):
    global music_path, voice_client, current_music
    os.remove(music_path)
    if len(music_queue) != 0 :
        if loopflg:
            music_queue.append(current_music)
        current_music = music_queue.popleft()
        f = drive.CreateFile({'id': current_music[0]})
        music_path = os.path.join('/tmp', f['title'])
        f.GetContentFile(music_path)
        ffmpeg_audio_source = discord.FFmpegPCMAudio(music_path)
        voice_client.play(ffmpeg_audio_source, after = check_queue)
    else:
        print("再生終了！")
        
#ドライブ情報のアップデート
def update_drive():
    global drive, dir_id, music_fulllist
    drive = GoogleDrive(gauth)

    dir_id = drive.ListFile({'q': 'title = "music-bot"'}).GetList()[0]['id']
    music_fulllist = drive.ListFile({'q': '"{}" in parents'.format(dir_id)}).GetList()

####################
##async関数開始

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    if 'discord.ext.commands.errors.CommandNotFound' in error_msg:
        await ctx.send('存在しないコマンドだよ！$helpで使えるコマンドを確認してね')
        return 
    await ctx.send(error_msg)

@bot.command(aliases = ["roll","dice"])
async def r(ctx, *args):
    tmp = None
    if len(args) == 0:
        tmp = '2D6'
    else:
        tmp = args[0]
        if judge_nDn(args[0]) == False:
            await ctx.send('引数が正しくありません。入力しなおして下さい。')
            return            
    num, times, result, sum_dice = nDn(tmp)
    if result is not None:
            await ctx.send(ctx.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice)) 
            
@bot.command(aliases=["power","po"])
async def p(ctx, *value):
    if len(value) == 0:
        await ctx.send('威力となる引数が必要です。')
        return
    if judge_Power(value[0]) == False:
        await ctx.send('威力となる引数が正しくありません。80以下の数字を入力してください。') 
        return
    num, times, result, sum_dice = nDn('2D6')
    pwr, pwrInv = culcPower(value[0], sum_dice)
    await ctx.send('出目：' + str(result) + '\nダメージ：' + pwr + '\n運命変転時ダメージ：' + pwrInv)
    
@bot.command(aliases = ["searchpower", "search"])
async def sp(ctx, *args):
    if len(args) < 2:
        await ctx.send('引数として威力、ダイスの合計値が必要です。')
        return
    if judge_Power(args[0]) == False:
        await ctx.send('威力となる引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    if int(args[1]) > 12 or int(args[1]) < 2:
        await ctx.send('ダイスの合計値が不正です。２～１２の数字を入力してください。')
        return
    pwr, pwrInv = culcPower(args[0], int(args[1]))
    await ctx.send('ダイス合計値：' + args[1] + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)
 
###TRPG

@bot.commnad(aliases = ["st","parameter"])
async def status(ctx):
    data = chara_datalist.get(ctx.author.name)
    
    embed = discord.Embed(title=data.get('character_name'), description="キャラのステータスは次の通りです。", color=0xe657ee)

    embed.add_field(name="最大HP：" + data.get('HP'), inline=False)
    embed.add_field(name="最大MP：" + data.get('MP'), inline=False)
    embed.add_field(name="器用度：" + data.get('DEX') + "，ボーナス：" + data.get('DEX_bonus'), inline=True)
    embed.add_field(name="敏捷度：" + data.get('AGI') + "，ボーナス：" + data.get('AGI_bonus'), inline=True)
    embed.add_field(name="筋力：" + data.get('STR') + "，ボーナス：" + data.get('STR_bonus'), inline=True)
    embed.add_field(name="生命力：" + data.get('VIT') + "，ボーナス：" + data.get('VIT_bonus'), inline=True)
    embed.add_field(name="知力：" + data.get('INT') + "，ボーナス：" + data.get('INT_bonus'), inline=True)
    embed.add_field(name="精神力：" + data.get('MND') + "，ボーナス：" + data.get('MND_bonus'), inline=True)
    embed.add_field(name="生命抵抗力：" + data.get('RES_VITAL'), inline=False)
    embed.add_field(name="精神抵抗力：" + data.get('RES_MENTAL'), inline=False)
    embed.add_field(name="技巧判定：" + data.get('judge_tech'), inline=False)
    embed.add_field(name="運動判定：" + data.get('judge_physical'), inline=False)
    embed.add_field(name="観察判定："+ data.get('judge_obs'), inline=False)
    embed.add_field(name="(魔物)知識判定：" + data.get('judge_wisdom'), inline=False)
    embed.add_field(name="先制力：" + data.get('priority'), inline=False)
    embed.add_field(name="移動力：" + + data.get('moving'), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(aliases = ["atk", "combat"])    
async def attack(ctx):
    data = chara_datalist.get(ctx.author.name)
    
    num, times, result, sum_dice = nDn('2D6')
    damage = int(data.get('total_damage')) + int(culcPower(data.get('weapon_power'), sum_dice))
    #damageInv = int(data.get('total_damage')) + int(culcPowerInv(data.get('weapon_power'), sum_dice))
    
    damagemsg = data.get('character_name') + "の通常攻撃！\n" + "出目：" + str(result) + "\nダメージ：" + str(damage)
    crimsg = "通常クリティカル値は" + data.get('weapon_critical') + "です。\nクリティカルの場合、$p " + data.get('weapon_power') + "を入力してそのダメージを加算してください。"
    
    await ctx.send(damagemsg + "\n" + crimsg)
    
################MusicBot

#参加
@bot.command(aliases = ["connect", "summon"]) 
async def join(ctx):
    voice_state = ctx.author.voice

    if (not voice_state) or (not voice_state.channel):
        #もし送信者がどこのチャンネルにも入っていないなら
        await ctx.send("先にボイスチャンネルに入っている必要があります。")
        return

    channel = voice_state.channel #送信者のチャンネル

    await channel.connect() #VoiceChannel.connect()を使用
    await ctx.send(channel.name + "に参加したよ！")

#退出   
@bot.command(aliases=["disconnect","bye","dc"])
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client

    if not voice_client:
        await ctx.send("Botはこのサーバーのボイスチャンネルに参加していません。")
        return

    #曲の途中なら一時ファイル削除
    if voice_client.is_playing():
        await ctx.send("再生リストと一時ファイルを削除します。")
        music_queue.clear()
        voice_client.stop()
        
    await voice_client.disconnect()
    await ctx.send("ボイスチャンネルから切断しました。")
    
#再生
@bot.command(aliases = ["再生","music"])
async def play(ctx):
    global music_path, voice_client, current_music
    voice_client = ctx.message.guild.voice_client

    if not voice_client:
        await ctx.send("Botはこのサーバーのボイスチャンネルに参加していません。")
        return

    update_drive()
    music_queue.clear()
    
    for musicfile in music_fulllist:
        file_id = musicfile['id']
        file_name = musicfile['title']
        music_queue.append([file_id, file_name])
        
    random.shuffle(music_queue)
    current_music = music_queue.popleft()
    f = drive.CreateFile({'id': current_music[0]})
    music_path = os.path.join('/tmp', f['title'])
  
    f.GetContentFile(music_path)
    ffmpeg_audio_source = discord.FFmpegPCMAudio(music_path)
    voice_client.play(ffmpeg_audio_source, after = check_queue)

    await ctx.send("再生中…")
    
@bot.command(aliases = ["np", "current"])
async def nowplaying(ctx):
    global current_music
    embed=discord.Embed(color=0x30ff30)
    embed.add_field(name="nowplaying", value=current_music[1], inline=False)
    await ctx.send(embed=embed)
    
@bot.command(aliases = ["lq","loopqueue"])
async def loop(ctx):
    global loopflg
    if not loopflg:
        loopflg = True
        await ctx.send("キューをループ状態にしました。解除はもう一度このコマンドを入力してください。")
    else:
        loopflg = False
        await ctx.send("キューのループ状態を解除しました。")
        
        
    
@bot.command(aliases = ["sh", "mix", "random"])
async def shuffle(ctx):
    global music_queue
    random.shuffle(music_queue)
    await ctx.send("再生リストをシャッフルしました。")
    
@bot.command(aliases = ["q", "playlist"])
async def queue(ctx):
    global music_queue
    
    if len(music_queue) > 10:
        sublist = itertools.islice(music_queue, 0, 10) 
    elif len(music_queue) == 0:
        await ctx.send("キューに何も入ってないよ！")
        return
    else:
        sublist = music_queue
    
    embed=discord.Embed(title= '現在の再生リスト(先頭10曲分)',color=0xffa030)
    embed.add_field(name ="Now playing", value = current_music[1])
    for count, value in enumerate(sublist, 1):
        embed.add_field(name= str(count) + ".", value=value[1], inline=False)
    embed.set_footer(text = "現在のキューは" + str(len(music_queue)) + "件です。")
    await ctx.send(embed=embed)
    

@bot.command()
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("現在の曲を停止し、次の曲を再生します。")
    else:
        await ctx.send("現在再生している曲がないよ！")
        
@bot.command()
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await ctx.send("既に一時停止中です。再開はresumeです。")
        return
    else:
        voice_client.pause()
        await ctx.send("再生を一時停止しました。再開はresumeです。")
        
@bot.command()
async def resume(ctx):
    

    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await ctx.send("再生を再開します。")
        voice_client.resume()
        return
    else:
        await ctx.send("再開するための曲がないよ！") 

############
#helpの調整
############
    
bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="DiceRoll", description="ダイスロールと音楽再生機能を持ったBotです。コマンドは次の通りです。", color=0xeee657)

    embed.add_field(name="$r|roll|dice [nDn]", value="サイコロを振ります。引数無しの場合は2D6を、引数(nDnの形で入力)ありの場合はそのダイスの形式で振ります。", inline=False)
    embed.add_field(name="$p|po|power [value]", value="威力表に基づいたダメージを算出します。引数には80以下の数字(5刻み)を入力してください。", inline=False)
    embed.add_field(name="$sp|search|searchpower [value] [sum_dice]", value="[sum_dice]の値が出た時、威力[value]のダメージを表示します。", inline=False)
    embed.add_field(name="$join|connect|summon", value="ボイスチャンネルに参加します。", inline=False)
    embed.add_field(name="$leave|disconnect|bye|dc", value="ボイスチャンネルから退出します。自動退出機能は無いため使い終わったらこのコマンドをお忘れなく。", inline=False)
    embed.add_field(name="$play|再生|music", value="音楽を再生します。\n https://drive.google.com/drive/folders/1oJHlfO8BTlG4439vz-201k64esvoQhlW?usp=sharing \nここのフォルダにあるファイルを全て再生します。\n再生停止は$leaveで。")
    embed.add_field(name="$nowplaying|nc|current", value="現在再生中のファイル名を表示します。", inline=False)
    embed.add_field(name="$shuffle|sh|mix|random", value="再生リストをシャッフルします。", inline=False)
    embed.add_field(name="$queue|q|playlist", value="プレイリストの先頭10件を表示します。", inline=False)
    embed.add_field(name="$loop|lq|loopqueue", value="再生リストをループ状態にします。解除はもう一度このコマンドを入力してください。", inline=False)
    embed.add_field(name="$skip", value="現在再生中の曲を停止し、次の曲を再生します。", inline=False)
    embed.add_field(name="$pause", value="再生を一時停止します。", inline=False)
    embed.add_field(name="$resume", value="一時停止を解除します。", inline=False)

    await ctx.send(embed=embed)

bot.run(token)
