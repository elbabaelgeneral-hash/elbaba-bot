import os
import telebot
from telebot import types
import sqlite3
import random
import time
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 8772508181
DEV_USERNAME = "@ELBABAELGRNERAL"
BOT_NAME = "ELGENERAL"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = threading.Lock()


def get_db():
    conn = sqlite3.connect('bot.db', check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        points INTEGER DEFAULT 0,
        referred_by INTEGER,
        joined_at INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT,
        channel_name TEXT,
        channel_url TEXT
    )''')
    conn.commit()
    conn.close()


init_db()


def get_setting(key, default=None):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        conn.close()
    return row[0] if row else default


def set_setting(key, value):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()


def get_user(user_id):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id, username, first_name, points, referred_by, joined_at FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
    return row


def add_user(user_id, username, first_name, referred_by=None):
    if get_user(user_id):
        return False
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (user_id, username, first_name, points, referred_by, joined_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username or "", first_name or "", 0, referred_by, int(time.time()))
        )
        conn.commit()
        conn.close()
    return True


def add_points(user_id, amount):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        conn.close()


def get_points(user_id):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
    return row[0] if row else 0


def get_all_users():
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        rows = c.fetchall()
        conn.close()
    return [r[0] for r in rows]


def get_users_count():
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        n = c.fetchone()[0]
        conn.close()
    return n


def get_force_channels():
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, channel_id, channel_name, channel_url FROM force_channels")
        rows = c.fetchall()
        conn.close()
    return rows


def check_subscription(user_id):
    channels = get_force_channels()
    if not channels:
        return True, []
    not_joined = []
    for cid, ch_id, ch_name, ch_url in channels:
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append((ch_name, ch_url))
        except:
            continue
    return len(not_joined) == 0, not_joined


def is_bot_on():
    return get_setting('bot_on', '1') == '1'


def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚡ تفعيل الاتصال الأبدي", callback_data="activate"),
        types.InlineKeyboardButton("💣 بناء جسر التلغيم", callback_data="bridge"),
    )
    markup.add(
        types.InlineKeyboardButton("🔗 رابط دعوتي", callback_data="my_link"),
        types.InlineKeyboardButton("💰 نقاطي", callback_data="my_points"),
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
    markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back_main"))
    return markup


def admin_menu():
    bot_status = "🟢 شغال" if is_bot_on() else "🔴 متوقف"
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
        types.InlineKeyboardButton("📢 إدارة الاشتراك الإجباري", callback_data="admin_force"),
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users"),
    )
    markup.add(types.InlineKeyboardButton(f"⏻ {bot_status}", callback_data="admin_toggle"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return markup


def sub_check_menu(not_joined):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name, url in not_joined:
        markup.add(types.InlineKeyboardButton(f"📢 {name}", url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقّق", callback_data="check_sub"))
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
            if ref_id != user_id:
                referred_by = ref_id
        except:
            pass

    is_new = add_user(user_id, username, first_name, referred_by)

    if is_new and referred_by and get_user(referred_by):
        add_points(referred_by, 10)
        try:
            bot.send_message(referred_by,
                "🎉 <b>مبروك!</b>\n👤 واحد جديد دخل من رابطك\n💰 +10 نقاط",
                parse_mode='HTML')
        except:
            pass

    ok, not_joined = check_subscription(user_id)
    if not ok:
        bot.send_message(user_id,
            "⚠️ <b>لازم تشترك في القنوات دي الأول:</b>",
            parse_mode='HTML',
            reply_markup=sub_check_menu(not_joined))
        return

    if not is_bot_on() and user_id != OWNER_ID:
        bot.send_message(user_id, "🔴 <b>البوت متوقف مؤقتاً</b>", parse_mode='HTML')
        return

    send_welcome(user_id, first_name)


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
        ok, not_joined = check_subscription(user_id)
        if ok:
            bot.send_message(chat_id, "✅ تم التحقق! أهلاً بيك.", parse_mode='HTML')
            send_welcome(chat_id)
        else:
            bot.send_message(chat_id, "❌ لسه مشتركتش في كل القنوات!",
                             parse_mode='HTML', reply_markup=sub_check_menu(not_joined))
        return

    if data == "my_link":
        bot.answer_callback_query(call.id)
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
        text = (
            "🔗 <b>رابط الدعوة الخاص بك</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<code>{link}</code>\n\n"
            "💰 كل واحد يدخل من الرابط ده = <b>+10 نقاط</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 مشاركة", url=f"https://t.me/share/url?url={link}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
        return

    if data == "my_points":
        bot.answer_callback_query(call.id)
        points = get_points(user_id)
        text = (
            "💰 <b>نقاطك</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"⭐ الرصيد: <b>{points}</b>"
        )
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "info":
        bot.answer_callback_query(call.id)
        text = (
            f"ℹ️ <b>معلومات النظام</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🔥 <b>{BOT_NAME}</b>\n"
            f"👨‍💻 المطور: {DEV_USERNAME}"
        )
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "activate":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id,
            "📱 <b>أدخل رقم الواتساب</b>",
            parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_number)
        return

    if data == "bridge":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id,
            "🛡 <b>أدخل الباند المرفوض</b>",
            parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_band)
        return

    if not is_owner:
        bot.answer_callback_query(call.id, "❌ مش مسموحلك")
        return

    if data == "admin_panel":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"👑 <b>لوحة التحكم</b>",
                         parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_stats":
        bot.answer_callback_query(call.id)
        total = get_users_count()
        day_ago = int(time.time()) - 86400
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE joined_at > ?", (day_ago,))
            today = c.fetchone()[0]
            conn.close()
        text = (
            "📊 <b>إحصائيات</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👥 الإجمالي: <b>{total}</b>\n"
            f"🆕 اليوم: <b>{today}</b>"
        )
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_toggle":
        bot.answer_callback_query(call.id)
        current = is_bot_on()
        set_setting('bot_on', '0' if current else '1')
        status = "متوقف 🔴" if current else "شغال 🟢"
        bot.send_message(chat_id, f"✅ الحالة: <b>{status}</b>",
                         parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📢 اكتب الرسالة:")
        bot.register_next_step_handler(msg, process_broadcast)
        return

    if data == "admin_add_points":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "💰 اكتب: <code>USER_ID AMOUNT</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_add_points)
        return

    if data == "admin_remove_points":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "➖ اكتب: <code>USER_ID AMOUNT</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_remove_points)
        return

    if data == "admin_users":
        bot.answer_callback_query(call.id)
        total = get_users_count()
        text = f"👥 <b>عدد المستخدمين: {total}</b>"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_force":
        bot.answer_callback_query(call.id)
        channels = get_force_channels()
        text = "📢 <b>الاشتراك الإجباري</b>\n\n"
        for cid, ch_id, name, url in channels:
            text += f"#{cid} — {name}\n"
        text += "\n/add_channel لإضافة قناة\n/del_channel ID لحذف قناة"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=admin_menu())
        return


def process_number(message):
    if message.text and message.text.startswith('/'):
        return
    chat_id = message.chat.id
    number = message.text.strip()
    msg = bot.send_message(chat_id, "⏳ <b>جاري التنفيذ...</b>", parse_mode='HTML')
    time.sleep(1)
    prefixes = ['+20', '+966', '+971', '+974', '+973']
    fake = random.choice(prefixes) + ''.join(str(random.randint(0, 9)) for _ in range(9))
    code = f"YADASH-{int(time.time()):X}"
    text = (
        "✅ <b>تم التفعيل</b>\n"
        f"📱 الرقم: <code>{number}</code>\n"
        f"🔗 الجسر: <code>{fake}</code>\n"
        f"🔑 الكود: <code>{code}</code>"
    )
    bot.edit_message_text(text, chat_id, msg.message_id, parse_mode='HTML')
    bot.send_message(chat_id, "اختر من القائمة 👇", reply_markup=main_menu(chat_id))


def process_band(message):
    if message.text and message.text.startswith('/'):
        return
    chat_id = message.chat.id
    band = message.text.strip()
    msg = bot.send_message(chat_id, "⏳ <b>جاري التلغيم...</b>", parse_mode='HTML')
    time.sleep(1)
    weapon_id = "WP-" + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    text = (
        "💣 <b>تم التلغيم</b>\n"
        f"🎯 الباند: <code>{band}</code>\n"
        f"💣 السلاح: <code>{weapon_id}</code>"
    )
    bot.edit_message_text(text, chat_id, msg.message_id, parse_mode='HTML')
    bot.send_message(chat_id, "اختر من القائمة 👇", reply_markup=main_menu(chat_id))


def process_broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    users = get_all_users()
    success = 0
    bot.send_message(message.chat.id, f"⏳ الإرسال لـ {len(users)}...")
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ نجح: {success}", reply_markup=admin_menu())


def process_add_points(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.split()
        uid = int(parts[0])
        amt = int(parts[1])
        add_points(uid, amt)
        bot.send_message(message.chat.id, f"✅ تم", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ خطأ", reply_markup=admin_menu())


def process_remove_points(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.split()
        uid = int(parts[0])
        amt = int(parts[1])
        add_points(uid, -amt)
        bot.send_message(message.chat.id, f"✅ تم", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ خطأ", reply_markup=admin_menu())


@bot.message_handler(commands=['add_channel'])
def add_channel_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    msg = bot.send_message(message.chat.id,
        "📢 اكتب: <code>CHANNEL_ID | NAME | URL</code>",
        parse_mode='HTML')
    bot.register_next_step_handler(msg, process_add_channel)


def process_add_channel(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = [p.strip() for p in message.text.split('|')]
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ صيغة غلط", reply_markup=admin_menu())
            return
        ch_id, name, url = parts
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO force_channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                      (ch_id, name, url))
            conn.commit()
            conn.close()
        bot.send_message(message.chat.id, f"✅ تم إضافة: <b>{name}</b>",
                         parse_mode='HTML', reply_markup=admin_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {e}", reply_markup=admin_menu())


@bot.message_handler(commands=['del_channel'])
def del_channel_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        cid = int(message.text.split()[1])
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM force_channels WHERE id=?", (cid,))
            conn.commit()
            conn.close()
        bot.send_message(message.chat.id, f"✅ اتحذف", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ اكتب: /del_channel ID", reply_markup=admin_menu())


@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.send_message(message.chat.id, "👑 <b>لوحة التحكم</b>",
                     parse_mode='HTML', reply_markup=admin_menu())


@bot.message_handler(commands=['myid'])
def my_id_cmd(message):
    uid = message.from_user.id
    bot.reply_to(message, f"🆔 <code>{uid}</code>", parse_mode='HTML')


if __name__ == "__main__":
    print(f"🔥 {BOT_NAME} — البوت شغّال...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            print(f"⚠️ إعادة تشغيل: {e}")
            time.sleep(5)
