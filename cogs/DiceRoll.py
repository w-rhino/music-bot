# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 11:34:01 2020

@author: sone daichi
"""
import discord
import re
import random
from discord.ext import commands

class DiceRoll(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.pattern = '\d{1,3}d\d{1,3}|\d{1,3}D\d{1,3}'
        self.split_pattern = 'd|D'
        
    #入力した文字がnDnに合致するか
    def judge_nDn(self, src):
        repatter = re.compile(self.pattern)
        result = repatter.fullmatch(src)
        if result is not None:
            return True
        return False

    #nDnの数字を前半と後半に分ける
    def split_nDn(self, src):
        return re.split(self.split_pattern,src)

#ダイスロール
    def roll_nDn(self, src):
        result = []
        sum_dice = 0
        roll_index = self.split_nDn(src)
        roll_count = int(roll_index[0])
        nDice = int(roll_index[1])
        
        for i in range(roll_count):
            tmp = random.randint(1,nDice)
            result.append(tmp)
            sum_dice = sum_dice + tmp
        
        is1dice = True if roll_count == 1 else False
        
        return result,sum_dice,is1dice

    #入力と出力
    def nDn(self, text):
        if self.judge_nDn(text):
            result,sum_dice,is1dice = self.roll_nDn(text)
            spl = self.split_nDn(text)
            return spl[1],spl[0],result,sum_dice
        else:
            return 0,0,[],0      
    
    #event(on_XX)で動かしたい場合はcommands.Cog.listener()を用いること。
        
    @commands.command(aliases = ["roll","dice"])
    async def r(self, ctx, *args):
        tmp = None
        if len(args) == 0:
            tmp = '2D6'
        else:
            tmp = args[0]
        if self.judge_nDn(args[0]) == False:
            await ctx.send('引数が正しくありません。入力しなおして下さい。')
            return            
        num, times, result, sum_dice = self.nDn(tmp)
        if result is not None:
            await ctx.send(ctx.author.name + 'さんのダイスロール\n' + num + '面ダイスを' + times + '回振ります。\n出目：' + str(result) + '\n合計：' + str(sum_dice)) 

def setup(bot):
    return bot.add_cog(DiceRoll(bot))        