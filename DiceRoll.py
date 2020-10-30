# インストールした discord.py を読み込む
from discord.ext import commands
import os
import traceback

#正規表現用ライブラリ
import re
import random

#csv読み込みライブラリ
import csv

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
        if int(result) <= 80:
            return True
    return False

def judge_adjest(src):
    repatter = re.compile(pattern_power)
    result = repatter.fullmatch(src)
    if result is not None:
        return True
    return False
    
    
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
        if judge_nDn(args[0]) == False:
            await ctx.send('引数が正しくありません。入力しなおして下さい。')
            return            
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
        if judge_nDn(args[0]) == False:
            await ctx.send('引数が正しくありません。入力しなおして下さい。') 
            return
    num, times, result, sum_dice = nDn(tmp)
    if result is not None:
            await ctx.send(ctx.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice)) 
            
@bot.command()
async def p(ctx, value):
    if  value is None:
        await ctx.send('威力となる引数が必要です。')
        return
    if judge_Power(value) == False:
        await ctx.send('威力となる引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    num, times, result, sum_dice = nDn('2D6')
    pwr, pwrInv = culcPower(value, sum_dice)
    await ctx.send('出目：' + str(result) + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)

@bot.command()
async def power(ctx, value):
    if judge_Power(value) == False:
        await ctx.send('引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    num, times, result, sum_dice = nDn('2D6')
    pwr, pwrInv = culcPower(value, sum_dice)
    await ctx.send('出目：' + str(result) + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)    
    
@bot.command()
async def sp(ctx, power, dice_value):
    if judge_Power(power) == False:
        await ctx.send('威力となる引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    if dice_value > 12 or dice_value < 2:
        await ctx.send('ダイスの合計値が不正です。２～１２の数字を入力してください。')
        return
    pwr, pwrInv = culcPower(power, dice_value)
    await ctx.send('ダイス合計値：' + dice_value + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)
    
@bot.command()
async def searchpower(ctx, power, dice_value):
    if judge_Power(power) == False:
        await ctx.send('威力となる引数が正しくありません。80以下の数字（５刻み）を入力してください。') 
        return
    if dice_value > 12 or dice_value < 2:
        await ctx.send('ダイスの合計値が不正です。２～１２の数字を入力してください。')
        return
    pwr, pwrInv = culcPower(power, dice_value)
    await ctx.send('ダイス合計値：' + dice_value + '\n威力：' + pwr + '\n運命変転時威力：' + pwrInv)
    
bot.run(token)
