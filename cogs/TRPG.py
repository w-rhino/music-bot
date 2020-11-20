# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 17:59:12 2020

@author: sone daichi
"""
import re
import csv
import os

import discord
from discord.ext import commands

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from .diceroll import DiceRoll

class TRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.powerlist = {}
        self.chara_datalist = {}
        self.pattern_power = '\d{1,2}'
        self.gauth = GoogleAuth()
        self.gauth.CommandLineAuth()
        self.drive = GoogleDrive(self.gauth)

    def load_powerlist(self, path):
        with open(path, newline='', encoding='utf-8-sig') as csvfile:
            read = csv.DictReader(csvfile)
            for row in read:
                tmp = {}
                tmp = row
                self.powerlist[row.get('power')] = tmp

    def load_charadata(self):
        self.drive = GoogleDrive(self.gauth)

        dir_id = self.drive.ListFile({'q': 'title = "sword_world"'}).GetList()[0]['id']
        chara_metadata = self.drive.ListFile({'q': '"{}" in parents and title = "charadata"'.format(dir_id)}).GetList()
        data_id = chara_metadata[0]['id']

        f = self.drive.CreateFile({'id': data_id})
        data_path = os.path.join('/tmp', 'chara.csv')
        f.GetContentFile(data_path, mimetype='text/csv')

        with open(data_path, newline='', encoding='utf-8-sig') as csvfile:
            readdata = csv.DictReader(csvfile)
            for row in readdata:
                tmp = {}
                tmp = row
                tmp['DEX_bonus'] = self.bonus(int(row.get('DEX')))
                tmp['AGI_bonus'] = self.bonus(int(row.get('AGI')))
                tmp['STR_bonus'] = self.bonus(int(row.get('STR')))
                tmp['VIT_bonus'] = self.bonus(int(row.get('VIT')))
                tmp['INT_bonus'] = self.bonus(int(row.get('INT')))
                tmp['MND_bonus'] = self.bonus(int(row.get('MND')))
                self.chara_datalist[row.get('discord_user_name')] = tmp

        os.remove(data_path)

    def bonus(self, parameter):
        return int(parameter//6)

    def culcPower(self, value, sum_dice):
        pwr = self.powerlist.get(str(value))
        damage = pwr.get(str(sum_dice))

        return damage

    def culcPowerInv(self, value, sum_dice):
        pwr = self.powerlist.get(str(value))
        damageInv = pwr.get(str(14 - sum_dice))

        return damageInv

    def judge_Power(self, src):
        repatter = re.compile(self.pattern_power)
        result = repatter.fullmatch(src)
        if result is not None:
            if int(result.group()) <= 80:
                return True
        return False

    @commands.command(aliases = ["p","威力"])
    async def power(self, ctx, *args):
        if len(args) == 0:
            await ctx.send('威力となる引数が必要です。')
            return
        if self.judge_Power(args[0]) == False:
            await ctx.send('威力となる引数が正しくありません。80以下の数字を入力してください。')
            return
        num, times, result, sum_dice = DiceRoll().nDn('2D6')
        pwr = self.culcPower(args[0], sum_dice)
        pwrInv = self.culcPowerInv(args[0], sum_dice)
        await ctx.send('出目：' + str(result) + '\nダメージ：' + pwr + '\n運命変転時ダメージ：' + pwrInv)

    @commands.command(aliases = ["searchpower", "search"])
    async def sp(self, ctx, *args):
        if len(args) < 2:
            await ctx.send('引数として威力、ダイスの合計値が必要です。')
            return
        if self.judge_Power(args[0]) == False:
            await ctx.send('威力となる引数が正しくありません。80以下の数字を入力してください。')
            return
        if int(args[1]) > 12 or int(args[1]) < 2:
            await ctx.send('ダイスの合計値が不正です。２～１２の数字を入力してください。')
            return
        pwr = self.culcPower(args[0], int(args[1]))
        pwrInv = self.culcPowerInv(args[0], int(args[1]))
        await ctx.send('ダイス合計値：' + args[1] + '\nダメージ：' + pwr + '\n運命変転時ダメージ：' + pwrInv)


    @commands.command()
    async def charaLoad(self, ctx):
        await ctx.send("スプレッドシートのキャラデータをロード中です…")
        self.load_charadata()
        await ctx.send("ロードが完了しました。")

    @commands.command(aliases = ["st","parameter"])
    async def status(self, ctx):
        data = self.chara_datalist.get(ctx.author.name)

        embed = discord.Embed(title=data.get('character_name'), color=0xe657ee)

        msg = "最大HP：" + str(data.get('HP')) + "\n" + \
        "最大MP：" + str(data.get('MP')) + "\n" + \
        "器用度：" + str(data.get('DEX')) + "，ボーナス：" + str(data.get('DEX_bonus')) + "\n" + \
        "敏捷度：" + str(data.get('AGI')) + "，ボーナス：" + str(data.get('AGI_bonus')) + "\n" + \
        "筋力：" + str(data.get('STR')) + "，ボーナス：" + str(data.get('STR_bonus')) + "\n" + \
        "生命力：" + str(data.get('VIT')) + "，ボーナス：" + str(data.get('VIT_bonus')) + "\n" + \
        "知力：" + str(data.get('INT')) + "，ボーナス：" + str(data.get('INT_bonus')) + "\n" + \
        "精神力：" + str(data.get('MND')) + "，ボーナス：" + str(data.get('MND_bonus')) + "\n" + \
        "生命抵抗力：" + str(data.get('RES_VITAL')) + "\n" + \
        "精神抵抗力：" + str(data.get('RES_MENTAL')) + "\n" + \
        "技巧判定：" + str(data.get('judge_tech')) + "\n" + \
        "運動判定：" + str(data.get('judge_physical')) + "\n" + \
        "観察判定："+ str(data.get('judge_obs')) + "\n" + \
        "(魔物)知識判定：" + str(data.get('judge_wisdom')) + "\n" + \
        "先制力：" + str(data.get('initiative')) + "\n" + \
        "移動力：" + str(data.get('moving'))

        embed.add_field(name="ステータス", value=msg, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def judge(self, ctx, *args):
        data = self.chara_datalist.get(ctx.author.name)

        if len(args) == 0:
            await ctx.send("何の判定か、加えて目標値を入力してください。\n技巧判定：tec\n運動判定：phy\n観察判定：obs\n(魔物)知識判定：wis\n先制判定：ini")
            return
        if len(args) == 1:
            await ctx.send("判定の目標値を入力してください。")
            return

        goal = int(args[1])
        num, times, result, sum_dice = DiceRoll().nDn('2D6')
        total = int(sum_dice)
        msg = data.get("character_name") + "の"
        if args[0] == 'tec':
            msg = msg + "技巧判定"
            total = total + int(data.get("judge_tech"))
        elif args[0] == 'phy':
            msg = msg + "運動判定"
            total = total + int(data.get("judge_phy"))
        elif args[0] == 'obs':
            msg = msg + "観察判定"
            total = total + int(data.get("judge_obs"))
        elif args[0] == 'wis':
            msg = msg + "(魔物)知識判定"
            total = total + int(data.get("judge_wisdom"))
        elif args[0] == 'ini':
            msg = msg + "先制判定"
            total = total + int(data.get("initiative"))
        else:
            await ctx.send("引数が異なります。\n技巧判定：tec\n運動判定：phy\n観察判定：obs\n(魔物)知識判定：wis\n先制判定：ini")
            return

        msg = msg + "を行います。\n判定合計値：" + str(total) + "，目標値：" + args[1]
        if total < goal:
            msg = msg + "\n判定失敗です…"
        else:
            msg = msg + "\n判定成功です！"

        await ctx.send(msg)

    @commands.command(aliases = ["atk","攻撃"])
    async def attack(self, ctx):
        data = self.chara_datalist.get(ctx.author.name)

        num, times, result, sum_dice = DiceRoll().nDn('2D6')
        if sum_dice == 2:
            damage = str(self.culcPower(data.get('weapon_power'), sum_dice))
        else:
            damage = int(data.get('total_damage')) + int(self.culcPower(data.get('weapon_power'), sum_dice))
        #damageInv = int(data.get('total_damage')) + int(culcPowerInv(data.get('weapon_power'), sum_dice))

        damagemsg = data.get('character_name') + "の通常攻撃！\n" + "出目：" + str(result) + "\nダメージ：" + str(damage)
        crimsg = "通常クリティカル値は" + data.get('weapon_critical') + "です。\nクリティカルの場合、$p " + data.get('weapon_power') + "を入力してそのダメージを加算してください。"

        await ctx.send(damagemsg + "\n" + crimsg)


def setup(bot):
    return bot.add_cog(TRPG(bot))
