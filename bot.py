import os
import telebot
from telebot import types
import sqlite3
import random
import time
import threading
from features import wifi_scan, format_wifi_scan, analyze_national_id

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 8985043877
DEV_USERNAME = "@ELBABAELGRNERAL"
BOT_NAME = "ELGENERAL"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = threading.Lock()


APPEAL_TEMPLATES = {
    "t1": {"title": "📝 عام", "text": "السلام عليكم فريق دعم واتساب،\n\nأراسلكم بخصوص حظر حسابي. رقمي: [رقمك]\n\nأستخدم واتساب بشكل شخصي ولم أقصد مخالفة أي سياسة.\n\nأرجو إعادة النظر.\n\nمع التحية."},
    "t2": {"title": "📝 شخصي", "text": "فريق واتساب،\n\nرقمي: [رقمك]\n\nحسابي محظور، وأنا شخص عادي أستخدم التطبيق للتواصل مع العائلة والأصدقاء. لم أرتكب مخالفة متعمدة.\n\nأطلب مراجعة حسابي.\n\nشكراً."},
    "t3": {"title": "📝 عمل", "text": "السادة فريق واتساب،\n\nرقمي: [رقمك]\n\nأنا صاحب عمل صغير وأستخدم واتساب للتواصل مع عملائي. الحظر يؤثر على رزقي.\n\nأرجو إعادة تفعيل حسابي.\n\nشكراً."},
    "t4": {"title": "📝 حظر خاطئ", "text": "فريق واتساب،\n\nرقمي: [رقمك]\n\nحظر حسابي حدث بالخطأ أو ببلاغ كاذب. أنا مستخدم منتظم منذ سنوات.\n\nأرجو التحقق.\n\nشكراً."},
    "t5": {"title": "📝 رسمي", "text": "قسم مراجعة الحسابات،\n\nرقم الهاتف: [رقمك]\nتاريخ الحظر: [التاريخ]\n\nأرجو إعادة النظر في قرار حظر حسابي.\n\nشكراً."},
    "t6": {"title": "📝 جديد", "text": "فريق واتساب،\n\nرقمي: [رقمك]\n\nحسابي محظور بعد فترة قصيرة. ربما بسبب نشاط تلقائي.\n\nأرجو إعادة التفعيل.\n\nشكراً."},
    "t7": {"title": "📝 English", "text": "Dear WhatsApp Support,\n\nMy number: [your number]\n\nMy account has been banned. I use WhatsApp only for personal communication. I have not intentionally violated any policy.\n\nPlease review my account.\n\nThank you."},
    "t8": {"title": "📝 تاجر", "text": "فريق دعم واتساب،\n\nرقمي: [رقمك]\n\nأنا صاحب متجر وأستخدم واتساب للعمل. الحظر سبب خسائر كبيرة.\n\nأرجو إعادة التفعيل.\n\nشكراً."},
    "t9": {"title": "📝 طالب", "text": "فريق واتساب،\n\nرقمي: [رقمك]\n\nأنا طالب وأستخدم واتساب للدراسة. الحظر أثر على دراستي.\n\nأرجو المراجعة.\n\nشكراً."},
    "t10": {"title": "📝 مفصل", "text": "فريق واتساب المحترم،\n\nأتقدم باستئناف بخصوص حظر حسابي.\n\n📱 الرقم: [رقمك]\n📅 التاريخ: [التاريخ]\n\nأنا مستخدم واتساب منذ سنوات. لم أخالف أي سياسة.\n\n🙏 أرجو إعادة النظر.\n\nمع التحية."}
}


def get_db():
    conn = sqlite3.connect('bot.db', check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        points INTEGER DEFAULT 0, referred_by INTEGER, joined_at INTEGER,
        last_gift INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, identifier TEXT, name TEXT, url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS button_prices (
        button_key TEXT PRIMARY KEY, label TEXT, price INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()


init_db()


def get_setting(key, default=None):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone(); conn.close()
    return row[0] if row else default


def set_setting(key, value):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit(); conn.close()


def get_user(user_id):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT user_id, username, first_name, points, referred_by, joined_at, last_gift FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone(); conn.close()
    return row


def find_user(query):
    query = query.strip().replace('@', '')
    with db_lock:
        conn = get_db(); c = conn.cursor()
        if query.isdigit():
            c.execute("SELECT user_id, username, first_name, points FROM users WHERE user_id=?", (int(query),))
        else:
            c.execute("SELECT user_id, username, first_name, points FROM users WHERE LOWER(username)=LOWER(?)", (query,))
        row = c.fetchone(); conn.close()
    return row


def add_user(user_id, username, first_name, referred_by=None):
    if get_user(user_id): return False
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO users (user_id, username, first_name, points, referred_by, joined_at, last_gift) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, username or "", first_name or "", 0, referred_by, int(time.time()), 0))
        conn.commit(); conn.close()
    return True


def add_points(user_id, amount):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
        conn.commit(); conn.close()


def get_points(user_id):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone(); conn.close()
    return row[0] if row else 0


def get_all_users():
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]


def get_users_count():
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        n = c.fetchone()[0]; conn.close()
    return n


def get_top_users(limit=10):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT first_name, username, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
        rows = c.fetchall(); conn.close()
    return rows


def get_force_channels():
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT id, type, identifier, name, url FROM force_channels")
        rows = c.fetchall(); conn.close()
    return rows


def add_force_channel(ftype, identifier, name, url):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO force_channels (type, identifier, name, url) VALUES (?, ?, ?, ?)", (ftype, identifier, name, url))
        conn.commit(); conn.close()


def delete_force_channel(cid):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM force_channels WHERE id=?", (cid,))
        conn.commit(); conn.close()


def get_button_price(key):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT price FROM button_prices WHERE button_key=?", (key,))
        row = c.fetchone(); conn.close()
    return row[0] if row else 0


def set_button_price(key, label, price):
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO button_prices (button_key, label, price) VALUES (?, ?, ?)", (key, label, price))
        conn.commit(); conn.close()


def get_all_button_prices():
    with db_lock:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT button_key, label, price FROM button_prices")
        rows = c.fetchall(); conn.close()
    return rows


def is_bot_on():
    return get_setting('bot_on', '1') == '1'


def check_subscription(user_id):
    channels = get_force_channels()
    if not channels: return True, []
    not_subscribed = []
    for cid, ftype, identifier, name, url in channels:
        if ftype in ('link', 'bot'): continue
        try:
            member = bot.get_chat_member(identifier, user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append({'id': cid, 'type': ftype, 'name': name, 'url': url})
        except: continue
    return len(not_subscribed) == 0, not_subscribed


def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚡ تفعيل الاتصال", callback_data="activate"),
        types.InlineKeyboardButton("💣 جسر التلغيم", callback_data="bridge"),
    )
    markup.add(
        types.InlineKeyboardButton("📡 ماسح الواي فاي", callback_data="wifi_scan"),
        types.InlineKeyboardButton("🆔 محلل الرقم القومي", callback_data="nid_analyze"),
    )
    markup.add(
        types.InlineKeyboardButton("🚫 مساعد فك الحظر", callback_data="unban_help"),
        types.InlineKeyboardButton("📝 قوالب استئناف", callback_data="appeal_templates"),
    )
    markup.add(
        types.InlineKeyboardButton("🎁 هدية يومية", callback_data="daily_gift"),
        types.InlineKeyboardButton("🏆 المتصدرين", callback_data="leaderboard"),
    )
    markup.add(
        types.InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
        types.InlineKeyboardButton("🔗 رابط دعوتي", callback_data="my_link"),
    )
    markup.add(
        types.InlineKeyboardButton("🎰 عجلة الحظ", callback_data="paid_lucky"),
        types.InlineKeyboardButton("🎲 لعبة النرد", callback_data="paid_dice"),
    )
    markup.add(
        types.InlineKeyboardButton("💎 صندوق الغموض", callback_data="paid_box"),
        types.InlineKeyboardButton("🎯 مضاعفة النقاط", callback_data="paid_double"),
    )
    markup.add(
        types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_USERNAME.replace('@','')}"),
        types.InlineKeyboardButton("ℹ️ معلومات", callback_data="info"),
    )
    if user_id == OWNER_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel"))
    return markup


def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return markup


def admin_menu():
    bot_status = "🟢 شغال" if is_bot_on() else "🔴 متوقف"
    channels_count = len(get_force_channels())
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("💰 إضافة نقاط", callback_data="admin_add_points"),
        types.InlineKeyboardButton("➖ خصم نقاط", callback_data="admin_remove_points"),
    )
    markup.add(
        types.InlineKeyboardButton(f"📢 الاشتراك ({channels_count})", callback_data="admin_force"),
        types.InlineKeyboardButton("💰 سعر الإحالة", callback_data="admin_ref_price"),
    )
    markup.add(
        types.InlineKeyboardButton("🎛️ أسعار الأزرار", callback_data="admin_btn_prices"),
    )
    markup.add(
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users"),
        types.InlineKeyboardButton(f"⏻ {bot_status}", callback_data="admin_toggle"),
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return markup


def force_admin_menu():
    channels = get_force_channels()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ إضافة اشتراك جديد", callback_data="force_add"))
    if channels:
        for cid, ftype, identifier, name, url in channels:
            emoji = {"channel": "📢", "group": "👥", "bot": "🤖", "link": "🔗"}.get(ftype, "📌")
            markup.add(types.InlineKeyboardButton(f"{emoji} {name} | 🗑", callback_data=f"force_del_{cid}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    return markup


def force_type_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 قناة", callback_data="force_type_channel"),
        types.InlineKeyboardButton("👥 جروب", callback_data="force_type_group"),
    )
    markup.add(
        types.InlineKeyboardButton("🤖 بوت", callback_data="force_type_bot"),
        types.InlineKeyboardButton("🔗 لينك", callback_data="force_type_link"),
    )
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_force"))
    return markup


def subscribe_menu(not_subscribed):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for item in not_subscribed:
        emoji = {"channel": "📢", "group": "👥", "bot": "🤖", "link": "🔗"}.get(item['type'], "📌")
        markup.add(types.InlineKeyboardButton(f"{emoji} {item['name']}", url=item['url']))
    markup.add(types.InlineKeyboardButton("✅ تحقّق", callback_data="check_sub"))
    return markup


def prices_admin_menu():
    btns = get_all_button_prices()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ ضبط سعر زر", callback_data="btn_price_add"))
    if btns:
        for key, label, price in btns:
            markup.add(types.InlineKeyboardButton(f"{label} = {price} نقطة | 🗑", callback_data=f"btn_price_del_{key}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    return markup


def points_confirm_menu(user_id, amount, action):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد", callback_data=f"points_confirm_{user_id}_{amount}_{action}"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel"),
    )
    return markup


def send_welcome(user_id, first_name=None):
    points = get_points(user_id)
    name_part = f"أهلاً {first_name}!" if first_name else "أهلاً!"
    text = (
        f"🔥 <b>{BOT_NAME}</b> 🔥\n"
        "📡 <b>نظام الجسر الأبدي — WABridge Pro</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 {name_part}\n"
        f"💰 رصيدك: <b>{points} نقطة</b>\n\n"
        "اختر من القائمة 👇"
    )
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=main_menu(user_id))


def check_and_charge(user_id, button_key):
    price = get_button_price(button_key)
    if price <= 0: return True
    points = get_points(user_id)
    if points < price: return False
    add_points(user_id, -price)
    return True


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    is_owner = user_id == OWNER_ID

    if data == "back_main":
        bot.answer_callback_query(call.id)
        send_welcome(chat_id)
        return

    if data == "check_sub":
        bot.answer_callback_query(call.id)
        ok, not_subscribed = check_subscription(user_id)
        if ok:
            bot.send_message(chat_id, "✅ <b>تم التحقق!</b>", parse_mode='HTML')
            send_welcome(chat_id)
        else:
            bot.send_message(chat_id, "❌ <b>لسه مشتركتش!</b>", parse_mode='HTML', reply_markup=subscribe_menu(not_subscribed))
        return

    if data.startswith("points_confirm_"):
        bot.answer_callback_query(call.id)
        parts = data.replace("points_confirm_", "").split("_")
        target_id = int(parts[0])
        amount = int(parts[1])
        action = parts[2]
        if action == "add":
            add_points(target_id, amount)
            bot.edit_message_text(f"✅ <b>تمت الإضافة!</b>\n\n💰 +{amount} نقطة لـ <code>{target_id}</code>\n⭐ رصيده الآن: <b>{get_points(target_id)}</b>",
                                  chat_id, call.message.message_id, parse_mode='HTML', reply_markup=admin_menu())
            try:
                bot.send_message(target_id, f"🎉 <b>مبروك!</b>\n\n💰 تم إضافة <b>{amount} نقطة</b>\n⭐ رصيدك: <b>{get_points(target_id)}</b>", parse_mode='HTML')
            except: pass
        else:
            add_points(target_id, -amount)
            bot.edit_message_text(f"✅ <b>تمت الخصم!</b>\n\n💸 -{amount} نقطة من <code>{target_id}</code>\n⭐ رصيده الآن: <b>{get_points(target_id)}</b>",
                                  chat_id, call.message.message_id, parse_mode='HTML', reply_markup=admin_menu())
            try:
                bot.send_message(target_id, f"⚠️ <b>تم خصم نقاط</b>\n\n💸 -{amount} نقطة\n⭐ رصيدك: <b>{get_points(target_id)}</b>", parse_mode='HTML')
            except: pass
        return

    if data == "daily_gift":
        bot.answer_callback_query(call.id)
        with db_lock:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT last_gift FROM users WHERE user_id=?", (user_id,))
            row = c.fetchone(); conn.close()
        last_gift = row[0] if row else 0
        now = int(time.time())
        if now - last_gift < 86400:
            remaining = 86400 - (now - last_gift)
            hours = remaining // 3600
            mins = (remaining % 3600) // 60
            bot.send_message(chat_id, f"⏰ <b>استلمت الهدية!</b>\n\n🕐 فاضل: <b>{hours} ساعة و {mins} دقيقة</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        add_points(user_id, 5)
        with db_lock:
            conn = get_db(); c = conn.cursor()
            c.execute("UPDATE users SET last_gift=? WHERE user_id=?", (now, user_id))
            conn.commit(); conn.close()
        bot.send_message(chat_id, "🎁 <b>مبروك!</b>\n\n💰 +5 نقاط\n\nارجع بكرة ✅", parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "leaderboard":
        bot.answer_callback_query(call.id)
        top = get_top_users(10)
        text = "🏆 <b>لوحة المتصدرين</b>\n━━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, username, pts) in enumerate(top, 1):
            m = medals[i-1] if i <= 3 else f"{i}."
            display = name or (f"@{username}" if username else "مستخدم")
            text += f"{m} <b>{display}</b> — {pts} نقطة\n"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "my_stats":
        bot.answer_callback_query(call.id)
        points = get_points(user_id)
        with db_lock:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
            ref_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE points > ?", (points,))
            rank = c.fetchone()[0] + 1
            conn.close()
        text = (f"📊 <b>إحصائياتي</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"⭐ النقاط: <b>{points}</b>\n"
                f"👥 الإحالات: <b>{ref_count}</b>\n"
                f"🏆 ترتيبك: <b>#{rank}</b>")
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "my_link":
        bot.answer_callback_query(call.id)
        ref_points = get_setting('referral_points', '10')
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
        text = f"🔗 <b>رابط الدعوة</b>\n━━━━━━━━━━━━━━━━━━\n<code>{link}</code>\n\n💰 كل واحد = <b>+{ref_points} نقطة</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 مشاركة", url=f"https://t.me/share/url?url={link}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
        return

    if data == "info":
        bot.answer_callback_query(call.id)
        text = f"ℹ️ <b>معلومات</b>\n━━━━━━━━━━━━━━━━━━\n🔥 <b>{BOT_NAME}</b>\n👨‍💻 {DEV_USERNAME}"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "paid_lucky":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "paid_lucky"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        prize = random.choice([1, 2, 3, 5, 10, 20, 50, 100])
        add_points(user_id, prize)
        bot.send_message(chat_id, f"🎰 <b>عجلة الحظ!</b>\n\n🎁 ربحت: <b>{prize} نقطة</b>\n💰 رصيدك: <b>{get_points(user_id)}</b>", parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "paid_dice":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "paid_dice"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        my_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        if my_roll > bot_roll:
            add_points(user_id, 30)
            result = "🎉 <b>كسبت!</b> +30 نقطة"
        elif my_roll == bot_roll:
            result = "🤝 <b>تعادل!</b>"
        else:
            result = "😢 <b>خسرت!</b>"
        bot.send_message(chat_id, f"🎲 <b>لعبة النرد</b>\n\nأنت: <b>{my_roll}</b>\nالبوت: <b>{bot_roll}</b>\n\n{result}\n💰 رصيدك: <b>{get_points(user_id)}</b>", parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "paid_box":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "paid_box"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        prize = random.choice([0, 10, 20, 30, 50, 100, 200])
        add_points(user_id, prize)
        bot.send_message(chat_id, f"💎 <b>صندوق الغموض</b>\n\n🎁 جوّه: <b>{prize} نقطة</b>\n💰 رصيدك: <b>{get_points(user_id)}</b>", parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "paid_double":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "paid_double"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        current = get_points(user_id)
        if random.random() < 0.5:
            add_points(user_id, current)
            bot.send_message(chat_id, f"🎯 <b>مبروك!</b>\n\n💰 اتضاعفت نقاطك!\n⭐ رصيدك: <b>{get_points(user_id)}</b>", parse_mode='HTML', reply_markup=back_menu())
        else:
            bot.send_message(chat_id, f"😢 <b>خسرت</b>\n\n💰 رصيدك: <b>{current}</b>", parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "wifi_scan":
        bot.answer_callback_query(call.id)
        wait_msg = bot.send_message(chat_id, "📡 <b>جاري المسح...</b>", parse_mode='HTML')
        time.sleep(2)
        text = format_wifi_scan(wifi_scan())
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 مسح تاني", callback_data="wifi_scan"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.edit_message_text(text, chat_id, wait_msg.message_id, parse_mode='HTML', reply_markup=markup)
        return

    if data == "nid_analyze":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🆔 ابعت الرقم القومي (14 رقم):", parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_nid)
        return

    if data == "unban_help":
        bot.answer_callback_query(call.id)
        text = ("🚫 <b>مساعد فك حظر واتساب</b>\n━━━━━━━━━━━━━━━━━━\n\n"
                "📌 <b>الخطوات:</b>\n1️⃣ افتح واتساب\n2️⃣ الإعدادات ⚙️\n3️⃣ Help\n4️⃣ Contact Us\n5️⃣ اكتب استئناف\n\n"
                "🔗 https://faq.whatsapp.com\n\n"
                "⚠️ <b>تحذير:</b> مفيش حد يفك الحظر غير واتساب.\n❌ أي حد يطلب إيميلك = نصب.")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 الموقع الرسمي", url="https://faq.whatsapp.com"))
        markup.add(types.InlineKeyboardButton("📝 قوالب استئناف", callback_data="appeal_templates"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        return

    if data == "appeal_templates":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, tpl in APPEAL_TEMPLATES.items():
            markup.add(types.InlineKeyboardButton(tpl["title"], callback_data=f"show_{key}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, "📝 <b>قوالب استئناف جاهزة</b>\n\nاختار:", parse_mode='HTML', reply_markup=markup)
        return

    if data.startswith("show_") and data.replace("show_", "") in APPEAL_TEMPLATES:
        bot.answer_callback_query(call.id)
        key = data.replace("show_", "")
        tpl = APPEAL_TEMPLATES[key]
        text = (f"<b>{tpl['title']}</b>\n━━━━━━━━━━━━━━━━━━\n\n<blockquote>{tpl['text']}</blockquote>\n\n"
                "📌 انسخها بالضغط المطول، وغير [رقمك].")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 نموذج واتساب", url="https://www.whatsapp.com/contact/"))
        markup.add(types.InlineKeyboardButton("📋 قوالب تانية", callback_data="appeal_templates"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        return

    if data == "activate":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "activate"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        msg = bot.send_message(chat_id, "📱 أدخل رقم الواتساب:", parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_number)
        return

    if data == "bridge":
        bot.answer_callback_query(call.id)
        if not check_and_charge(user_id, "bridge"):
            bot.send_message(chat_id, "❌ <b>نقاطك مش كفاية!</b>", parse_mode='HTML', reply_markup=back_menu())
            return
        msg = bot.send_message(chat_id, "🛡 أدخل الباند:", parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_band)
        return

    if not is_owner:
        bot.answer_callback_query(call.id, "❌ مش مسموحلك")
        return

    if data == "admin_panel":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "👑 <b>لوحة التحكم</b>", parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_stats":
        bot.answer_callback_query(call.id)
        total = get_users_count()
        bot.send_message(chat_id, f"📊 <b>إحصائيات</b>\n\n👥 المستخدمين: <b>{total}</b>", parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_toggle":
        bot.answer_callback_query(call.id)
        current = is_bot_on()
        set_setting('bot_on', '0' if current else '1')
        status = "متوقف 🔴" if current else "شغال 🟢"
        bot.send_message(chat_id, f"✅ <b>{status}</b>", parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📢 اكتب الرسالة:")
        bot.register_next_step_handler(msg, process_broadcast)
        return

    if data == "admin_add_points":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id,
            "💰 <b>إضافة نقاط</b>\n\nابعت <b>ID</b> أو <b>@username</b>:",
            parse_mode='HTML',
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")))
        bot.register_next_step_handler(msg, process_add_points_step1)
        return

    if data == "admin_remove_points":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id,
            "➖ <b>خصم نقاط</b>\n\nابعت <b>ID</b> أو <b>@username</b>:",
            parse_mode='HTML',
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")))
        bot.register_next_step_handler(msg, process_remove_points_step1)
        return

    if data == "admin_users":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"👥 <b>{get_users_count()} مستخدم</b>", parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_ref_price":
        bot.answer_callback_query(call.id)
        current = get_setting('referral_points', '10')
        msg = bot.send_message(chat_id, f"💰 <b>سعر الإحالة:</b> {current} نقطة\n\nاكتب الجديد:", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_ref_price)
        return

    if data == "admin_btn_prices":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🎛️ <b>أسعار الأزرار</b>", parse_mode='HTML', reply_markup=prices_admin_menu())
        return

    if data == "btn_price_add":
        bot.answer_callback_query(call.id)
        text = ("🎛️ اكتب: <code>button_key | label | price</code>\n\n"
                "<b>الأزرار:</b>\n"
                "activate, bridge, wifi_scan, nid_analyze, unban_help, appeal_templates\n"
                "paid_lucky, paid_dice, paid_box, paid_double\n\n"
                "مثال: <code>paid_lucky | 🎰 عجلة الحظ | 5</code>")
        msg = bot.send_message(chat_id, text, parse_mode='HTML')
        bot.register_next_step_handler(msg, process_btn_price)
        return

    if data.startswith("btn_price_del_"):
        bot.answer_callback_query(call.id)
        key = data.replace("btn_price_del_", "")
        with db_lock:
            conn = get_db(); c = conn.cursor()
            c.execute("DELETE FROM button_prices WHERE button_key=?", (key,))
            conn.commit(); conn.close()
        bot.send_message(chat_id, "✅ <b>تم الحذف</b>", parse_mode='HTML', reply_markup=prices_admin_menu())
        return

    if data == "admin_force":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📢 <b>الاشتراك الإجباري</b>", parse_mode='HTML', reply_markup=force_admin_menu())
        return

    if data == "force_add":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📌 اختار النوع:", parse_mode='HTML', reply_markup=force_type_menu())
        return

    if data.startswith("force_del_"):
        bot.answer_callback_query(call.id)
        cid = int(data.replace("force_del_", ""))
        delete_force_channel(cid)
        bot.send_message(chat_id, "✅ <b>تم الحذف</b>", parse_mode='HTML', reply_markup=force_admin_menu())
        return

    if data in ("force_type_channel", "force_type_group", "force_type_bot", "force_type_link"):
        bot.answer_callback_query(call.id)
        ftype = data.replace("force_type_", "")
        texts = {
            "channel": "📢 ابعت @username أو Forward لأي رسالة.",
            "group": "👥 ابعت @username أو Forward لأي رسالة.",
            "bot": "🤖 ابعت رابط البوت.",
            "link": "🔗 ابعت اللينك.",
        }
        msg = bot.send_message(chat_id, texts[ftype], parse_mode='HTML',
                               reply_markup=types.InlineKeyboardMarkup().add(
                                   types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_force")))
        bot.register_next_step_handler(msg, process_add_force, ftype)
        return


def process_add_points_step1(message):
    if message.from_user.id != OWNER_ID: return
    if not message.text: return
    user_data = find_user(message.text.strip())
    if not user_data:
        bot.send_message(message.chat.id, f"❌ مش لاقي: <code>{message.text}</code>", parse_mode='HTML', reply_markup=admin_menu())
        return
    target_id, uname, fname, points = user_data
    display = fname or (f"@{uname}" if uname else str(target_id))
    msg = bot.send_message(message.chat.id,
        f"👤 {display}\n🆔 <code>{target_id}</code>\n⭐ رصيده: <b>{points}</b>\n\n💰 اكتب عدد النقاط:",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")))
    bot.register_next_step_handler(msg, lambda m: process_add_points_step2(m, target_id, display))


def process_add_points_step2(message, target_id, display):
    if message.from_user.id != OWNER_ID: return
    try:
        amount = int(message.text.strip())
        if amount <= 0: raise ValueError()
        bot.send_message(message.chat.id,
            f"💰 <b>تأكيد</b>\n\n👤 {display}\n➕ {amount} نقطة\n⭐ بعد: <b>{get_points(target_id) + amount}</b>",
            parse_mode='HTML',
            reply_markup=points_confirm_menu(target_id, amount, "add"))
    except:
        bot.send_message(message.chat.id, "❌ رقم غير صالح", reply_markup=admin_menu())


def process_remove_points_step1(message):
    if message.from_user.id != OWNER_ID: return
    if not message.text: return
    user_data = find_user(message.text.strip())
    if not user_data:
        bot.send_message(message.chat.id, f"❌ مش لاقي: <code>{message.text}</code>", parse_mode='HTML', reply_markup=admin_menu())
        return
    target_id, uname, fname, points = user_data
    display = fname or (f"@{uname}" if uname else str(target_id))
    msg = bot.send_message(message.chat.id,
        f"👤 {display}\n🆔 <code>{target_id}</code>\n⭐ رصيده: <b>{points}</b>\n\n➖ اكتب عدد النقاط:",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")))
    bot.register_next_step_handler(msg, lambda m: process_remove_points_step2(m, target_id, display, points))


def process_remove_points_step2(message, target_id, display, current_points):
    if message.from_user.id != OWNER_ID: return
    try:
        amount = int(message.text.strip())
        if amount <= 0: raise ValueError()
        if amount > current_points: amount = current_points
        bot.send_message(message.chat.id,
            f"➖ <b>تأكيد الخصم</b>\n\n👤 {display}\n➖ {amount} نقطة\n⭐ بعد: <b>{current_points - amount}</b>",
            parse_mode='HTML',
            reply_markup=points_confirm_menu(target_id, amount, "remove"))
    except:
        bot.send_message(message.chat.id, "❌ رقم غير صالح", reply_markup=admin_menu())


def process_ref_price(message):
    if message.from_user.id != OWNER_ID: return
    try:
        num = int(message.text.strip())
        set_setting('referral_points', num)
        bot.send_message(message.chat.id, f"✅ سعر الإحالة: {num} نقطة", parse_mode='HTML', reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ رقم غير صالح", reply_markup=admin_menu())


def process_btn_price(message):
    if message.from_user.id != OWNER_ID: return
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3: raise Exception()
        key, label, price = parts
        set_button_price(key, label, int(price))
        bot.send_message(message.chat.id, f"✅ {label} = {price} نقطة", parse_mode='HTML', reply_markup=prices_admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ صيغة غلط", reply_markup=prices_admin_menu())


def process_add_force(message, ftype):
    if message.from_user.id != OWNER_ID: return
    if ftype in ('channel', 'group'):
        chat_id_to_use = chat_name = chat_url = None
        if message.forward_from_chat:
            chat = message.forward_from_chat
            chat_id_to_use = chat.id
            chat_name = chat.title or "بدون اسم"
            chat_url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        elif message.text:
            text = message.text.strip()
            if not (text.startswith('@') or text.startswith('-100')):
                bot.send_message(message.chat.id, "❌ صيغة غلط", reply_markup=force_admin_menu()); return
            try:
                chat = bot.get_chat(text)
                chat_id_to_use = chat.id
                chat_name = chat.title or text
                chat_url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id).replace('-100', '')}"
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}", reply_markup=force_admin_menu()); return
        else: return
        try:
            bm = bot.get_chat_member(chat_id_to_use, bot.get_me().id)
            if bm.status not in ['administrator', 'creator']:
                bot.send_message(message.chat.id, "⚠️ البوت مش أدمن!", reply_markup=force_admin_menu()); return
        except: pass
        add_force_channel(ftype, str(chat_id_to_use), chat_name, chat_url)
        bot.send_message(message.chat.id, f"✅ <b>تم!</b>\n\n{chat_name}", parse_mode='HTML', reply_markup=force_admin_menu())
        return
    elif ftype == 'bot':
        url = message.text.strip()
        if not url.startswith('http'): url = f"https://t.me/{url.replace('@', '')}"
        ident = url.replace("https://t.me/", "").replace("@", "")
        add_force_channel('bot', ident, f"@{ident}", url)
        bot.send_message(message.chat.id, f"✅ {url}", parse_mode='HTML', reply_markup=force_admin_menu())
    else:
        url = message.text.strip()
        if not url.startswith('http'): bot.send_message(message.chat.id, "❌ لازم http", reply_markup=force_admin_menu()); return
        add_force_channel('link', url, url[:30], url)
        bot.send_message(message.chat.id, f"✅ {url}", parse_mode='HTML', reply_markup=force_admin_menu())


def process_number(message):
    if not message.text or message.text.startswith('/'): return
    chat_id = message.chat.id
    number = message.text.strip()
    msg = bot.send_message(chat_id, "⏳ <b>جاري التنفيذ...</b>", parse_mode='HTML')
    time.sleep(1)
    fake = random.choice(['+20', '+966', '+971']) + ''.join(str(random.randint(0, 9)) for _ in range(9))
    code = f"YADASH-{int(time.time()):X}"
    bot.edit_message_text(f"✅ <b>تم</b>\n📱 {number}\n🔗 {fake}\n🔑 <code>{code}</code>", chat_id, msg.message_id, parse_mode='HTML')
    bot.send_message(chat_id, "اختر من القائمة 👇", reply_markup=main_menu(chat_id))


def process_band(message):
    if not message.text or message.text.startswith('/'): return
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ <b>جاري التلغيم...</b>", parse_mode='HTML')
    time.sleep(1)
    wid = "WP-" + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    bot.edit_message_text(f"💣 <b>تم</b>\n🎯 {message.text.strip()}\n💣 <code>{wid}</code>", chat_id, msg.message_id, parse_mode='HTML')
    bot.send_message(chat_id, "اختر من القائمة 👇", reply_markup=main_menu(chat_id))


def process_nid(message):
    if not message.text or message.text.startswith('/'): return
    chat_id = message.chat.id
    text = message.text.strip()
    full_name, id_num = "", text
    if '|' in text:
        parts = [p.strip() for p in text.split('|', 1)]
        full_name, id_num = parts[0], parts[1]
    result = analyze_national_id(id_num.strip(), full_name)
    bot.send_message(chat_id, result, parse_mode='HTML', reply_markup=main_menu(chat_id))


def process_broadcast(message):
    if message.from_user.id != OWNER_ID: return
    users = get_all_users()
    sent = 0
    bot.send_message(message.chat.id, f"⏳ الإرسال لـ {len(users)}...")
    for uid in users:
        try:
            bot.send_message(uid, message.text); sent += 1; time.sleep(0.05)
        except: pass
    bot.send_message(message.chat.id, f"✅ نجح: {sent}", reply_markup=admin_menu())


@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    referred_by = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref'):
        try:
            ref_id = int(args[1].replace('ref', ''))
            if ref_id != user_id: referred_by = ref_id
        except: pass
    is_new = add_user(user_id, username, first_name, referred_by)
    if is_new and referred_by and get_user(referred_by):
        ref_points = int(get_setting('referral_points', '10'))
        add_points(referred_by, ref_points)
        try:
            bot.send_message(referred_by, f"🎉 <b>مبروك!</b>\n👤 واحد جديد دخل من رابطك\n💰 +{ref_points} نقطة", parse_mode='HTML')
        except: pass
    ok, not_subscribed = check_subscription(user_id)
    if not ok:
        bot.send_message(user_id, "⚠️ <b>لازم تشترك في القنوات دي:</b>", parse_mode='HTML', reply_markup=subscribe_menu(not_subscribed))
        return
    if not is_bot_on() and user_id != OWNER_ID:
        bot.send_message(user_id, "🔴 <b>البوت متوقف</b>", parse_mode='HTML'); return
    send_welcome(user_id, first_name)


@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != OWNER_ID: return
    bot.send_message(message.chat.id, "👑", reply_markup=admin_menu())


@bot.message_handler(commands=['myid'])
def my_id_cmd(message):
    bot.reply_to(message, f"🆔 <code>{message.from_user.id}</code>", parse_mode='HTML')


if __name__ == "__main__":
    print(f"🔥 {BOT_NAME} — البوت شغّال...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)
