# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 11:59:11 2020

@author: sone daichi
"""
import os

from pydrive.auth import GoogleAuth

os.chdir(os.path.dirname(os.path.abspath(__file__)))

gauth = GoogleAuth()
gauth.LocalWebserverAuth()