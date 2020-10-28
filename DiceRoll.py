# インストールした discord.py を読み込む
from discord.ext import commands
import os
import traceback

#正規表現用ライブラリ
import re
import random

bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']


#ダイス用正規表現
pattern = '\$\d{1,3}d\d{1,3}|\$\d{1,3}D\d{1,3}'
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
    src2 = re.sub('\$','',src)
    return re.split(split_pattern,src2)

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
        if is1dice:
            return spl[1] +'面ダイスを1回振ります。' + '\n出目：' + str(sum_dice)
        else:
            return spl[1] + '面ダイスを' + spl[0] + '回振ります。' + '\n出目：' + str(result) + '\n合計：' + str(sum_dice)
    else:
        return None

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)
    
# メッセージ受信時に動作する処理
@bot.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # ダイスロール処理
    msg = message.content
    result = nDn(msg) 
    if result is not None:
        await message.channel.send(message.author.name + 'さんのダイスロール\n' + result)

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run(token)
