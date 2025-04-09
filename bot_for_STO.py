import logging
import psycopg2
from datetime import datetime, timedelta, date
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

# =============== НАСТРОЙКИ ===============
TOKEN = "ВАШ ТОКЕН" 

DB_CONFIG = {
    "host": "localhost",
    "user": "postgres", # НАЗВАНИЕ БД КОТОРУЮ ИСПОЛЬЗУЕТЕ
    "password": "ВАШ ПАРОЛЬ",
    "dbname": "ВАШЕ НАЗВАНИЕ СОЗДАННОГО БД"
}

ADMIN_CHAT_ID = 0 #АЙДИ АДМИНИСТРАТОРА (НЕ ЮЗЕРНЕЙМ)

# =============== СОСТОЯНИЯ ===============
NAME, PHONE, CAR, PROBLEM, PICK_DATE, PICK_TIME = range(6)

logging.basicConfig(level=logging.INFO)

# =============== КЛАВИАТУРЫ ===============
main_menu_keyboard = ReplyKeyboardMarkup(
    [["Записаться"], ["Контакты", "Услуги"]],
    resize_keyboard=True
)

back_to_menu_keyboard = ReplyKeyboardMarkup(
    [["🔙 В главное меню"]],
    resize_keyboard=True
)

# =============== СОХРАНЕНИЕ В БД ===============
def save_to_db(data):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            name TEXT,
            phone TEXT,
            car TEXT,
            problem TEXT,
            preferred_datetime TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.execute("""
        INSERT INTO service_requests (user_id, name, phone, car, problem, preferred_datetime)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data["user_id"],
        data["name"],
        data["phone"],
        data["car"],
        data["problem"],
        data["datetime"]
    ))
    conn.commit()
    cur.close()
    conn.close()

# =============== ВСПОМОГАТЕЛЬНОЕ ===============
def get_date_keyboard():
    today = date.today()
    buttons = []
    for i in range(6):
        d = today + timedelta(days=i)
        buttons.append([InlineKeyboardButton(d.strftime("%d.%m.%Y"), callback_data=f"date|{d}")])
    return InlineKeyboardMarkup(buttons)

def get_time_keyboard(selected_date):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT preferred_datetime FROM service_requests
        WHERE DATE(preferred_datetime) = %s
    """, (selected_date,))
    existing = [row[0].strftime("%H:%M") for row in cur.fetchall()]
    cur.close()
    conn.close()

    times = [f"{hour:02d}:00" for hour in range(9, 18)]
    buttons = []
    row = []
    for t in times:
        if t not in existing:
            row.append(InlineKeyboardButton(t, callback_data=f"time|{t}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Назад к дате", callback_data="back_to_date")])
    return InlineKeyboardMarkup(buttons)

# =============== ХЕНДЛЕРЫ ===============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Добро пожаловать в Telegram-бот автосервиса!\nВыберите действие:",
        reply_markup=main_menu_keyboard
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Контакты":
        await update.message.reply_text("📍 Ростов-на-Дону\n📞 +79614021441\n🕘 Пн-Сб: 09:00–19:00")
    elif text == "Услуги":
        await update.message.reply_text("🛠 Замена масла\n🔧 Диагностика двигателя\n🚗 Шиномонтаж\n📦 ТО и ремонт подвески")
    elif text == "🔙 В главное меню":
        await back_to_main(update, context)

# =============== ЗАПИСЬ КЛИЕНТА ===============
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как вас зовут?", reply_markup=back_to_menu_keyboard)
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 В главное меню":
        return await back_to_main(update, context)
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Ваш номер телефона (например: +79991234567):")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 В главное меню":
        return await back_to_main(update, context)
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Марка/модель автомобиля:")
    return CAR

async def get_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 В главное меню":
        return await back_to_main(update, context)
    context.user_data["car"] = update.message.text
    await update.message.reply_text("Какая проблема/услуга вас интересует?")
    return PROBLEM

async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 В главное меню":
        return await back_to_main(update, context)
    context.user_data["problem"] = update.message.text
    await update.message.reply_text("Выберите удобную дату:", reply_markup=get_date_keyboard())
    return PICK_DATE

async def pick_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, date_str = query.data.split("|")
    context.user_data["selected_date"] = date_str
    await query.message.edit_text("Выберите удобное время:", reply_markup=get_time_keyboard(date_str))
    return PICK_TIME

async def pick_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_date":
        await query.message.edit_text("Выберите удобную дату:", reply_markup=get_date_keyboard())
        return PICK_DATE
    _, time_str = query.data.split("|")
    selected_date = context.user_data["selected_date"]
    full_datetime = datetime.strptime(f"{selected_date} {time_str}", "%Y-%m-%d %H:%M")

    context.user_data["datetime"] = full_datetime
    context.user_data["user_id"] = query.from_user.id

    save_to_db(context.user_data)

    message = (
        "📬 Новая заявка на СТО:\n"
        f"👤 Имя: {context.user_data['name']}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"🚗 Авто: {context.user_data['car']}\n"
        f"🔧 Проблема: {context.user_data['problem']}\n"
        f"📅 Время: {full_datetime.strftime('%d.%m.%Y, %H:%M')}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

    await query.message.edit_text("✅ Ваша заявка принята! Мы свяжемся с вами в ближайшее время.")
    return ConversationHandler.END

# =============== СБРОС ===============
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Вы вернулись в главное меню. Выберите действие:",
        reply_markup=main_menu_keyboard
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=main_menu_keyboard)
    return ConversationHandler.END

# =============== ЗАПУСК ===============
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Записаться$"), ask_name)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_car)],
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
            PICK_DATE: [CallbackQueryHandler(pick_date, pattern="^date|.*")],
            PICK_TIME: [CallbackQueryHandler(pick_time, pattern="^(time|back_to_date).*")]
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🔙 В главное меню$"), back_to_main),
            CommandHandler("cancel", cancel)
        ],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
