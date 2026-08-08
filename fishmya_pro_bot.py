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

# Global State
bot_running = False
status_message_id = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Start Bot 🚀", callback_data="start_bot")],
        [InlineKeyboardButton("Stop Bot 🛑", callback_data="stop_bot")]
    ])

async def update_status(context, text):
    global status_message_id
    try:
        if status_message_id:
            await context.bot.edit_message_text(chat_id=CHAT_ID, message_id=status_message_id, text=text, reply_markup=get_keyboard())
        else:
            msg = await context.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=get_keyboard())
            status_message_id = msg.message_id
    except Exception:
        msg = await context.bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=get_keyboard())
        status_message_id = msg.message_id

async def send_photo(context, path, caption):
    try:
        with open(path, "rb") as photo:
            await context.bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=f"📸 {caption}")
    except Exception as e:
        logging.error(f"Send photo error: {e}")

def find_template(screen_path, template_name, threshold=0.7):
    template_path = f"assets/{template_name}.png"
    if not os.path.exists(template_path): return None
    img = cv2.imread(screen_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, 0)
    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    for pt in zip(*loc[::-1]):
        return (pt[0] + template.shape[1]//2, pt[1] + template.shape[0]//2)
    return None

async def click_cv(page, template_name, timeout=10):
    for _ in range(timeout):
        path = f"tmp_{template_name}.png"
        await page.screenshot(path=path)
        coords = find_template(path, template_name)
        if coords:
            await page.mouse.click(*coords)
            os.remove(path)
            return True
        await asyncio.sleep(1)
    return False

async def game_automation(context):
    global bot_running
    while bot_running:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(viewport={'width': 1000, 'height': 1000})
                page = await ctx.new_page()
                
                await update_status(context, "🔄 ဂိမ်းထဲဝင်နေပါပြီ...")
                await page.goto(GAME_URL)
                await asyncio.sleep(30)
                
                # Popups
                await update_status(context, "🧹 Popup များပိတ်နေပါသည်...")
                for _ in range(5):
                    await click_cv(page, "close_blue", 2)
                    await click_cv(page, "close_purple", 2)
                
                # Daily Reward
                await update_status(context, "🎁 Daily Reward ယူနေပါသည်...")
                if await click_cv(page, "daily_reward"):
                    await asyncio.sleep(5)
                    # Click multiple check-in areas
                    for x, y in [(165, 465), (355, 465), (545, 465), (165, 655), (355, 655), (545, 655), (785, 560)]:
                        await page.mouse.click(x, y)
                        await asyncio.sleep(0.5)
                    await page.mouse.click(88, 241) # Back
                
                # Enter Game
                await update_status(context, "🎮 Fish Hunter ထဲဝင်နေပါသည်...")
                await click_cv(page, "les_t_shot")
                await asyncio.sleep(15)
                
                # Auto Fishing
                await update_status(context, "🎣 အလိုအလျောက် ငါးဖမ်းနေပါသည် (X4 နှိပ်နေသည်)...")
                await click_cv(page, "auto_btn")
                await click_cv(page, "target_btn")
                
                await page.screenshot(path="fishing.png")
                await send_photo(context, "fishing.png", "ငါးဖမ်းခြင်း စတင်ပါပြီ")

                counter = 0
                while bot_running:
                    await page.mouse.click(45, 450) # X4
                    counter += 1
                    if counter % 60 == 0:
                        await update_status(context, f"✅ ငါးဖမ်းနေသည်မှာ {counter} စက္ကန့်ရှိပါပြီ...")
                        await page.screenshot(path="status.png")
                        await send_photo(context, "status.png", f"Status: {counter}s")
                    if counter % 300 == 0: break
                    await asyncio.sleep(1)
                
                await browser.close()
        except Exception as e:
            logging.error(f"Bot error: {e}")
            await asyncio.sleep(10)

async def start_cmd(update, context):
    await update.message.reply_text("FishMya Pro CV Bot အဆင်သင့်ဖြစ်ပါပြီ။", reply_markup=get_keyboard())

async def button_handler(update, context):
    global bot_running
    query = update.callback_query
    await query.answer()
    if query.data == "start_bot":
        if not bot_running:
            bot_running = True
            await update_status(context, "🚀 Bot စတင်နေပါပြီ...")
            asyncio.create_task(game_automation(context))
    elif query.data == "stop_bot":
        bot_running = False
        await update_status(context, "🛑 Bot ကို ရပ်တန့်လိုက်ပါပြီ။")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
