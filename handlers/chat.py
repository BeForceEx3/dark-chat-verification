from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import DATAPATH, ADMINID
from utils.storage import loaddata, savedata
import time

userpartners = {}
waitingsince = {}

def reloaddata():
    """Загружает partners и messages глобально"""
    global userpartners
    partners, messages = loaddata(DATAPATH)
    userpartners = partners[file:1]

# Остальной код findpartner и stopchat без изменений...
