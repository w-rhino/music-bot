# インストールした discord.py を読み込む
from discord.ext import commands
import os
import traceback

#正規表現用ライブラリ
import re
import random

#csv読み込みライブラリ
import csv

with open('./sw25_power.csv', newline='') as csvfile:
    read = csv.reader(csvfile)
    lst = [row for row in read]


# nDnダイスモジュール

#ダイス用正規表現
pattern = '\d{1,3}d\d{1,3}|\d{1,3}D\d{1,3}'
split_pattern = 'd|D'

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
    
####################

bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

@bot.command()
async def r(ctx, *args):
    tmp = None
    if len(args) == 0:
        tmp = '2D6'
    else:
        tmp = args[0]    
    num, times, result, sum_dice = nDn(tmp)
    if result is not None:
            await ctx.send(ctx.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice)) 

@bot.command()
async def roll(ctx, *args):
    tmp = None
    if len(args) == 0:
        tmp = '2D6'
    else:
        tmp = args[0]    
    num, times, result, sum_dice = nDn(tmp)
    if result is not None:
            await ctx.send(ctx.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice)) 
            
@bot.command()
async def p(ctx, value):
    num, times, result, sum_dice = nDn('2D6')
    v = int(int(value)/5)
    pwr = lst[v][sum_dice - 1]
    if pwr == 127: pwr = 'ファンブル！'
    await ctx.send('出目：' + str(result) + '\n威力：' + pwr)

@bot.command()
async def power(ctx, value):
    num, times, result, sum_dice = nDn('2D6')
    v = int(int(value)/5)
    pwr = lst[v][sum_dice - 1]
    if pwr == 127: pwr = 'ファンブル！'
    await ctx.send('出目：' + str(result) + '\n威力：' + pwr)
    
bot.run(token)
