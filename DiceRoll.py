# インストールした discord.py を読み込む
import discord

# Jupyter用のエラー回避ライブラリ
import asyncio
import nest_asyncio

#正規表現用ライブラリ
import re

import random

# エラー回避ライブラリの適用
nest_asyncio.apply()

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

# 自分のBotのアクセストークンに置き換えてください
TOKEN = 'NzcwOTA3ODczMjYwNjAxMzY0.X5kZ5w.fFRwKmAUm6S-qGOAbC0YdJUz0y4'

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # ダイスロール処理
    msg = message.content
    result = nDn(msg) 
    if result is not None:
        await message.channel.send(message.author.name + 'さんのダイスロール\n' + result)

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
