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
        super().__init__(200)

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
                    self.current_id, self.current_title = await asyncio.wait_for(self.queue.get(), timeout=180)
                except asyncio.TimeoutError:
                    asyncio.create_task(self.leave())
            f = self.drive.CreateFile({'id': self.current_id})
            self.music_path = os.path.join('/tmp', f['title'])
            f.GetContentFile(self.music_path)
            src = discord.FFmpegPCMAudio(self.music_path)
            self.vc.play(src, after=self.play_next)
            if self.loopf:
                await self.add_music(self.current_id, self.current_title)
            await self.playing.wait()

    def play_next(self, err=None):
        if os.path.exists(self.music_path):
            os.remove(self.music_path)
        self.playing.set()

    async def leave(self):
        self.queue.reset()
        if os.path.exists(self.music_path):
            os.remove(self.music_path)
        if self.vc is not None:
            await self.vc.disconnect()
            self.vc = None

    @property
    def is_playing(self):
        return self.vc.is_playing()

    def stop(self):
        self.vc.stop()

    @property
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
        self.music_fulllist = []

    def get_all_music(self):
        all_list = self.get_filelist_recursively(self.dir_id)
        return all_list

    def get_filelist_recursively(self, parent_id, lst=None):
        if lst is None:
            lst = []

        file_list = self.drive.ListFile({'q' : f'"{parent_id}" in parents and trashed = false'}).GetList()
        lst += [f for f in file_list if f['mimeType'] != 'application/vnd.google-apps.folder']

        for f in file_list:
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                self.get_filelist_recursively(f['id'], lst)

        return lst

    def search_music(self, q):
        results = []
        all_list = self.get_all_music()

        for d in all_list:
            if q in d.get('title'):
                results.append(d)

        return results

    @commands.command(aliases=["connect", "summon"])
    async def join(self, ctx):
        # VoiceChannel未参加
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('先にボイスチャンネルに参加してください')
        vc = await ctx.author.voice.channel.connect()
        if vc is None:
            return await ctx.send("BotがVoiceClientの情報を正しく取得できませんでした。Botを切断し、時間をおいてから再実行してください。")
        await ctx.send(ctx.author.voice.channel.name + "に参加したよ！")
        self.music_statuses[ctx.guild.id] = MusicStatus(ctx, vc)

    @commands.command(aliases=["dc", "disconnect", "bye"])
    async def leave(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('ボイスチャンネルにまだ未参加です')
        await status.leave()
        await ctx.send("ボイスチャンネルから切断しました。")
        del self.music_statuses[ctx.guild.id]

    @commands.command(aliases=["music", "再生"])
    async def play(self, ctx, *args):
        self.drive = GoogleDrive(self.gauth)
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            await ctx.invoke(self.join)
            await ctx.send("ボイスチャンネルに参加します。")
            status = self.music_statuses.get(ctx.guild.id)

        if len(args) == 0:
            self.music_fulllist.clear()
            self.music_fulllist = self.drive.ListFile({'q': f'"{self.dir_id}" in parents and mimeType != "application/vnd.google-apps.folder"'}).GetList()
        else:
            folder_name = "playlist_" + args[0]
            folder_metalist = self.drive.ListFile({'q': f'"{self.dir_id}" in parents and mimeType = "application/vnd.google-apps.folder" and title = "{folder_name}"'}).GetList()
            if folder_metalist == []:
                return await ctx.send("指定したフォルダはありません。「playlist_XX」のXXに当たる部分を引数として入力してください。")
            folder_id = folder_metalist[0].get('id')

            self.music_fulllist.clear()
            self.music_fulllist = self.drive.ListFile({'q': f'"{folder_id}" in parents and mimeType != "application/vnd.google-apps.folder"'}).GetList()

        status.queue.reset()
        await ctx.send("再生リストを構築中です…")
        for musicfile in self.music_fulllist:
            file_id = musicfile['id']
            file_name = musicfile['title']
            await status.add_music(file_id, file_name)

        if status.is_playing:
            status.stop()
        status.shuffle()
        await ctx.send("再生中…")

    async def display_search(self, ctx, embed, num):
        msg = await ctx.send(embed=embed)

        emojis = ["⏮️", "⏹️", "▶️", "⏭️"]
        emojis_num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        emojis_play = emojis_num[:int(num)]
        for emoji in emojis:
            await msg.add_reaction(emoji)
        for emoji in emojis_play:
            await msg.add_reaction(emoji)
        await ctx.send("曲を再生したい場合は対応した番号にリアクションしてください。")

        def check(reaction, user):
            return user == ctx.author and (reaction.emoji in emojis or reaction.emoji in emojis_play) and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("リアクションの受付が終了しました。")
            return "timeout"

        if reaction.emoji == "⏮️":
            return "prev"
        elif reaction.emoji == "⏹️":
            return "stop"
        elif reaction.emoji == "▶️":
            return "play"
        elif reaction.emoji == "⏭️":
            return "next"
        elif reaction.emoji == "1️⃣":
            return "1"
        elif reaction.emoji == "2️⃣":
            return "2"
        elif reaction.emoji == "3️⃣":
            return "3"
        elif reaction.emoji == "4️⃣":
            return "4"
        elif reaction.emoji == "5️⃣":
            return "5"
        elif reaction.emoji == "6️⃣":
            return "6"
        elif reaction.emoji == "7️⃣":
            return "7"
        elif reaction.emoji == "8️⃣":
            return "8"
        elif reaction.emoji == "9️⃣":
            return "9"
        elif reaction.emoji == "🔟":
            return "10"
        else:
            await ctx.send("check関数に関連するエラーです。開発者に報告してください。")
            return "timeout"

    @commands.command(aliases=["find","once"])
    async def search(self, ctx, *args):
        if len(args) == 0:
            return await ctx.send("引数に検索ワードを入力してください。")

        q = args[0]
        results = self.search_music(q)
        if len(results) == 0:
            return await ctx.send("対象の文字列を含む音楽ファイルは見つかりませんでした。")
        display_list = []

        for i in range((len(results)//10)+1):
            display_list.append(results[i*10:(i+1)*10])

        embed_list = []

        for page, part in enumerate(display_list, 1):
            embed = discord.Embed(title=f"検索結果：{str(page)}ページ目", color=0x00d9ff)
            for i, data in enumerate(part, 1):
                embed.add_field(name=str(i), value=data.get('title'), inline=False)
            else:
                embed.set_footer(text=f"検索結果：{str(len(results))}件\n⏮️：前ページ ⏹️：検索終了 ▶️：検索結果をキューに入れる ⏭️：次ページ")
                embed_list.append(embed)

        page = 0

        while True:
            sign = await self.display_search(ctx, embed_list[page], len(display_list[page]))
            if sign == "next":
                page = page + 1
                if page >= len(embed_list):
                    page = page - len(embed_list)
            elif sign == "prev":
                page = page - 1
                if page < 0:
                    page = page + len(embed_list)
            elif sign == "play":
                status = self.music_statuses.get(ctx.guild.id)
                if status is None:
                    await ctx.invoke(self.join)
                    await ctx.send("ボイスチャンネルに参加します。")
                    status = self.music_statuses.get(ctx.guild.id)
                for musicfile in results:
                    file_id = musicfile['id']
                    file_name = musicfile['title']
                    await status.add_music(file_id, file_name)
                await ctx.send("検索結果をキューに入れました。\n検索を終了します。")
                break
            elif sign == "stop" or sign == "timeout":
                await ctx.send("検索を終了します。")
                break
            else:
                status = self.music_statuses.get(ctx.guild.id)
                if status is None:
                    await ctx.invoke(self.join)
                    await ctx.send("ボイスチャンネルに参加します。")
                    status = self.music_statuses.get(ctx.guild.id)
                seq = int(sign)
                musicfile = display_list[page][seq-1]
                file_id = musicfile['id']
                file_name = musicfile['title']
                await status.add_music(file_id, file_name)
                await ctx.send(f"{file_name}を再生リストに追加しました。\n検索を終了します。")
                break


    @commands.command()
    async def reset(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        status.queue.reset()
        return await ctx.send("再生リストを空にしました。")

    @commands.command(aliases=["np", "current"])
    async def nowplaying(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if not status.is_playing:
            return await ctx.send('現在再生している曲はありません。')
        embed = discord.Embed(color=0x30ff30)
        embed.add_field(name="nowplaying", value=status.current_title, inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["lq", "loopqueue"])
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
        await ctx.send("現在再生中の曲を停止します。")
        queue = status.get_list()
        if len(queue) == 0:
            await ctx.send('なお、現在キューは空になっています。playコマンド等で次の曲を追加してください。')
        else:
            await ctx.send("次の曲を再生します。")
        status.stop()


    @commands.command()
    async def pause(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if status.is_paused:
            await ctx.send("既に一時停止中です。")
        else:
            status.pause()
            await ctx.send("再生を一時停止しました。再開はresumeです。")

    @commands.command()
    async def resume(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('Botはまだボイスチャンネルに参加していません')
        if status.is_paused:
            await ctx.send("再生を再開します。")
            status.resume()
        else:
            await ctx.send("再生するための曲がありません。")

    @commands.command(aliases=["sh", "mix", "random"])
    async def shuffle(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('先にボイスチャンネルに参加してください')
        status.shuffle()
        await ctx.send("再生リストをシャッフルしました。")

    async def display_queue(self, ctx, embed):
        msg = await ctx.send(embed=embed)

        emojis = ["⏮️", "⏹️", "⏭️"]
        for emoji in emojis:
            await msg.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and reaction.emoji in emojis and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=120.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("リアクションの受付が終了しました。")
            return "timeout"

        if reaction.emoji == "⏮️":
            return "prev"
        elif reaction.emoji == "⏹️":
            return "stop"
        elif reaction.emoji == "⏭️":
            return "next"

    @commands.command(aliases=["q", "playlist"])
    async def queue(self, ctx):
        status = self.music_statuses.get(ctx.guild.id)
        if status is None:
            return await ctx.send('先にボイスチャンネルに参加してください')
        queue = status.get_list()
        if len(queue) == 0:
            return await ctx.send('現在キューは空になっています。playコマンド等で曲を追加してください。')

        display_list = []

        for i in range((len(queue)//10)+1):
            display_list.append(queue[i*10:(i+1)*10])

        embed_list = []

        for page, part in enumerate(display_list, 1):
            embed = discord.Embed(title=f"{str(page)}ページ目", color=0xffa030)
            for i, data in enumerate(part, 1):
                embed.add_field(name=str(i), value=data[1], inline=False)
            else:
                embed.set_footer(text=f"現在のキュー：{str(len(queue))}件\n⏮️：前ページ ⏹️：観覧終了 ⏭️：次ページ")
                embed_list.append(embed)

        page = 0

        while True:
            sign = await self.display_queue(ctx, embed_list[page])
            if sign == "next":
                page = page + 1
                if page >= len(embed_list):
                    page = page - len(embed_list)
            elif sign == "prev":
                page = page - 1
                if page < 0:
                    page = page + len(embed_list)
            else:
                await ctx.send("観覧を終了します。")
                break


def setup(bot):
    return bot.add_cog(Music(bot))
