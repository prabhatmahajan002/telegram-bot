import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import time
import pytz

# 🔑 REPLACE THESE
import os
BOT_TOKEN = os.environ.get("8705367880:AAHidnfXwi5y2KwZ68jg9lrXMPl3oNFZKbY")
API_KEY = os.environ.get("29a0cad8414f4c329e6ba1a05801f3b1")
CHAT_ID = -1003924481330

# 🕐 Set your timezone (IST for India)
IST = pytz.timezone("Asia/Kolkata")

# 📍 Locations
locations = [
    {"name": "Kundalika", "lat": 18.45, "lon": 73.20},
    {"name": "Bankot Creek Bridge", "lat": 17.98, "lon": 73.03},
    {"name": "JSW Jaigarh Port", "lat": 16.59, "lon": 73.35},
    {"name": "Daman (Jampur Beach)", "lat": 20.41, "lon": 72.83}
]


# 🌦 Fetch weather
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url).json()
        if "main" not in res:
            return None, None, None
        return res["wind"]["speed"], res["main"]["temp"], res["main"]["humidity"]
    except:
        return None, None, None


# 🧠 Safety logic
def get_status(wind, humidity):
    if wind is None:
        return "❌ Data unavailable"
    if wind < 20 and humidity < 80:
        return "✅ SAFE"
    elif wind < 35:
        return "🟡 MODERATE"
    else:
        return "🔴 DANGER"


# 📩 Generate report
def generate_report():
    message = "🚢 *Marine Multi-Location Safety Report*\n\n"
    for loc in locations:
        wind, temp, humidity = get_weather(loc["lat"], loc["lon"])
        message += f"📍 *{loc['name']}*\n"
        if wind is None:
            message += "❌ Data unavailable\n\n"
            continue
        status = get_status(wind, humidity)
        message += f"🌬 Wind: {wind} km/h\n"
        message += f"🌡 Temp: {temp} °C\n"
        message += f"💧 Humidity: {humidity}%\n"
        message += f"{status}\n\n"
    return message


# 🤖 Manual /report command
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Manual command received")
    await update.message.reply_text(generate_report(), parse_mode="Markdown")


# ⏰ Auto send job
async def auto_send(context: ContextTypes.DEFAULT_TYPE):
    print("Auto report triggered")
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=generate_report(),
        parse_mode="Markdown"
    )


# 🚀 Startup message — must be async and accept correct signature
async def on_startup(app):
    print("Sending startup report...")
    await app.bot.send_message(
        chat_id=CHAT_ID,
        text=generate_report(),
        parse_mode="Markdown"
    )


# 🚀 MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("report", report))

# ✅ Set post_init BEFORE run_polling
app.post_init = on_startup

job_queue = app.job_queue

# ⏰ Schedule with IST timezone
scheduled_times = ["06:00", "07:00", "08:00", "09:00", "10:00", "11:00" "12:00", "14:00", "18:00", "20:00", "22:00"]

for t in scheduled_times:
    hour, minute = map(int, t.split(":"))
    job_queue.run_daily(
        auto_send,
        time(hour=hour, minute=minute, tzinfo=IST)  # ✅ timezone added
    )
    print(f"Scheduled for {hour:02d}:{minute:02d} IST")

print("Bot started...")
app.run_polling()  # ✅ This must be LAST — it blocks