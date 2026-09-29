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


# ==================== DATABASE ====================
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
        type TEXT,
        identifier TEXT,
        name TEXT,
        url TEXT
    )''')
    conn.commit()
    conn.close()


init_db()


# ==================== HELPERS ====================
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
        c.execute("SELECT id, type, identifier, name, url FROM force_channels")
        rows = c.fetchall()
        conn.close()
    return rows


def add_force_channel(ftype, identifier, name, url):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO force_channels (type, identifier, name, url) VALUES (?, ?, ?, ?)",
                  (ftype, identifier, name, url))
        conn.commit()
        conn.close()


def delete_force_channel(cid):
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM force_channels WHERE id=?", (cid,))
        conn.commit()
        conn.close()


def is_bot_on():
    return get_setting('bot_on', '1') == '1'


# ==================== SUBSCRIPTION CHECK ====================
def check_subscription(user_id):
    """يرجع (True, []) لو مشترك في كل حاجة، أو (False, [عناصر غير مشترك فيها])"""
    channels = get_force_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for cid, ftype, identifier, name, url in channels:
        # للقنوات والجروبات: نتحقق بـ get_chat_member
        if ftype in ('channel', 'group'):
            try:
                member = bot.get_chat_member(identifier, user_id)
                if member.status in ['left', 'kicked']:
                    not_subscribed.append({
                        'id': cid, 'type': ftype, 'name': name, 'url': url
                    })
            except Exception as e:
                # لو فشل التحقق (مثلاً البوت مش أدمن)، نعتبره مشترك
                print(f"Sub check failed for {identifier}: {e}")
                continue
        # للينكات والبوتات: نعرضها بس بدون تحقق
        elif ftype in ('link', 'bot'):
            # نعتبر المستخدم مشترك لو ضغط على "تحققت" قبل كده
            key = f"verified_{user_id}_{cid}"
            if get_setting(key, '0') != '1':
                not_subscribed.append({
                    'id': cid, 'type': ftype, 'name': name, 'url': url
                })

    return len(not_subscribed) == 0, not_subscribed


# ==================== MENUS ====================
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
        types.InlineKeyboardButton(f"📢 الاشتراك الإجباري ({channels_count})", callback_data="admin_force"),
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
            type_emoji = {"channel": "📢", "group": "👥", "bot": "🤖", "link": "🔗"}.get(ftype, "📌")
            markup.add(types.InlineKeyboardButton(
                f"{type_emoji} {name}  |  🗑 حذف",
                callback_data=f"force_del_{cid}"
            ))

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
        type_emoji = {"channel": "📢", "group": "👥", "bot": "🤖", "link": "🔗"}.get(item['type'], "📌")
        markup.add(types.InlineKeyboardButton(
            f"{type_emoji} {item['name']}",
            url=item['url']
        ))
    markup.add(types.InlineKeyboardButton("✅ تحقّق من الاشتراك", callback_data="check_sub"))
    return markup


# ==================== START ====================
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

    # ============ فحص الاشتراك الإجباري ============
    ok, not_subscribed = check_subscription(user_id)
    if not ok:
        text = (
            "⚠️ <b>لازم تشترك في القنوات/الجروبات دي الأول:</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "اضغط على كل واحدة، اشترك فيها، وبعدين اضغط ✅ <b>تحقّق من الاشتراك</b>"
        )
        bot.send_message(user_id, text, parse_mode='HTML',
                         reply_markup=subscribe_menu(not_subscribed))
        return

    if not is_bot_on() and user_id != OWNER_ID:
        bot.send_message(user_id, "🔴 <b>البوت متوقف مؤقتاً</b>", parse_mode='HTML')
        return

    send_welcome(user_id, first_name)


# ==================== CALLBACKS ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    is_owner = user_id == OWNER_ID

    # ============ رجوع رئيسي ============
    if data == "back_main":
        bot.answer_callback_query(call.id)
        send_welcome(chat_id)
        return

    # ============ فحص الاشتراك ============
    if data == "check_sub":
        bot.answer_callback_query(call.id)
        ok, not_subscribed = check_subscription(user_id)
        if ok:
            bot.send_message(chat_id, "✅ <b>تم التحقق! أهلاً بيك.</b>", parse_mode='HTML')
            send_welcome(chat_id)
        else:
            bot.send_message(chat_id,
                "❌ <b>لسه مشتركتش في كل القنوات!</b>\n\n"
                "اتأكد إنك اشتركت في كل اللي فوق، وبعدين اضغط تحقّق تاني.",
                parse_mode='HTML',
                reply_markup=subscribe_menu(not_subscribed))
        return

    # ============ قوائم عامة ============
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
        cursor = None
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
            ref_count = c.fetchone()[0]
            conn.close()
        text = (
            "💰 <b>نقاطك</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"⭐ الرصيد: <b>{points}</b>\n"
            f"👥 اللي دخلوا منك: <b>{ref_count}</b>"
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
        msg = bot.send_message(chat_id, "📱 <b>أدخل رقم الواتساب</b>",
                               parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_number)
        return

    if data == "bridge":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🛡 <b>أدخل الباند المرفوض</b>",
                               parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_band)
        return

    # ============ أدمن فقط ============
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
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL")
            referred = c.fetchone()[0]
            conn.close()
        text = (
            "📊 <b>إحصائيات</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"👥 الإجمالي: <b>{total}</b>\n"
            f"🆕 اليوم: <b>{today}</b>\n"
            f"🔗 جايين من روابط: <b>{referred}</b>"
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

    # ============ إدارة الاشتراك الإجباري ============
    if data == "admin_force":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id,
            "📢 <b>إدارة الاشتراك الإجباري</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "اضغط على أي اشتراك لحذفه، أو أضف واحد جديد.",
            parse_mode='HTML',
            reply_markup=force_admin_menu())
        return

    if data == "force_add":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id,
            "📌 <b>اختار نوع الاشتراك:</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📢 <b>قناة</b>: لازم تعمل البوت أدمن فيها\n"
            "👥 <b>جروب</b>: لازم تعمل البوت أدمن فيه\n"
            "🤖 <b>بوت</b>: مفيش تحقق، زر بس\n"
            "🔗 <b>لينك</b>: مفيش تحقق، زر بس",
            parse_mode='HTML',
            reply_markup=force_type_menu())
        return

    if data.startswith("force_del_"):
        bot.answer_callback_query(call.id)
        cid = int(data.replace("force_del_", ""))
        delete_force_channel(cid)
        bot.send_message(chat_id, "✅ <b>تم الحذف</b>", parse_mode='HTML',
                         reply_markup=force_admin_menu())
        return

    if data in ("force_type_channel", "force_type_group", "force_type_bot", "force_type_link"):
        bot.answer_callback_query(call.id)
        ftype = data.replace("force_type_", "")

        if ftype == "channel":
            text = (
                "📢 <b>إضافة قناة للاشتراك الإجباري</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ابعت يوزرنيم القناة بالشكل ده:\n"
                "<code>@channel_username</code>\n\n"
                "⚠️ لازم تعمل البوت <b>أدمن</b> في القناة الأول."
            )
        elif ftype == "group":
            text = (
                "👥 <b>إضافة جروب للاشتراك الإجباري</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ابعت يوزرنيم الجروب بالشكل ده:\n"
                "<code>@group_username</code>\n\n"
                "⚠️ لازم تعمل البوت <b>أدمن</b> في الجروب الأول."
            )
        elif ftype == "bot":
            text = (
                "🤖 <b>إضافة بوت للاشتراك الإجباري</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ابعت رابط البوت:\n"
                "<code>https://t.me/bot_username</code>"
            )
        else:  # link
            text = (
                "🔗 <b>إضافة لينك للاشتراك الإجباري</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ابعت اللينك (أي رابط):\n"
                "<code>https://example.com</code>"
            )

        msg = bot.send_message(chat_id, text, parse_mode='HTML',
                               reply_markup=types.InlineKeyboardMarkup().add(
                                   types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_force")))
        bot.register_next_step_handler(msg, process_add_force, ftype)
        return


# ==================== PROCESS FORCE ADD ====================
def process_add_force(message, ftype):
    if message.from_user.id != OWNER_ID:
        return
    if not message.text:
        return
    text = message.text.strip()

    if text.startswith('/'):
        return

    # استخراج البيانات
    if ftype in ('channel', 'group'):
        identifier = text
        if not identifier.startswith('@') and not identifier.startswith('-100'):
            bot.send_message(message.chat.id,
                "❌ <b>صيغة غلط</b>\n"
                "لازم تبدأ بـ <code>@</code> (مثلاً <code>@mychannel</code>)",
                parse_mode='HTML', reply_markup=force_admin_menu())
            return

        try:
            chat_info = bot.get_chat(identifier)
            name = chat_info.title or identifier
            if hasattr(chat_info, 'username') and chat_info.username:
                url = f"https://t.me/{chat_info.username}"
            else:
                url = f"https://t.me/c/{str(chat_info.id).replace('-100', '')}"
        except Exception as e:
            bot.send_message(message.chat.id,
                f"❌ <b>مش قادر ألاقي القناة/الجروب</b>\n"
                f"<code>{e}</code>\n\n"
                "تأكد إن:\n"
                "1. البوت أدمن في القناة/الجروب\n"
                "2. اليوزرنيم صحيح",
                parse_mode='HTML', reply_markup=force_admin_menu())
            return

        # تأكد إن البوت أدمن
        try:
            bot_member = bot.get_chat_member(identifier, bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                bot.send_message(message.chat.id,
                    "⚠️ <b>البوت مش أدمن!</b>\n"
                    "لازم تعمل البوت أدمن في القناة/الجروب الأول، وبعدين جرب تاني.",
                    parse_mode='HTML', reply_markup=force_admin_menu())
                return
        except Exception as e:
            bot.send_message(message.chat.id,
                f"⚠️ <b>مش قادر أتحقق من الصلاحيات</b>\n"
                f"تأكد إن البوت أدمن. الخطأ: <code>{e}</code>",
                parse_mode='HTML', reply_markup=force_admin_menu())
            return

        add_force_channel(ftype, identifier, name, url)
        type_name = "القناة" if ftype == "channel" else "الجروب"
        bot.send_message(message.chat.id,
            f"✅ <b>تم إضافة {type_name}</b>\n\n"
            f"📛 الاسم: <b>{name}</b>\n"
            f"🆔 المعرف: <code>{identifier}</code>\n"
            f"🔗 الرابط: {url}",
            parse_mode='HTML', reply_markup=force_admin_menu())

    elif ftype == 'bot':
        url = text if text.startswith('http') else f"https://t.me/{text.replace('@', '')}"
        try:
            identifier = url.replace("https://t.me/", "").replace("@", "")
            name = f"@{identifier}"
            add_force_channel('bot', identifier, name, url)
            bot.send_message(message.chat.id,
                f"✅ <b>تم إضافة البوت</b>\n\n"
                f"🔗 الرابط: {url}",
                parse_mode='HTML', reply_markup=force_admin_menu())
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ: {e}", reply_markup=force_admin_menu())

    else:  # link
        url = text
        if not url.startswith('http'):
            bot.send_message(message.chat.id,
                "❌ اللينك لازم يبدأ بـ <code>http</code>",
                parse_mode='HTML', reply_markup=force_admin_menu())
            return
        name = url[:30] + ("..." if len(url) > 30 else "")
        add_force_channel('link', url, name, url)
        bot.send_message(message.chat.id,
            f"✅ <b>تم إضافة اللينك</b>\n\n"
            f"🔗 {url}",
            parse_mode='HTML', reply_markup=force_admin_menu())


# ==================== PROCESS TEXT ====================
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
            time.sleep(0.05)
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


# ==================== RUN ====================
if __name__ == "__main__":
    print(f"🔥 {BOT_NAME} — البوت شغّال...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            print(f"⚠️ إعادة تشغيل: {e}")
            time.sleep(5)
