import telebot
import requests
import uuid
import random
import time
import urllib3
from datetime import datetime
from collections import defaultdict

# ОТКЛЮЧАЕМ ПРЕДУПРЕЖДЕНИЯ О SSL (НЕ ВЛИЯЕТ НА БЕЗОПАСНОСТЬ)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== ВСТАВЬ СВОИ ДАННЫЕ =====
TELEGRAM_TOKEN = "8710199445:AAHQwkKePs1Lff8HjaDnnHolGrubNuQobl0"
CLIENT_ID = "019e1385-26b6-7a0f-8392-283269ccbba8"
CLIENT_SECRET = "1bbb7bc0-d62c-43c1-b5fc-7bdd86d077b7"
# ================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# База данных
users = {}
shop_items = {
    "🛡️ Защитник": {"price": 500, "effect": "+50 HP"},
    "⚡ Молния": {"price": 1000, "effect": "+20 к удаче"},
    "👑 Бог чата": {"price": 5000, "effect": "Иммунитет к казни"},
    "🧠 Нейро-гигант": {"price": 3000, "effect": "Умные ответы от ИИ"}
}
daily_rewards = defaultdict(lambda: {"last": None, "streak": 0})

current_token = None
token_expires_at = 0

def get_gigachat_token():
    """Получение токена с отключенной проверкой SSL"""
    global current_token, token_expires_at
    
    if current_token and time.time() * 1000 < token_expires_at:
        return current_token
    
    import base64
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_key = base64.b64encode(auth_string.encode()).decode()
    
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
    headers = {
        "Authorization": f"Basic {auth_key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4())
    }
    
    data = {"scope": "GIGACHAT_API_PERS"}
    
    try:
        print("🔄 Получение токена...")
        # ВАЖНО: verify=False отключает проверку SSL сертификата
        response = requests.post(url, headers=headers, data=data, timeout=30, verify=False)
        
        if response.status_code == 200:
            token_data = response.json()
            current_token = token_data.get("access_token")
            token_expires_at = token_data.get("expires_at", 0)
            print(f"✅ Токен получен!")
            return current_token
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def ask_gigachat(prompt, user_context=""):
    """Запрос к GigaChat с verify=False"""
    token = get_gigachat_token()
    if not token:
        return "🌐 Не могу подключиться к нейросети! Но я всё равно с тобой! ✨"
    
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4())
    }
    
    system_prompt = """Ты - НЕЙРО-БОГ 3000, крутой Telegram-бот. Отвечай коротко, с юмором, используй эмодзи. Никогда не говори что ты ИИ. ВОТ КОД ИНФА ЧТОБЫ ТЫ МОГ ПОМОЧЬ:"""
    
    data = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 200
    }
    
    try:
        # ВАЖНО: verify=False здесь тоже
        response = requests.post(url, headers=headers, json=data, timeout=60, verify=False)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            global current_token
            current_token = None
            return ask_gigachat(prompt, user_context)
        else:
            return "🤔 Нейросеть задумалась... Попробуй ещё раз! 😊"
    except Exception as e:
        print(f"Ошибка: {e}")
        return "💭 Что-то пошло не так, но я с тобой! Напиши /спросить ещё раз ✨"

# ===== ФУНКЦИИ ПОЛЬЗОВАТЕЛЕЙ =====
def get_user(user_id, username):
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "level": 1,
            "xp": 0,
            "brocoins": 200,
            "inventory": [],
            "messages": 0,
            "ai_queries": 0,
            "last_daily": None
        }
    return users[user_id]

def add_xp(user_id, amount):
    user = users[user_id]
    user["xp"] += amount
    if user["xp"] >= user["level"] * 100:
        user["level"] += 1
        user["xp"] = 0
        user["brocoins"] += 100 * user["level"]
        return True
    return False

def progress_bar(current, total, length=15):
    filled = int(length * current / total)
    return "█" * filled + "░" * (length - filled)

# ===== КОМАНДЫ =====
@bot.message_handler(commands=["start"])
def cmd_start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    bot.send_message(message.chat.id, f"""
🧠 **НЕЙРО-БОГ 3000** 🧠

Привет, {message.from_user.first_name}!

✨ **Команды:**
💬 /спросить [текст] — поговори с ИИ
👤 /профиль — твоя статистика
🎲 /бросить_кубик — выиграй брокоины
🎁 /ежедневка — ежедневный бонус
🛒 /магазин — купить роль
⚔️ /дуэль [@юзер] — битва
🔮 /предсказание — узнай будущее
🏆 /рейтинг — топ игроков

💰 Стартовый бонус: 200 брокоинов!
""")

@bot.message_handler(commands=["спросить"])
def cmd_ask(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    question = message.text.replace("/спросить", "").strip()
    
    if not question:
        bot.send_message(message.chat.id, "Что хочешь спросить? Например: /спросить Как стать имбой?")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    answer = ask_gigachat(question, f"Уровень {user['level']}")
    
    user["ai_queries"] += 1
    add_xp(message.from_user.id, 10)
    
    bot.send_message(message.chat.id, f"🧠 **ИИ:** {answer}\n\n✨ +10 XP")

@bot.message_handler(commands=["профиль"])
def cmd_profile(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    bar = progress_bar(user["xp"], user["level"] * 100)
    rank = ["🐣", "💪", "⚔️", "🛡️", "🏆", "👑", "🐉"][min(user["level"] // 3, 6)]
    
    bot.send_message(message.chat.id, f"""
📜 **ПРОФИЛЬ {user['username']}** {rank}

🎚️ Уровень: **{user['level']}**
💚 Опыт: {user['xp']}/{user['level']*100}
{bar}

💰 Брокоины: **{user['brocoins']}** 🪙
💬 Сообщений: {user['messages']}
🧠 Запросов к ИИ: {user['ai_queries']}
""")

@bot.message_handler(commands=["бросить_кубик"])
def cmd_dice(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    roll = random.randint(1, 100)
    
    if roll >= 95:
        reward = 100
        user["brocoins"] += reward
        result = f"🎉 **ДЖЕКПОТ!** +{reward} брокоинов!"
    elif roll <= 10:
        penalty = 50
        user["brocoins"] = max(0, user["brocoins"] - penalty)
        result = f"💀 **ПРОВАЛ!** -{penalty} брокоинов"
    else:
        result = f"🎲 Выпало {roll}"
    
    add_xp(message.from_user.id, 10)
    bot.send_message(message.chat.id, f"{result}\n🪙 Теперь: {user['brocoins']}")

@bot.message_handler(commands=["ежедневка"])
def cmd_daily(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    today = datetime.now().date()
    
    if user.get("last_daily") == today:
        bot.send_message(message.chat.id, "⏳ Уже получал сегодня!")
        return
    
    if user.get("last_daily") and (today - user["last_daily"]).days == 1:
        daily_rewards[message.from_user.id]["streak"] += 1
    else:
        daily_rewards[message.from_user.id]["streak"] = 1
    
    streak = daily_rewards[message.from_user.id]["streak"]
    bonus = 50 + (streak * 10)
    
    user["brocoins"] += bonus
    user["last_daily"] = today
    
    bot.send_message(message.chat.id, f"🎁 **+{bonus} брокоинов!**\n🔥 Стрик: {streak} дней")
    add_xp(message.from_user.id, 20)

@bot.message_handler(commands=["магазин"])
def cmd_shop(message):
    text = "🛒 **МАГАЗИН**\n\n"
    for item, data in shop_items.items():
        text += f"{item} — {data['price']} 🪙 | {data['effect']}\n"
    text += "\n/купить [название]"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["купить"])
def cmd_buy(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2 or parts[1] not in shop_items:
        bot.send_message(message.chat.id, "Что купить? /магазин")
        return
    
    item = parts[1]
    price = shop_items[item]["price"]
    
    if user["brocoins"] < price:
        bot.send_message(message.chat.id, f"💰 Не хватает! Нужно {price} 🪙")
        return
    
    user["brocoins"] -= price
    user["inventory"].append(item)
    bot.send_message(message.chat.id, f"✅ **Куплено {item}!**")

@bot.message_handler(commands=["дуэль"])
def cmd_duel(message):
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "⚔️ Ответь на сообщение противника!")
        return
    
    p1 = message.from_user.first_name
    p2 = message.reply_to_message.from_user.first_name
    
    if p1 == p2:
        bot.send_message(message.chat.id, "🤡 Нельзя с собой!")
        return
    
    power1 = random.randint(50, 150)
    power2 = random.randint(50, 150)
    winner = p1 if power1 > power2 else p2
    
    bot.send_message(message.chat.id, f"""
⚔️ **ДУЭЛЬ:** {p1} vs {p2}

{p1}: {'❤️' * (power1//15)} {power1} HP
{p2}: {'❤️' * (power2//15)} {power2} HP

🏆 **ПОБЕДИТЕЛЬ: {winner}!** 🏆
""")
    add_xp(message.from_user.id, 25)

@bot.message_handler(commands=["предсказание"])
def cmd_fortune(message):
    user = get_user(message.from_user.id, message.from_user.first_name)
    fortunes = [
        f"🔮 {user['username']}, завтра ты получишь {random.randint(50, 200)} брокоинов!",
        "🌟 Звёзды говорят: сегодня твой день!",
        "⚡ Нейросеть предсказывает успех в дуэлях!",
        "💀 Кто-то готовит тебе комплимент..."
    ]
    bonus = random.randint(10, 50)
    user["brocoins"] += bonus
    bot.send_message(message.chat.id, f"🔮 {random.choice(fortunes)}\n\n✨ +{bonus} брокоинов!")

@bot.message_handler(commands=["рейтинг"])
def cmd_rating(message):
    if not users:
        bot.send_message(message.chat.id, "Пока никого нет! Напиши /start")
        return
    
    top = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)[:5]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    text = "🏆 **ТОП ИГРОКОВ**\n\n"
    for i, (_, data) in enumerate(top):
        text += f"{medals[i]} {data['username']} — {data['level']} ур. ({data['brocoins']} 🪙)\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["монетка"])
def cmd_coin(message):
    result = random.choice(["🦅 ОРЁЛ", "🪙 РЕШКА"])
    bot.send_message(message.chat.id, f"🪙 Монетка падает...\n\n🎯 **{result}**")

@bot.message_handler(commands=["кубик"])
def cmd_dice6(message):
    roll = random.randint(1, 6)
    faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    bot.send_message(message.chat.id, f"🎲 Бросок...\n\n{faces[roll-1]} **{roll}**")

# ===== ОБЫЧНЫЕ СООБЩЕНИЯ =====
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.text.startswith('/'):
        return
    
    user = get_user(message.from_user.id, message.from_user.first_name)
    user["messages"] += 1
    add_xp(message.from_user.id, random.randint(1, 3))

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════╗
║   🧠 НЕЙРО-БОГ 3000 (GigaChat) 🧠       ║
║   Реальный ИИ + Экономика + Игры        ║
║   Готов к битве!                        ║
╚══════════════════════════════════════════╝
    """)
    
    # Проверяем подключение
    token = get_gigachat_token()
    if token:
        print("✅ GigaChat подключён!")
    else:
        print("⚠️ Ошибка подключения, но бот работает!")
    
    bot.infinity_polling()
