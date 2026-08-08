import os
import logging
import asyncio
import cv2
import numpy as np
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8941522018:AAFTGW_vaGgJyqEh-g-Hn_he3BjBzRYiM2k")
CHAT_ID = os.getenv("CHAT_ID", "8458492763")
GAME_URL = os.getenv("GAME_URL", """https://fishmya.ugame.vn/index.html?access_token=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJkMDBvMWdJdXhnTHNsY1BoT0tuNkVwNkNLVEw5U21mWEU3ZUVDUUV5OUk4In0.eyJqdGkiOiJhM2NkZTE5MS1lNmRmLTRhYTItOWU2ZS04NTQ5MjUzMjEwZjMiLCJleHAiOjE3ODgxNDkwNTMsIm5iZiI6MCwiaWF0IjoxNzg1NDcwNjUzLCJpc3MiOiJodHRwczovL2lkLm15dGVsLmNvbS5tbS9hdXRoL3JlYWxtcy9jaW0iLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNzZlNjIxNTUtZjdiYS00ZWI4LWJhNjUtNjNkMjI0ODhmOGViIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiY3BtLWNsaWVudCIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6IjQ2MjcxNDgxLTNhNTQtNGNmYi05OTNiLWQ4MmQzNjlkMmYxMiIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoidGR5ZyhuaiIsImlkIjoiNzZlNjIxNTUtZjdiYS00ZWI4LWJhNjUtNjNkMjI0ODhmOGViIn0.kowAQORXBt19WB6fU3J1UzQg_9nD9melHXFkw5C4jcVTaNHZgHqeR-QHGCOcrQx7t4_Atcekrz_Tsu5Na-_EYduvXHiB95gIyF-KGq6XkKBbCX-xlNxp7eYBfyaqqucOEgR5npYcorXJkA5g4mB2CsnryPVM1b1CLVv7SeLv5Uab4lY-DnjbdT9IFNCFrEgQ3c0pASEU9YWK5jpXGyBkDA5zy6CzgzDaJ2nlJi83JVO1Vm-XZ0bbn-zupJF_37I5N788H6UyiuxwCntkqicD76l0cDOlDCY9Zjp1wPYifM-CH0cJuWwtF_2SIhL5IjxBQQv-cV3ygRIHlW1vul-ALQ&log=true&cp=myid&lang=my&wss=true&t=1722311941""")

# Coordinates (Fallback)
COORDS = {
    "close_popup_blue": (733, 324),
    "close_popup_purple": (645, 355),
    "daily_reward_icon": (60, 345),
    "check_in_day_1": (165, 465),
    "check_in_day_2": (355, 465),
    "check_in_day_3": (545, 465),
    "check_in_day_4": (165, 655),
    "check_in_day_5": (355, 655),
    "check_in_day_6": (545, 655),
    "check_in_day_7": (785, 560),
    "back_button": (88, 241),
    "game_card_fish_hunter": (150, 500),
    "auto_button": (45, 275),
    "target_button": (45, 530),
    "close_mission_popup": (900, 250),
    "x4_button": (45, 450),
}

# Global State
bot_running = False
status_message_id = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Start Bot 🚀", callback_data="start_bot")],
        [InlineKeyboardButton("Stop Bot 🛑", callback_data="stop_bot")]
    ])

async def update_status(context: ContextTypes.DEFAULT_TYPE, text: str):
    global status_message_id
    try:
        if status_message_id:
            try:
                await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=status_message_id, text=text, reply_markup=get_keyboard())
            except Exception:
                msg = await context.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=get_keyboard())
                status_message_id = msg.message_id
        else:
            msg = await context.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=get_keyboard())
            status_message_id = msg.message_id
    except Exception as e:
        logging.error(f"Status update error: {e}")

async def send_screenshot(context: ContextTypes.DEFAULT_TYPE, page, caption: str):
    try:
        await asyncio.sleep(2)
        screenshot_path = "/tmp/screenshot.png"
        await page.screenshot(path=screenshot_path)
        with open(screenshot_path, "rb") as photo:
            await context.bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=f"📸 {caption}")
    except Exception as e:
        logging.error(f"Screenshot error: {e}")

async def game_automation(context: ContextTypes.DEFAULT_TYPE):
    global bot_running
    while bot_running:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                browser_context = await browser.new_context(viewport={'width': 1000, 'height': 1000})
                page = await browser_context.new_page()
                
                await update_status(context, "🔄 ဂိမ်းထဲဝင်နေပါပြီ...")
                await page.goto(GAME_URL, timeout=60000)
                await asyncio.sleep(30)
                
                await update_status(context, "🌐 ဂိမ်းသို့ အောင်မြင်စွာ ရောက်ရှိပါပြီ။")
                
                # Close Popups
                await update_status(context, "🧹 Popup များပိတ်နေပါသည်...")
                for _ in range(3):
                    await page.mouse.click(*COORDS["close_popup_blue"])
                    await asyncio.sleep(2)
                    await page.mouse.click(*COORDS["close_popup_purple"])
                    await asyncio.sleep(2)
                
                # Daily Reward
                await update_status(context, "🎁 Daily Reward ယူနေပါသည်...")
                await page.mouse.click(*COORDS["daily_reward_icon"])
                await asyncio.sleep(5)
                for day in ["check_in_day_1", "check_in_day_2", "check_in_day_3", "check_in_day_4", "check_in_day_5", "check_in_day_6", "check_in_day_7"]:
                    await page.mouse.click(*COORDS[day])
                    await asyncio.sleep(1)
                
                # Enter Game
                await update_status(context, "🎮 Fish Hunter ထဲဝင်နေပါသည်...")
                await page.mouse.click(*COORDS["game_card_fish_hunter"])
                await asyncio.sleep(15)
                await page.mouse.click(*COORDS["close_mission_popup"])
                await asyncio.sleep(2)
                
                # Auto Fishing
                await update_status(context, "🎣 အလိုအလျောက် ငါးဖမ်းနေပါသည် (X4 နှိပ်နေသည်)...")
                await page.mouse.click(*COORDS["auto_button"])
                await asyncio.sleep(2)
                await page.mouse.click(*COORDS["target_button"])
                await asyncio.sleep(2)
                
                # Loop X4
                counter = 0
                while bot_running:
                    await page.mouse.click(*COORDS["x4_button"])
                    counter += 1
                    if counter % 30 == 0:
                        await update_status(context, f"✅ ငါးဖမ်းနေသည်မှာ {counter} စက္ကန့်ရှိပါပြီ...")
                    
                    if counter % 300 == 0: # Auto-restart every 5 mins
                        break 
                    
                    await asyncio.sleep(1)
                
                await browser.close()
        except Exception as e:
            await update_status(context, f"⚠️ Error ဖြစ်ပွားပါသည်: ပြန်လည်စတင်နေပါသည်...")
            await asyncio.sleep(10)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FishMya Pro Bot မှ ကြိုဆိုပါသည်။ အောက်ပါခလုတ်များဖြင့် ထိန်းချုပ်နိုင်ပါသည်။", reply_markup=get_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_running
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_bot":
        if not bot_running:
            bot_running = True
            await update_status(context, "🚀 Bot စတင်နေပါပြီ...")
            context.application.create_task(game_automation(context))
        else:
            await query.message.reply_text("Bot က အလုပ်လုပ်နေပြီးသားဖြစ်ပါတယ်။")
            
    elif query.data == "stop_bot":
        bot_running = False
        await update_status(context, "🛑 Bot ကို ရပ်တန့်လိုက်ပါပြီ။")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    application.run_polling()
