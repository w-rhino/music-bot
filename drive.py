# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 18:35:43 2020

@author: sone daichi
"""
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class drive:
    def __init__(self):
        self.gauth = GoogleAuth()
        self.gauth.CommandLineAuth()
        self.drive = GoogleDrive(gauth)
        