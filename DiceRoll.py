# インストールした discord.py を読み込む
from discord.ext import commands
import os
import traceback

# nDnダイスを呼び出す
import nDnDICE

bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']

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
    if message.content == '\$\d{1,3}d\d{1,3}|\$\d{1,3}D\d{1,3}':
        msg = message.content
        num, times, result, sum_dice = nDn(msg)
        if result is not None:
            await message.channel.send(message.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run(token)
