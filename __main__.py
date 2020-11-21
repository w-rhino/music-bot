# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 11:20:54 2020

@author: sone daichi
"""
import os
import traceback
import discord
from discord.ext import commands


bot = commands.Bot(command_prefix='$')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    if 'discord.ext.commands.errors.CommandNotFound' in error_msg:
        await ctx.send('存在しないコマンドだよ！$helpで使えるコマンドを確認してね')
        return
    await ctx.send(error_msg)


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')

############
# helpの調整
############

bot.remove_command('help')


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="music-bot", description="音楽再生機能を持ったBotです。コマンドは次の通りです。", color=0xeee657)

    embed.add_field(name="$load　[cogfile]", value="指定のCogファイルをロードします。", inline=False)
    embed.add_field(name="$unload　[cogfile]", value="指定のCogファイルをアンロードします。", inline=False)
    embed.add_field(name="$join|connect|summon", value="ボイスチャンネルに参加します。", inline=False)
    embed.add_field(name="$leave|disconnect|bye|dc", value="ボイスチャンネルから退出します。", inline=False)
    embed.add_field(name="$play|再生|music [playlist]", value="音楽を再生します。\n googledriveの「music-bot」フォルダ下にあるファイルを全てシャッフル再生します。\n引数にプレイリスト(フォルダ名playlist_XXのXXの部分)の名前を与えることで、そのフォルダ内の音楽を再生します。")
    embed.add_field(name="$nowplaying|nc|current", value="現在再生中のファイル名を表示します。", inline=False)
    embed.add_field(name="$shuffle|sh|mix|random", value="再生リストをシャッフルします。", inline=False)
    embed.add_field(name="$queue|q|playlist", value="プレイリストの先頭10件を表示します。", inline=False)
    embed.add_field(name="$repeat", value="現在再生中の曲をリピート再生します。解除はもう一度このコマンドを入力してください。", inline=False)
    embed.add_field(name="$loop|lq|loopqueue", value="再生リストをループ状態にします。解除はもう一度このコマンドを入力してください。", inline=False)
    embed.add_field(name="$skip", value="現在再生中の曲を停止し、次の曲を再生します。", inline=False)
    embed.add_field(name="$pause", value="再生を一時停止します。", inline=False)
    embed.add_field(name="$resume", value="一時停止を解除します。", inline=False)

    await ctx.send(embed=embed)

for filename in os.listdir("./cogs"):
    if(filename.endswith(".py")):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(token)
