# 🤖 Telegram-бот для автосервиса + 🖥️ Админ-панель  
Полноценный проект для записи клиентов в автосервис через Telegram-бота с удобной веб-админкой для просмотра, редактирования и удаления заявок.

## 🚀 Возможности  
**Бот:**  
- 📋 Запись клиентов (имя, телефон, авто, проблема, дата)  
- 📞 Просмотр контактов  
- 🛠 Список услуг  
- 🔙 Возврат в главное меню  
- ✅ Уведомление администратора о новой записи  

**Админка:**  
- 🔒 Авторизация по логину и паролю  
- 🌓 Переключатель светлой/тёмной темы  
- 🔍 Поиск по имени и номеру телефона  
- 📝 Редактирование и ❌ удаление заявок  
- 💻 Реализация на Flask + PostgreSQL  

## 🧠 Технологии  
- Python 3.12+  
- PostgreSQL  
- psycopg2  
- Flask  
- HTML + CSS  
- Telegram Bot API  

## 📦 Установка  
1. Клонируй репозиторий:  
`git clone https://github.com/your-username/your-repo.git`  
`cd your-repo`

2. Установи зависимости:  
`pip install flask psycopg2-binary`

3. В `app.py` укажи настройки своей БД:  
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "ваш_пароль",
    "dbname": "sto_bot"
}
```
4. Запусти сервер:
py app.py
Зайди на http://127.0.0.1:5000

🤖 Запуск Telegram-бота
1. В bot_for_STO.py укажи токен и chat_id:
```
TOKEN = "ваш_токен"
ADMIN_CHAT_ID = ваш_chat_id
```
3. Запусти бота:
py bot_for_STO.py

🛡️ Доступ в админку
Логин: admin
Пароль: 1234
(можно поменять в app.py → USERS)
