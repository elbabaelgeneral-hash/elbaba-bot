import os
import telebot
from telebot import types
import sqlite3
import random
import time
import threading
from features import wifi_scan, format_wifi_scan, analyze_national_id

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = 8772508181
DEV_USERNAME = "@ELBABAELGRNERAL"
BOT_NAME = "ELGENERAL"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = threading.Lock()


APPEAL_TEMPLATES = {
    "t1": {"title": "📝 قالب 1 — استئناف عام", "text": """السلام عليكم فريق دعم واتساب،

أراسلكم بخصوص حظر حسابي على واتساب. رقمي هو: [اكتب رقمك هنا]

أنا أستخدم واتساب بشكل شخصي وعائلي فقط، ولم أقصد مخالفة أي من سياساتكم.

أرجو منكم إعادة النظر في قرار الحظر وإعادة تفعيل حسابي.

شكراً لكم على وقتكم وجهدكم.

مع التحية."""},
    "t2": {"title": "📝 قالب 2 — استئناف شخصي", "text": """إلى فريق دعم واتساب الموقر،

تحية طيبة وبعد،

أكتب إليكم بخصوص حظر حسابي على منصة واتساب. رقمي: [اكتب رقمك هنا]

أنا شخص عادي أستخدم التطبيق للتواصل مع عائلتي وأصدقائي. لم أرتكب أي مخالفة متعمدة، وإذا حدث خطأ سهواً فأنا أعتذر عنه.

أطلب منكم مراجعة حسابي وإعادته.

شكراً لتعاونكم."""},
    "t3": {"title": "📝 قالب 3 — حساب عمل", "text": """السادة فريق دعم واتساب،

أنا صاحب عمل صغير وأستخدم واتساب للتواصل مع عملائي. رقمي: [اكتب رقمك هنا]

حظر الحساب يؤثر بشكل كبير على عملي ومصدر رزقي الوحيد.

أرجو منكم مراجعة قرار الحظر وإعادة تفعيل حسابي. أتعهد بالالتزام بجميع سياسات واتساب.

مع الشكر الجزيل."""},
    "t4": {"title": "📝 قالب 4 — حظر خاطئ", "text": """فريق دعم واتساب،

تحية طيبة،

تم حظر حسابي على واتساب رقم: [اكتب رقمك هنا]

أعتقد أن هذا الحظر حدث بالخطأ، أو أن شخصاً ما أبلغ عني بشكل كاذب لأسباب شخصية.

أرجو منكم التحقق من حسابي بعناية، فأنا مستخدم منتظم منذ سنوات ولم أرتكب أي مخالفة.

شكراً لكم."""},
    "t5": {"title": "📝 قالب 5 — استئناف رسمي", "text": """إلى قسم مراجعة الحسابات في واتساب،

بخصوص: طلب استئناف حظر حساب

رقم الهاتف: [اكتب رقمك هنا]
تاريخ الحظر التقريبي: [اكتب التاريخ]

السبب حسب علمي: غير معروف

التماس الاستئناف:
أرجو إعادة النظر في قرار حظر حسابي. أستخدم واتساب لأغراض شخصية مشروعة، وأتعهد بالالتزام بكافة سياسات وشروط خدمة واتساب.

شكراً لتفهمكم وتعاونكم."""},
    "t6": {"title": "📝 قالب 6 — مستخدم جديد", "text": """فريق واتساب المحترم،

رقمي: [اكتب رقمك هنا]

حسابي تم حظره بعد فترة قصيرة من إنشائه، وأنا لم أقم بأي نشاط مخالف.

ربما حدث هذا بسبب نشاط تلقائي من جهاز جديد أو رقم جديد.

أرجو منكم إعادة تفعيل حسابي لأتمكن من التواصل مع أهلي.

شكراً لكم."""},
    "t7": {"title": "📝 قالب 7 — استئناف إنجليزي", "text": """Dear WhatsApp Support Team,

I am writing to appeal the ban on my WhatsApp account.

Phone Number: [Type your number here]
Date of Ban: [Approximate date]

I have been using WhatsApp for personal communication with family and friends. I have not intentionally violated any of your policies.

I kindly request you to review my account and restore it. I promise to comply with all WhatsApp terms of service.

Thank you for your time and consideration.

Sincerely."""},
    "t8": {"title": "📝 قالب 8 — تاجر/متجر", "text": """فريق دعم واتساب،

أنا صاحب متجر إلكتروني وأستخدم واتساب للتواصل مع العملاء وتلقي الطلبات. رقمي: [اكتب رقمك هنا]

حظر حسابي تسبب في خسارة كبيرة للعملاء والإيرادات.

أرجو منكم إعادة تفعيل حسابي بشكل عاجل. أنا ملتزم بسياساتكم ولن أستخدم الحساب في أي نشاط مخالف.

شكراً لتفهمكم."""},
    "t9": {"title": "📝 قالب 9 — طالب", "text": """إلى فريق دعم واتساب،

أنا طالب جامعي وأستخدم واتساب بشكل أساسي للتواصل مع زملائي في الجامعة والمشاريع الدراسية. رقمي: [اكتب رقمك هنا]

حظر حسابي أثر بشكل كبير على دراستي.

أرجو منكم مراجعة حسابي وإعادته. لم أرتكب أي مخالفة متعمدة.

شكراً لكم على جهودكم."""},
    "t10": {"title": "📝 قالب 10 — استئناف مفصل", "text": """فريق دعم واتساب المحترم،

تحية طيبة وبعد،

أتقدم إليكم بهذا الاستئناف بخصوص حظر حسابي على تطبيق واتساب.

📱 معلومات الحساب:
• رقم الهاتف: [اكتب رقمك هنا]
• تاريخ الحظر التقريبي: [اكتب التاريخ]

📋 تفاصيل:
أنا مستخدم واتساب منذ [اكتب عدد السنوات]. أستخدم الحساب بشكل شخصي فقط للتواصل مع الأهل والأصدقاء. لم أقم بأي نشاط مخالف لسياسات واتساب.

🙏 الطلب:
أرجو منكم إعادة النظر في قرار الحظر، وإعادة تفعيل حسابي. أتعهد بالالتزام الكامل بجميع شروط الخدمة والسياسات.

شكراً لتعاونكم، وبارك الله فيكم.

مع خالص التحية والاحترام."""}
}


def get_db():
    conn = sqlite3.connect('bot.db', check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, points INTEGER DEFAULT 0, referred_by INTEGER, joined_at INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, identifier TEXT, name TEXT, url TEXT)''')
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
        c.execute("INSERT INTO users (user_id, username, first_name, points, referred_by, joined_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, username or "", first_name or "", 0, referred_by, int(time.time())))
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
        c.execute("INSERT INTO force_channels (type, identifier, name, url) VALUES (?, ?, ?, ?)", (ftype, identifier, name, url))
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


def check_subscription(user_id):
    channels = get_force_channels()
    if not channels:
        return True, []
    not_subscribed = []
    for cid, ftype, identifier, name, url in channels:
        if ftype in ('link', 'bot'):
            continue
        try:
            member = bot.get_chat_member(identifier, user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append({'id': cid, 'type': ftype, 'name': name, 'url': url})
        except Exception as e:
            print(f"Sub check failed: {e}")
            continue
    return len(not_subscribed) == 0, not_subscribed


def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚡ تفعيل الاتصال الأبدي", callback_data="activate"),
        types.InlineKeyboardButton("💣 بناء جسر التلغيم", callback_data="bridge"),
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
    markup.add(types.InlineKeyboardButton(f"📢 الاشتراك الإجباري ({channels_count})", callback_data="admin_force"))
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
            markup.add(types.InlineKeyboardButton(f"{type_emoji} {name} | 🗑 حذف", callback_data=f"force_del_{cid}"))
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
        markup.add(types.InlineKeyboardButton(f"{type_emoji} {item['name']}", url=item['url']))
    markup.add(types.InlineKeyboardButton("✅ تحقّق من الاشتراك", callback_data="check_sub"))
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
            bot.send_message(referred_by, "🎉 <b>مبروك!</b>\n👤 واحد جديد دخل من رابطك\n💰 +10 نقاط", parse_mode='HTML')
        except:
            pass
    ok, not_subscribed = check_subscription(user_id)
    if not ok:
        text = "⚠️ <b>لازم تشترك في القنوات/الجروبات دي الأول:</b>\n\nاضغط على كل واحدة، اشترك، وبعدين اضغط ✅ <b>تحقّق</b>"
        bot.send_message(user_id, text, parse_mode='HTML', reply_markup=subscribe_menu(not_subscribed))
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
        ok, not_subscribed = check_subscription(user_id)
        if ok:
            bot.send_message(chat_id, "✅ <b>تم التحقق!</b>", parse_mode='HTML')
            send_welcome(chat_id)
        else:
            bot.send_message(chat_id, "❌ <b>لسه مشتركتش!</b>", parse_mode='HTML', reply_markup=subscribe_menu(not_subscribed))
        return

    if data == "my_link":
        bot.answer_callback_query(call.id)
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
        text = f"🔗 <b>رابط الدعوة</b>\n━━━━━━━━━━━━━━━━━━\n<code>{link}</code>\n\n💰 كل واحد = <b>+10 نقاط</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 مشاركة", url=f"https://t.me/share/url?url={link}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
        return

    if data == "my_points":
        bot.answer_callback_query(call.id)
        points = get_points(user_id)
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
            ref_count = c.fetchone()[0]
            conn.close()
        text = f"💰 <b>نقاطك</b>\n━━━━━━━━━━━━━━━━━━\n⭐ الرصيد: <b>{points}</b>\n👥 اللي دخلوا منك: <b>{ref_count}</b>"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "info":
        bot.answer_callback_query(call.id)
        text = f"ℹ️ <b>معلومات</b>\n━━━━━━━━━━━━━━━━━━\n🔥 <b>{BOT_NAME}</b>\n👨‍💻 {DEV_USERNAME}"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=back_menu())
        return

    if data == "wifi_scan":
        bot.answer_callback_query(call.id)
        wait_msg = bot.send_message(chat_id, "📡 <b>جاري مسح الشبكات...</b>", parse_mode='HTML')
        time.sleep(2)
        networks = wifi_scan()
        text = format_wifi_scan(networks)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 مسح تاني", callback_data="wifi_scan"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.edit_message_text(text, chat_id, wait_msg.message_id, parse_mode='HTML', reply_markup=markup)
        return

    if data == "nid_analyze":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id,
            "🆔 <b>محلل الرقم القومي</b>\n━━━━━━━━━━━━━━━━━━\nابعت الرقم القومي (14 رقم)\nمثال: <code>29501021234567</code>",
            parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_nid)
        return

    if data == "unban_help":
        bot.answer_callback_query(call.id)
        text = (
            "🚫 <b>مساعد فك حظر واتساب</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>الخطوات الرسمية لفك الحظر:</b>\n\n"
            "1️⃣ افتح تطبيق واتساب\n"
            "2️⃣ روح للإعدادات ⚙️\n"
            "3️⃣ اضغط Help / المساعدة\n"
            "4️⃣ اضغط Contact Us / اتصل بنا\n"
            "5️⃣ اكتب رسالة استئناف باحترام\n"
            "6️⃣ استنى الرد (24-48 ساعة)\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>الموقع الرسمي:</b>\n"
            "https://faq.whatsapp.com\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <b>تحذير مهم:</b>\n\n"
            "❌ مفيش أي حد يقدر يفك حظر رقمك غير فريق واتساب الرسمي\n\n"
            "❌ أي حد يقولك \"ابعتلي إيميلك وباسوردك وهفكلك الحظر\" = <b>نصب</b>\n\n"
            "❌ متبعتش بياناتك لأي حد مهما كان\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>نصائح لتجنب الحظر:</b>\n\n"
            "• متبعتش رسائل جماعية كثيرة\n"
            "• متضيفش ناس في جروبات بدون إذن\n"
            "• متستخدمش نسخ معدلة\n"
            "• متبعتش لينكات مشبوهة\n"
            "• استخدم WhatsApp Business للأنشطة التجارية"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 موقع واتساب الرسمي", url="https://faq.whatsapp.com"))
        markup.add(types.InlineKeyboardButton("📝 قوالب الاستئناف الجاهزة", callback_data="appeal_templates"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        return

    if data == "appeal_templates":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, tpl in APPEAL_TEMPLATES.items():
            markup.add(types.InlineKeyboardButton(tpl["title"], callback_data=f"show_{key}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        text = (
            "📝 <b>قوالب استئناف واتساب الجاهزة</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "اختار القالب اللي يناسب حالتك:\n\n"
            "👇"
        )
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
        return

    if data.startswith("show_") and data.replace("show_", "") in APPEAL_TEMPLATES:
        bot.answer_callback_query(call.id)
        key = data.replace("show_", "")
        tpl = APPEAL_TEMPLATES[key]
        text = (
            f"<b>{tpl['title']}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"<blockquote>{tpl['text']}</blockquote>\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📌 <b>خطوات الإرسال:</b>\n\n"
            "1️⃣ اضغط على الرسالة فوق مطوّل عشان تنسخها\n"
            "2️⃣ غير <code>[اكتب رقمك هنا]</code> برقمك\n"
            "3️⃣ اضغط الرابط اللي تحت\n"
            "4️⃣ الصق الرسالة في النموذج\n"
            "5️⃣ اكتب بريدك واضغط Send"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🌐 نموذج دعم واتساب الرسمي", url="https://www.whatsapp.com/contact/"))
        markup.add(types.InlineKeyboardButton("📋 قوالب تانية", callback_data="appeal_templates"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        return

    if data == "activate":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📱 <b>أدخل رقم الواتساب</b>", parse_mode='HTML', reply_markup=back_menu())
        bot.register_next_step_handler(msg, process_number)
        return

    if data == "bridge":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🛡 <b>أدخل الباند المرفوض</b>", parse_mode='HTML', reply_markup=back_menu())
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
        day_ago = int(time.time()) - 86400
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users WHERE joined_at > ?", (day_ago,))
            today = c.fetchone()[0]
            conn.close()
        text = f"📊 <b>إحصائيات</b>\n━━━━━━━━━━━━━━━━━━\n👥 الإجمالي: <b>{total}</b>\n🆕 اليوم: <b>{today}</b>"
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=admin_menu())
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
        bot.send_message(chat_id, f"👥 <b>{total} مستخدم</b>", parse_mode='HTML', reply_markup=admin_menu())
        return

    if data == "admin_force":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id,
            "📢 <b>الاشتراك الإجباري</b>\n\nاضغط على أي اشتراك لحذفه، أو أضف جديد.",
            parse_mode='HTML', reply_markup=force_admin_menu())
        return

    if data == "force_add":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id,
            "📌 <b>اختار النوع:</b>\n\n"
            "📢 قناة / 👥 جروب: لازم البوت أدمن\n"
            "🤖 بوت / 🔗 لينك: مش بيحجب البوت",
            parse_mode='HTML', reply_markup=force_type_menu())
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
        if ftype == "channel":
            text = ("📢 <b>إضافة قناة</b>\n\n"
                    "1️⃣ للقنوات العامة: ابعت <code>@username</code>\n"
                    "2️⃣ لأي قناة: <b>اعمل Forward لأي رسالة</b>\n\n"
                    "⚠️ البوت لازم يكون أدمن")
        elif ftype == "group":
            text = ("👥 <b>إضافة جروب</b>\n\n"
                    "1️⃣ للجروبات العامة: ابعت <code>@username</code>\n"
                    "2️⃣ لأي جروب: <b>اعمل Forward لأي رسالة</b>\n\n"
                    "⚠️ البوت لازم يكون أدمن")
        elif ftype == "bot":
            text = ("🤖 <b>إضافة بوت</b>\n\nابعت رابط البوت:\n<code>https://t.me/bot_username</code>\n\n"
                    "ℹ️ مش هيحجب البوت")
        else:
            text = ("🔗 <b>إضافة لينك</b>\n\nابعت اللينك:\n<code>https://example.com</code>\n\n"
                    "ℹ️ مش هيحجب البوت")
        msg = bot.send_message(chat_id, text, parse_mode='HTML',
                               reply_markup=types.InlineKeyboardMarkup().add(
                                   types.InlineKeyboardButton("❌ إلغاء", callback_data="admin_force")))
        bot.register_next_step_handler(msg, process_add_force, ftype)
        return


def process_add_force(message, ftype):
    if message.from_user.id != OWNER_ID:
        return
    if ftype in ('channel', 'group'):
        chat_id_to_use = None
        chat_name = None
        chat_url = None
        if message.forward_from_chat:
            chat = message.forward_from_chat
            chat_id_to_use = chat.id
            chat_name = chat.title or "بدون اسم"
            if chat.username:
                chat_url = f"https://t.me/{chat.username}"
            else:
                try:
                    invite = bot.create_chat_invite_link(chat.id)
                    chat_url = invite.invite_link
                except:
                    chat_url = f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        elif message.text:
            text = message.text.strip()
            if text.startswith('/'):
                return
            if not (text.startswith('@') or text.startswith('-100')):
                bot.send_message(message.chat.id, "❌ صيغة غلط", reply_markup=force_admin_menu())
                return
            try:
                chat = bot.get_chat(text)
                chat_id_to_use = chat.id
                chat_name = chat.title or text
                if chat.username:
                    chat_url = f"https://t.me/{chat.username}"
                else:
                    try:
                        invite = bot.create_chat_invite_link(chat.id)
                        chat_url = invite.invite_link
                    except:
                        chat_url = f"https://t.me/c/{str(chat.id).replace('-100', '')}"
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}", reply_markup=force_admin_menu())
                return
        else:
            return
        try:
            bot_member = bot.get_chat_member(chat_id_to_use, bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                bot.send_message(message.chat.id, "⚠️ البوت مش أدمن!", reply_markup=force_admin_menu())
                return
        except:
            pass
        identifier = str(chat_id_to_use)
        add_force_channel(ftype, identifier, chat_name, chat_url)
        type_name = "القناة" if ftype == "channel" else "الجروب"
        bot.send_message(message.chat.id,
            f"✅ <b>تم إضافة {type_name}</b>\n\n📛 {chat_name}\n🆔 <code>{chat_id_to_use}</code>\n🔗 {chat_url}",
            parse_mode='HTML', reply_markup=force_admin_menu())
        return
    elif ftype == 'bot':
        if not message.text:
            return
        url = message.text.strip()
        if url.startswith('/'):
            return
        if not url.startswith('http'):
            url = f"https://t.me/{url.replace('@', '')}"
        identifier = url.replace("https://t.me/", "").replace("@", "")
        add_force_channel('bot', identifier, f"@{identifier}", url)
        bot.send_message(message.chat.id, f"✅ <b>تم إضافة البوت</b>\n\n🔗 {url}",
                         parse_mode='HTML', reply_markup=force_admin_menu())
    else:
        if not message.text:
            return
        url = message.text.strip()
        if url.startswith('/'):
            return
        if not url.startswith('http'):
            bot.send_message(message.chat.id, "❌ اللينك لازم يبدأ بـ http", reply_markup=force_admin_menu())
            return
        name = url[:30] + ("..." if len(url) > 30 else "")
        add_force_channel('link', url, name, url)
        bot.send_message(message.chat.id, f"✅ <b>تم إضافة اللينك</b>\n\n🔗 {url}",
                         parse_mode='HTML', reply_markup=force_admin_menu())


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
    text = f"✅ <b>تم التفعيل</b>\n📱 الرقم: <code>{number}</code>\n🔗 الجسر: <code>{fake}</code>\n🔑 <code>{code}</code>"
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
    text = f"💣 <b>تم التلغيم</b>\n🎯 <code>{band}</code>\n💣 <code>{weapon_id}</code>"
    bot.edit_message_text(text, chat_id, msg.message_id, parse_mode='HTML')
    bot.send_message(chat_id, "اختر من القائمة 👇", reply_markup=main_menu(chat_id))


def process_nid(message):
    if message.text and message.text.startswith('/'):
        return
    chat_id = message.chat.id
    text = message.text.strip()
    full_name = ""
    id_num = text
    if '|' in text:
        parts = [p.strip() for p in text.split('|', 1)]
        full_name = parts[0]
        id_num = parts[1]
    result = analyze_national_id(id_num.strip(), full_name)
    bot.send_message(chat_id, result, parse_mode='HTML', reply_markup=main_menu(chat_id))


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
        add_points(int(parts[0]), int(parts[1]))
        bot.send_message(message.chat.id, "✅ تم", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ خطأ", reply_markup=admin_menu())


def process_remove_points(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        parts = message.text.split()
        add_points(int(parts[0]), -int(parts[1]))
        bot.send_message(message.chat.id, "✅ تم", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ خطأ", reply_markup=admin_menu())


@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.send_message(message.chat.id, "👑 <b>لوحة التحكم</b>", parse_mode='HTML', reply_markup=admin_menu())


@bot.message_handler(commands=['myid'])
def my_id_cmd(message):
    bot.reply_to(message, f"🆔 <code>{message.from_user.id}</code>", parse_mode='HTML')


if __name__ == "__main__":
    print(f"🔥 {BOT_NAME} — البوت شغّال...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            print(f"⚠️ إعادة تشغيل: {e}")
            time.sleep(5)
