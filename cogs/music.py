# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 21:32:13 2020

音楽再生関連
参照元：https://qiita.com/Shirataki2/items/f4ea533d5baf55c4b1d3

@author: sone daichi
"""
	
import asyncio
import os
from random import shuffle

import discord
from discord.ext import commands
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class MusicQueue(asyncio.Queue):
    def __init__(self):
        super().__init__(100)

    def __getitem__(self, index):
        return self._queue[index]

    def to_list(self):
        return list(self._queue)

    def shuffle(self):
        shuffle(self._queue)

    def reset(self):
        self._queue.clear()

class MusicStatus:
    def __init__(self, ctx, vc):
        self.vc = vc
        self.ctx = ctx
        self.queue = MusicQueue()
        self.playing = asyncio.Event()
        self.current_id = ""
        self.current_title = ""
        self.music_path = ""
        self.loopf = False
        self.repeatf = False
        self.gauth = GoogleAuth()
        self.gauth.CommandLineAuth()
        self.drive = GoogleDrive(self.gauth)
        asyncio.create_task(self.playing_task())

    async def add_music(self, file_id, file_name):
        await self.queue.put([file_id, file_name])

    def get_list(self):
        return self.queue.to_list()

    def shuffle(self):
        self.queue.shuffle()
        
    def loop(self):
        if self.loopf:
            self.loopf = False
        else:
            self.loopf = True
            self.repeatf = False
            
    def repeat(self):
        if self.repeatf:
            self.repeatf = False
        else:
            self.repeatf = True
            self.loopf = False

    async def playing_task(self):
        while True:
            self.playing.clear()
            if not self.repeatf:
                try:
                    self.current_id, self.current_title = await asyncio.wait_for(self.queue.get(), timeout = 240)
                except asyncio.TimeoutError:
                    asyncio.create_task(self.leave())
            f = self.drive.CreateFile({'id': self.current_id})
            self.music_path = os.path.join('/tmp',f['title'])
            f.GetContentFile(self.music_path)
            src = discord.FFmpegPCMAudio(self.music_path)
            self.vc.play(src, after=self.play_next)
            await self.ctx.playing.wait()

    def play_next(self, err=None):
        os.remove(self.music_path)
        if self.loopf:
            self.add_music(self.current_id, self.current_title)
        self.playing.set()

    async def leave(self):
        self.queue.reset()
        if os.path.exists(self.music_path):
            os.remove(self.music_path)
        if self.vc:
            await self.vc.disconnect()
            self.vc = None

    @property
    def is_playing(self):
        return self.vc.is_playing()

    def stop(self):
        self.vc.stop()

    def is_paused(self):
        return self.vc.is_paused()

    def pause(self):
        self.vc.pause()

    def resume(self):
        self.vc.resume()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_statuses = {}
        self.gauth = GoogleAuth()
        self.gauth.CommandLineAuth()
        self.drive = GoogleDrive(self.gauth)
        self.dir_id = self.drive.ListFile({'q': 'title = "music-bot"'}).GetList()[0]['id']
        self.music_fulllist = self.drive.ListFile({'q': '"{}" in parents and mimeType != "application/vnd.google-apps.folder"'.format(self.dir_id)}).GetList()

    @commands.command(aliases = ["connect","summon"])
    async def join(self, ctx):
        # VoiceChannel未参加
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('先にボイスチャンネルに参加してください')
        vc = await ctx.author.voice.channel.connect()
        await ctx.send(ctx.author.voice.channel.name + "に参加したよ！")
        self.music_statuses[ctx.guild.id] = MusicStatus(ctx, vc)

    @commands.command(aliases = ["dc","disconnect","bye"])
    async def leave(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('ボイスチャンネルにまだ未参加です')
        await status.leave()
        await ctx.send("ボイスチャンネルから切断しました。")
        del self.music_statuses[ctx.guild.id]

    @commands.command(aliases = ["music","再生"])
    async def play(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        #joinしていない場合joinする
        if status is None:
            await ctx.invoke(self.join)
            await ctx.send("ボイスチャンネルに参加します。")
            status = self.music_statuses.get(ctx.guild.id)

        await ctx.send("再生リストを構築中です…")
        for musicfile in self.music_fulllist:
            file_id = musicfile['id']
            file_name = musicfile['title']
            await status.add_music(file_id, file_name)
        await ctx.send("再生中…")

    @commands.command(aliases = ["np", "current"])
    async def nowplaying(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        embed=discord.Embed(color=0x30ff30)
        embed.add_field(name="nowplaying", value=status.current_title, inline=False)
        await ctx.send(embed=embed)
        
    @commands.command(aliases = ["lq","loopqueue"])
    async def loop(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        status.loop()
        if status.loopf:
            await ctx.send("キューをループ状態にしました。解除はこのコマンドをもう一度入力してください。")
        else:
            await ctx.send("キューのループ状態を解除しました。")
            
    @commands.command()
    async def repeat(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        status.repeat()
        if status.repeatf:
            await ctx.send("一曲リピートの状態にしました。解除はこのコマンドをもう一度入力してください。")
        else:
            await ctx.send("リピート状態を解除しました。")   

    @commands.command()
    async def skip(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        await ctx.send("次の曲を再生します。")
        await status.stop()

    @commands.command()
    async def stop(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if not status.is_playing:
            return await ctx.send('既に停止しています')
        await status.stop()
        await ctx.send('停止しました')

    @commands.command()
    async def pause(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if status.is_paused():
            await ctx.send("既に一時停止中です。再開はresumeです。")
        else:
            status.pause()
            await ctx.send("再生を一時停止しました。再開はresumeです。")

    @commands.command()
    async def resume(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if status.is_paused():
            await ctx.send("再生を再開します。")
            status.resume()
        else:
            await ctx.send("再生するための曲がありません。")

    @commands.command(aliases = ["sh","mix","random"])
    async def shuffle(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('先にボイスチャンネルに参加してください')
        status.shuffle()
        await ctx.send("再生リストをシャッフルしました。")


    @commands.command(aliases = ["q","playlist"])
    async def queue(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('先にボイスチャンネルに参加してください')
        queue = status.get_list()
        embed=discord.Embed(title= '現在の再生リスト(先頭10曲分)',color=0xffa030)
        embed.add_field(name ="Now playing", value = status.current_title, inline = False)

        msg = ""
        for i, (file_id, file_title) in enumerate(queue):
            msg = msg + str(i) + ". " + file_title + "\n"
            if i > 10:
                break
        embed.add_field(name = "次曲以降", value = msg, inline = False)
        embed.set_footer(text = "現在のキューは" + str(len(queue)) + "件です。")
        await ctx.send(embed=embed)


def setup(bot):
    return bot.add_cog(Music(bot))