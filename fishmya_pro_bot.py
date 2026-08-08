import os
import logging
import asyncio
from playwright.async_api import async_playwright
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8941522018:AAFTGW_vaGgJyqEh-g-Hn_he3BjBzRYiM2k")
CHAT_ID = os.getenv("CHAT_ID", "8458492763")
GAME_URL = os.getenv("GAME_URL", """https://fishmya.ugame.vn/index.html?access_token=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJkMDBvMWdJdXhnTHNsY1BoT0tuNkVwNkNLVEw5U21mWEU3ZUVDUUV5OUk4In0.eyJqdGkiOiJhM2NkZTE5MS1lNmRmLTRhYTItOWU2ZS04NTQ5MjUzMjEwZjMiLCJleHAiOjE3ODgxNDkwNTMsIm5iZiI6MCwiaWF0IjoxNzg1NDcwNjUzLCJpc3MiOiJodHRwczovL2lkLm15dGVsLmNvbS5tbS9hdXRoL3JlYWxtcy9jaW0iLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNzZlNjIxNTUtZjdiYS00ZWI4LWJhNjUtNjNkMjI0ODhmOGViIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiY3BtLWNsaWVudCIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6IjQ2MjcxNDgxLTNhNTQtNGNmYi05OTNiLWQ4MmQzNjlkMmYxMiIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdionXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6InByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInByZWZlcnJlZF91c2VybmFtZSI6InRkeWcobmoiLCJpZCI6Ijc2ZTYyMTU1LWY3YmEtNGViOC1iYTY1LTYzZDIyNDhmOGZlYiJ9Lmtvd0FRT1JYQnQxOVdCNmZVM0oxVXpRZ185bkQ5bWVsSFhGa3c1QzRqY1ZUYU5IWmdIcWVSLVFIR0NPY3JReDd0NF9BdGNla3J6X1RzdTVOYS1fRVlkdXZYSGlCOTVnSXlGLUtHNlhYa0tiQ1gteGxOeHA3ZVliZnlhcXF1Y09FZ1I1bnBZZ29yWEprQTVnNG1CMkNzbcnlUFZNMWIxQ0xWdjdTZUx2NVVhYjRsWS1EbmpiZFQ5SUZOQ0ZyRWdRM2MwcEFTRVU5WVdLNWpwWEd5QmtEQTV6eTZDemd6RGpKMm5sSmk4M0pWTzFWbS1YWjBiYm4tenVwSkZfMzdJNU43ODhINlV5aXV4d0NudGtxaWNENzZsMGNET2xEQ1k5WmpwMXdQWWlmTS1DSDBjSnV3dHRGXzJTSWhMNUlqeEJRUXYtY1YzeWdSSUhsVzF2dWwtQUxRJmxvZz10cnVlJmNwPW15aWQmbGFuZz1teSZ3c3M9dHJ1ZSZ0PTE3MjIzMTE5NDE=""")

# Coordinates
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
        # Action အားလုံး ပြီးဆုံးပြီး screen တည်ငြိမ်သွားစေရန် ၂ စက္ကန့် စောင့်ပါမည်
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
                await asyncio.sleep(30) # ဂိမ်း load လုပ်ရန် စောင့်ခြင်း
                
                await update_status(context, "🌐 ဂိမ်းသို့ အောင်မြင်စွာ ရောက်ရှိပါပြီ။")
                await send_screenshot(context, page, "ဂိမ်း စတင်ဝင်ရောက်ပြီးချိန်")
                
                # Close Popups
                await update_status(context, "🧹 Popup များပိတ်နေပါသည်...")
                for _ in range(3):
                    await page.mouse.click(*COORDS["close_popup_blue"])
                    await asyncio.sleep(2)
                    await page.mouse.click(*COORDS["close_popup_purple"])
                    await asyncio.sleep(2)
                
                await send_screenshot(context, page, "Popup များ ပိတ်ပြီးနောက်")
                
                # Daily Reward
                await update_status(context, "🎁 Daily Reward ယူနေပါသည်...")
                await page.mouse.click(*COORDS["daily_reward_icon"])
                await asyncio.sleep(5)
                for day in ["check_in_day_1", "check_in_day_2", "check_in_day_3", "check_in_day_4", "check_in_day_5", "check_in_day_6", "check_in_day_7"]:
                    await page.mouse.click(*COORDS[day])
                    await asyncio.sleep(1)
                
                await send_screenshot(context, page, "Daily Reward ယူပြီးနောက်")
                
                # Enter Game
                await update_status(context, "🎮 Fish Hunter ထဲဝင်နေပါသည်...")
                await page.mouse.click(*COORDS["game_card_fish_hunter"])
                await asyncio.sleep(15)
                await page.mouse.click(*COORDS["close_mission_popup"])
                await asyncio.sleep(2)
                
                await send_screenshot(context, page, "Fish Hunter ဂိမ်းတွင်းသို့ ရောက်ရှိချိန်")
                
                # Auto Fishing
                await update_status(context, "🎣 အလိုအလျောက် ငါးဖမ်းနေပါသည် (X4 နှိပ်နေသည်)...")
                await page.mouse.click(*COORDS["auto_button"])
                await asyncio.sleep(2)
                await page.mouse.click(*COORDS["target_button"])
                await asyncio.sleep(2)
                
                await send_screenshot(context, page, "Auto နှင့် Target ဖွင့်ပြီးချိန်")
                
                # Loop X4
                counter = 0
                while bot_running:
                    await page.mouse.click(*COORDS["x4_button"])
                    counter += 1
                    if counter % 30 == 0:
                        await update_status(context, f"✅ ငါးဖမ်းနေသည်မှာ {counter} စက္ကန့်ရှိပါပြီ...")
                    
                    if counter % 300 == 0:  # Every 5 mins, take screenshot & refresh
                        await update_status(context, "🔄 ၅ မိနစ်ပြည့်၍ အခြေအနေ screenshot ရိုက်ထားပါသည်။")
                        await send_screenshot(context, page, f"ငါးဖမ်းနေဆဲ ({counter} စက္ကန့်)")
                        break 
                    
                    await asyncio.sleep(1)
                
                await browser.close()
        except Exception as e:
            await update_status(context, f"⚠️ Error ဖြစ်ပွားပါသည်: {str(e)[:50]}... ပြန်လည်စတင်နေပါသည်...")
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
