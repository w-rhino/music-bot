# インストールした discord.py を読み込む
import discord
from discord.ext import commands
import os
import traceback
import asyncio
from collections import deque

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
#driveにアクセスすためのオブジェクト
drive = GoogleDrive(gauth)

dir_id = drive.ListFile({'q': 'title = "music-bot"'}).GetList()[0]['id']
music_fulllist = drive.ListFile({'q': '"{}" in parents'.format(dir_id)}).GetList()

#連続再生用の

#威力表読み込み
with open('./sw25_power.csv', newline='') as csvfile:
    read = csv.reader(csvfile)
    lst = [row for row in read]


# nDnダイスモジュール

#ダイス用正規表現
pattern = '\d{1,3}d\d{1,3}|\d{1,3}D\d{1,3}'
split_pattern = 'd|D'

#威力表用正規表現
pattern_power = '\d{1,2}'
pattern_poweradj = '\d{1}'

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
    v = int(int(value)/5)
    pwr = str(lst[v][sum_dice - 1])
    pwrInv = str(14 - int(lst[v][sum_dice - 1]))
    if pwr == '127': 
        pwr = 'ファンブル！'
    if pwrInv == '127':
        pwrInv = 'ファンブル！'
    return pwr, pwrInv

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
    
    
####################
##async関数開始

bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']

##音声コーデック
# if not discord.opus.is_loaded():
#     discord.opus.load_opus("heroku-buildpack-libopus")

#音楽用キュー
music_path = ''
queue = deque()
voice_client = None

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
        await ctx.send('威力となる引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    num, times, result, sum_dice = nDn('2D6')
    pwr, pwrInv = culcPower(value[0], sum_dice)
    await ctx.send('出目：' + str(result) + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)
    
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

    await voice_client.disconnect()
    await ctx.send("ボイスチャンネルから切断しました。")
    
#再生
@bot.command(aliases = ["再生","music"])
async def play(ctx):
    voice_client = ctx.message.guild.voice_client

    if not voice_client:
        await ctx.send("Botはこのサーバーのボイスチャンネルに参加していません。")
        return

    queue.clear()
    
    for musicfile in music_fulllist:
        file_id = musicfile['id']
        queue.append(file_id)  
        
    
    current_id = queue.popleft()
    f = drive.CreateFile({'id': current_id})
    music_path = os.path.join('/tmp', f['title'])
  
    f.GetContentFile(music_path)
    ffmpeg_audio_source = discord.FFmpegPCMAudio(music_path)
    voice_client.play(ffmpeg_audio_source, after = check_queue)

    await ctx.send("再生中…")
    
def check_queue(e):
    global music_path
    os.remove(music_path)
    try:
        if not queue.empty():
            current_id = queue.popleft()
            f = drive.CreateFile({'id': current_id})
            music_path = os.path.join('/tmp', f['title'])
            f.GetContentFile(music_path)
            ffmpeg_audio_source = discord.FFmpegPCMAudio(music_path)
            voice_client.play(ffmpeg_audio_source, after = check_queue)
    except:
        print(e)

@bot.command()
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("曲を停止しました。")
    else:
        await ctx.send("停止する曲がないよ！")
        
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

bot.run(token)
