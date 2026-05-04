import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import time
import pytz

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("API_KEY")
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
            return None, None, None, None, None
        wind_ms = res["wind"]["speed"]
        wind_kmh = round(wind_ms * 3.6, 2)  # ✅ convert m/s to km/h
        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]
        weather_desc = res["weather"][0]["description"]
        
        # 🌧️ Extract rain data (last 1 hour in mm)
        rain_1h = res.get("rain", {}).get("1h", 0)
        
        return wind_kmh, temp, humidity, weather_desc, rain_1h
    except:
        return None, None, None, None, None


# 🧠 Safety logic
def get_status(wind, humidity):
    if wind is None:
        return "❌ Data unavailable"
    if wind < 20:
        return "✅ SAFE"
    elif wind < 40:
        return "🟡 MODERATE"
    else:
        return "🔴 DANGER"


# 📩 Generate report
def generate_report():
    message = "🚢 *Marine Multi-Location Safety Report*\n\n"
    for loc in locations:
        wind, temp, humidity, desc, rain = get_weather(loc["lat"], loc["lon"])
        message += f"📍 *{loc['name']}*\n"
        if wind is None:
            message += "❌ Data unavailable\n\n"
            continue
        status = get_status(wind, humidity)
        message += f"🌬 Wind: {wind} km/h\n"
        message += f"🌡 Temp: {temp} °C\n"
        message += f"💧 Humidity: {humidity}%\n"
        message += f"🌤 Condition: {desc}\n"
        
        # 🌧️ Add rain information
        if rain > 0:
            message += f"🌧️ Rain: {rain} mm/h\n"
        else:
            message += f"🌧️ Rain: No rain\n"
        
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


# 🚀 Startup message
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

app.post_init = on_startup

job_queue = app.job_queue

# ⏰ Schedule with IST timezone
scheduled_times = ["06:00", "10:00", "14:00", "18:00", "22:00"]

for t in scheduled_times:
    hour, minute = map(int, t.split(":"))
    job_queue.run_daily(
        auto_send,
        time(hour=hour, minute=minute, tzinfo=IST)
    )
    print(f"Scheduled for {hour:02d}:{minute:02d} IST")

print("Bot started...")
app.run_polling()