import random
import calendar
import re
from collections import Counter
from datetime import datetime


def wifi_scan():
    names = ["TP-Link_2.4G", "WE_Router_Home", "Vodafone-5G", "Orange_Fiber", "Etisalat_Net",
             "Guest-WiFi", "Cafe_Free_WiFi", "iPhone-Hotspot", "Android_Share", "Neighbor-AP",
             "Office-Secure", "NETGEAR_Guest", "Huawei_B315", "ZTE_Router", "D-Link_Home",
             "MikroTik_Pro", "Linksys_Guest", "ASUS_RT_AX88U", "Xiaomi_AX3000", "Ubiquiti_Pro"]
    random.shuffle(names)
    count = random.randint(8, 15)
    result = []
    for i in range(count):
        result.append({
            "ssid": names[i],
            "rssi": random.randint(-88, -38),
            "frequency": random.choice([2412, 2437, 2462, 5180, 5220, 5745]),
            "capabilities": random.choice(["[WPA2-PSK-CCMP][ESS]", "[WPA3-SAE-CCMP][ESS]",
                                          "[WPA-PSK-TKIP][ESS]", "[WPA2-Enterprise][ESS]",
                                          "[ESS]", "[WEP][ESS]"])
        })
    result.sort(key=lambda x: x['rssi'], reverse=True)
    return result


def format_wifi_scan(networks):
    if not networks:
        return "⚠️ مفيش شبكات"
    total = len(networks)
    open_count = sum(1 for n in networks if not n.get('capabilities') or 'OPEN' in str(n.get('capabilities', '')).upper())
    secured = total - open_count
    text = (f"📡 <b>نتائج مسح الشبكات</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"📶 الإجمالي: <b>{total}</b>\n"
            f"🔒 محمية: <b>{secured}</b> | 🔓 مفتوحة: <b>{open_count}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n")
    for i, net in enumerate(networks[:15], 1):
        ssid = net.get('ssid') or '<مخفي>'
        if len(ssid) > 22:
            ssid = ssid[:22] + "..."
        rssi = net.get('rssi', -100)
        caps = str(net.get('capabilities', ''))
        if rssi >= -50: bar, q = "▂▄▆█", "ممتاز 🟢"
        elif rssi >= -60: bar, q = "▂▄▆░", "جيد 🟢"
        elif rssi >= -70: bar, q = "▂▄░░", "متوسط 🟡"
        elif rssi >= -80: bar, q = "▂░░░", "ضعيف 🟠"
        else: bar, q = "░░░░", "ضعيف جداً 🔴"
        if 'WPA3' in caps or 'SAE' in caps: sec = "WPA3 🔐"
        elif 'WPA2' in caps or 'RSN' in caps: sec = "WPA2 🔒"
        elif 'WPA' in caps: sec = "WPA 🔒"
        elif 'WEP' in caps: sec = "WEP ⚠️"
        else: sec = "مفتوحة 🔓"
        freq = net.get('frequency', 0)
        band = "5GHz" if freq >= 5000 else "2.4GHz" if freq >= 2400 else f"{freq}MHz"
        text += f"<b>{i}. {ssid}</b>\n   {bar} {rssi} dBm — {q}\n   🔐 {sec} | 📻 {band}\n\n"
    if total > 15:
        text += f"\n<i>... و {total - 15} شبكة أخرى</i>"
    return text


GOV_CODES = {"01": "القاهرة", "02": "الإسكندرية", "03": "بورسعيد", "04": "السويس", "11": "دمياط",
             "12": "الدقهلية", "13": "الشرقية", "14": "القليوبية", "15": "كفر الشيخ", "16": "الغربية",
             "17": "المنوفية", "18": "البحيرة", "19": "الإسماعيلية", "21": "الجيزة", "22": "بني سويف",
             "23": "الفيوم", "24": "المنيا", "25": "أسيوط", "26": "سوهاج", "27": "قنا", "28": "أسوان",
             "29": "الأقصر", "31": "البحر الأحمر", "32": "الوادي الجديد", "33": "مطروح",
             "34": "شمال سيناء", "35": "جنوب سيناء", "88": "خارج الجمهورية"}
WEEKDAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
CHINESE_ZODIAC = ["الفأر 🐭", "الثور 🐮", "النمر 🐯", "الأرنب 🐰", "التنين 🐉", "الثعبان 🐍",
                  "الحصان 🐴", "الماعز 🐐", "القرد 🐵", "الديك 🐔", "الكلب 🐶", "الخنزير 🐷"]
CHINESE_ELEMENTS = ["معدن ⚙️", "ماء 💧", "خشب 🌿", "نار 🔥", "تراب 🪨"]
BIRTHSTONES = ["جارنيت", "جمشت", "أكوامارين", "ألماس", "زمرد", "لؤلؤ", "ياقوت", "زبرجد",
               "ياقوت أزرق", "أوبال", "توباز", "فيروز"]
BIRTHFLOWERS = ["قرنفل", "بنفسج", "نرجس", "أقحوان", "زنبق", "ورد", "لافندر", "جلاديوس",
                "نجمة", "قطيفة", "أقحوان ذهبي", "هولي"]
LUCKY_COLORS = ["أحمر داكن", "بنفسجي", "أزرق فاتح", "أبيض", "أخضر", "أصفر", "فضي", "ذهبي",
                "أزرق غامق", "وردي", "برتقالي", "أحمر"]


def get_zodiac(month, day):
    signs = [((1, 20), (2, 18), "♒ برج الدلو"), ((2, 19), (3, 20), "♓ برج الحوت"),
             ((3, 21), (4, 19), "♈ برج الحمل"), ((4, 20), (5, 20), "♉ برج الثور"),
             ((5, 21), (6, 20), "♊ برج الجوزاء"), ((6, 21), (7, 22), "♋ برج السرطان"),
             ((7, 23), (8, 22), "♌ برج الأسد"), ((8, 23), (9, 22), "♍ برج العذراء"),
             ((9, 23), (10, 22), "♎ برج الميزان"), ((10, 23), (11, 21), "♏ برج العقرب"),
             ((11, 22), (12, 21), "♐ برج القوس")]
    for (sm, sd), (em, ed), name in signs:
        if (month == sm and day >= sd) or (month == em and day <= ed):
            return name
    return "♑ برج الجدي"


def get_season(month):
    if 3 <= month <= 5: return "ربيع 🌸"
    if 6 <= month <= 8: return "صيف ☀️"
    if 9 <= month <= 11: return "خريف 🍂"
    return "شتاء ❄️"


def get_generation(year):
    if year >= 2013: return "جيل ألفا"
    if year >= 1997: return "جيل Z"
    if year >= 1981: return "جيل الألفية"
    if year >= 1965: return "جيل X"
    if year >= 1946: return "جيل الطفرة السكانية"
    return "الجيل الصامت"


def get_president(year):
    if year >= 2014: return "عبد الفتاح السيسي"
    if year >= 2012: return "محمد مرسي"
    if year >= 2011: return "المجلس الأعلى للقوات المسلحة"
    if year >= 1981: return "حسني مبارك"
    if year >= 1970: return "أنور السادات"
    if year >= 1954: return "جمال عبد الناصر"
    if year >= 1952: return "محمد نجيب"
    return "الملك فاروق"


def analyze_national_id(id_num, full_name=""):
    id_num = id_num.strip()
    if not re.match(r'^\d{14}$', id_num):
        return "❌ الرقم لازم يكون <b>14 رقم</b> بالظبط"
    century_code = id_num[0]
    year_pair = int(id_num[1:3])
    month = int(id_num[3:5])
    day = int(id_num[5:7])
    gov_pair = id_num[7:9]
    serial = id_num[9:12]
    gender_digit = int(id_num[12])
    check_digit = id_num[13]
    if century_code == "2": century = 1900
    elif century_code == "3": century = 2000
    elif century_code == "4": century = 2100
    else: return "❌ رقم القرن غير مدعوم"
    birth_year = century + year_pair
    if not (1 <= month <= 12): return "❌ الشهر غير صالح"
    try: birth_date = datetime(birth_year, month, day)
    except: return "❌ تاريخ الميلاد غير صالح"
    gov_name = GOV_CODES.get(gov_pair)
    if not gov_name: return f"❌ كود المحافظة <code>{gov_pair}</code> غير معروف"
    gender = "أنثى ♀️" if gender_digit % 2 == 0 else "ذكر ♂️"
    today = datetime.now()
    age_years = today.year - birth_date.year
    age_months = today.month - birth_date.month
    age_days = today.day - birth_date.day
    if age_days < 0:
        age_months -= 1
        pm = today.month - 1 if today.month > 1 else 12
        py = today.year if today.month > 1 else today.year - 1
        age_days += calendar.monthrange(py, pm)[1]
    if age_months < 0:
        age_years -= 1
        age_months += 12
    total_days = (today - birth_date).days
    try: next_bd = datetime(today.year, month, day)
    except: next_bd = datetime(today.year, month, 28)
    if next_bd < today:
        try: next_bd = datetime(today.year + 1, month, day)
        except: next_bd = datetime(today.year + 1, month, 28)
    days_to_bd = (next_bd - today).days
    weekday = WEEKDAYS[birth_date.weekday()]
    zodiac = get_zodiac(month, day)
    chinese_zodiac = CHINESE_ZODIAC[(birth_year - 4) % 12]
    chinese_element = CHINESE_ELEMENTS[((birth_year - 4) % 10) // 2]
    season = get_season(month)
    generation = get_generation(birth_year)
    president = get_president(birth_year)
    stone = BIRTHSTONES[month - 1]
    flower = BIRTHFLOWERS[month - 1]
    lucky_color = LUCKY_COLORS[month - 1]
    digits = [int(d) for d in id_num]
    sum_digits = sum(digits)
    avg_digits = round(sum_digits / 14, 2)
    freq = Counter(digits)
    most_common = freq.most_common(1)[0]
    most_freq_str = f"رقم {most_common[0]} (تكرر {most_common[1]} مرة)"
    vote = "مؤهل ✅" if age_years >= 18 else "غير مؤهل ❌"
    marriage = "مؤهل ✅" if ("ذكر" in gender and age_years >= 21) or ("أنثى" in gender and age_years >= 18) else "غير مؤهل ❌"
    retirement_left = 60 - age_years
    retirement = f"متبقي {retirement_left} سنة" if retirement_left > 0 else "متقاعد ✅"
    age_status = "قاصر 👶" if age_years < 18 else ("بالغ 🧑" if age_years < 60 else "مسن 👴")
    name_line = f"\n👤 الاسم: <b>{full_name}</b>" if full_name else ""
    return (
        "🆔 <b>محلل الرقم القومي الشامل</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"<code>{id_num}</code>{name_line}\n━━━━━━━━━━━━━━━━━━\n\n"
        "📌 <b>البيانات الأساسية</b>\n"
        f"🎂 تاريخ الميلاد: <b>{day}/{month}/{birth_year}</b>\n"
        f"📅 اليوم: <b>{weekday}</b>\n"
        f"⏳ العمر: <b>{age_years} سنة، {age_months} شهر، {age_days} يوم</b>\n"
        f"📍 المحافظة: <b>{gov_name}</b>\n"
        f"⚧ النوع: <b>{gender}</b>\n"
        f"👥 الجيل: <b>{generation}</b>\n"
        f"🧬 الحالة: <b>{age_status}</b>\n\n"
        "🌟 <b>الأبراج والعناصر</b>\n"
        f"♈ البرج: <b>{zodiac}</b>\n"
        f"🐉 البرج الصيني: <b>{chinese_zodiac}</b>\n"
        f"⚡ العنصر: <b>{chinese_element}</b>\n"
        f"🍂 الفصل: <b>{season}</b>\n"
        f"💎 حجر الميلاد: <b>{stone}</b>\n"
        f"🌸 زهرة الميلاد: <b>{flower}</b>\n"
        f"🎨 لون الحظ: <b>{lucky_color}</b>\n\n"
        "⏰ <b>العمر بالتفصيل</b>\n"
        f"📆 أيام: <b>{total_days:,}</b>\n"
        f"🕐 ساعات: <b>{total_days * 24:,}</b>\n"
        f"🎉 متبقي لعيد الميلاد: <b>{days_to_bd} يوم</b>\n\n"
        "📊 <b>تحليلات رقمية</b>\n"
        f"➕ مجموع الأرقام: <b>{sum_digits}</b>\n"
        f"➗ المتوسط: <b>{avg_digits}</b>\n"
        f"🔢 الأكثر تكراراً: <b>{most_freq_str}</b>\n"
        f"🔢 التسلسل: <b>{serial}</b>\n"
        f"✔️ رقم التحقق: <b>{check_digit}</b>\n\n"
        "🏛️ <b>معلومات قانونية</b>\n"
        f"🗳️ الانتخابات: <b>{vote}</b>\n"
        f"💍 الزواج: <b>{marriage}</b>\n"
        f"👴 التقاعد: <b>{retirement}</b>\n"
        f"🏛️ الرئيس وقت الميلاد: <b>{president}</b>"
    )
