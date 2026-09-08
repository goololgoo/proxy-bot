import requests
import base64
import json
import urllib.parse
import os
import jdatetime
import pytz
import random
import time
import html
import re
import socket
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# تنظیمات ربات
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_USERNAME = "@goololgoo"

SOURCE_CHANNELS = [
    "persianvpnhub",
    "proxy_kafee",
    "daily_configs",
    "v2rayNG_Matsuri",
    "ConfigsHUB",
    "ConfigsHUB2",
    "proxy_mtm",
    "mehrosaboran",
    "makvaslim"
]

SOURCE_SUBS = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/refs/heads/main/top100.txt"
]

MTPROTO_CHANNELS = ["PinkProxy", "Myporoxy", "ProxyWR", "P500Y", "ProxyMTProto"]

CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"

MAX_V2RAY_POST = 5
MAX_MTPROTO_POST = 12
MAX_SUB_SIZE = 1000
BATCH_SIZE = 200

PREFERRED_COUNTRIES = {
    "NL", "DE", "FI", "FR", "SE", "GB", "PL", "IT", "ES", "BE",
    "AT", "CH", "NO", "DK", "CZ", "RO", "HU", "IE", "PT", "GR"
}
# ==========================================

SENT_IPS_FILE = "sent_ips.txt"
SUBSCRIPTION_FILE = "subscription.txt"

def to_persian_digits(text):
    mapping = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
    return text.translate(mapping)

def get_tehran_time():
    tz = pytz.timezone('Asia/Tehran')
    now = jdatetime.datetime.fromtimestamp(datetime.now(tz).timestamp(), tz)
    day = to_persian_digits(str(now.day))
    month = jdatetime.date.j_months_fa[now.month - 1]
    date_str = f"{day} {month}"
    hour = to_persian_digits(str(now.hour).zfill(2))
    minute = to_persian_digits(str(now.minute).zfill(2))
    time_str = f"{hour}:{minute}"
    return date_str, time_str

def get_sent_ips():
    if not os.path.exists(SENT_IPS_FILE):
        return set()
    with open(SENT_IPS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_sent_ips(ip_set):
    with open(SENT_IPS_FILE, "w") as f:
        for ip_port in sorted(ip_set):
            f.write(f"{ip_port}\n")

def load_subscription():
    if not os.path.exists(SUBSCRIPTION_FILE):
        return []
    with open(SUBSCRIPTION_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_subscription(configs):
    configs = configs[-MAX_SUB_SIZE:]
    with open(SUBSCRIPTION_FILE, "w", encoding="utf-8") as f:
        for cfg in configs:
            f.write(cfg + "\n")
    print(f"✅ ساب ذخیره شد. تعداد: {len(configs)}")

def is_valid_config(config: str) -> bool:
    if not config or not isinstance(config, str):
        return False
    config = config.strip()
    return config.startswith(("vless://", "vmess://", "trojan://", "ss://"))

def extract_ip_port(config):
    try:
        if config.startswith("vmess://"):
            b64_str = config.replace("vmess://", "")
            b64_str += '=' * (-len(b64_str) % 4)
            json_data = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            return json_data.get("add", ""), str(json_data.get("port", ""))
        elif config.startswith(("vless://", "trojan://", "ss://")):
            match = re.search(r'@([^:]+):(\d+)', config)
            if match:
                return match.group(1), match.group(2)
        elif "tg://proxy" in config or "https://t.me/proxy" in config:
            ip_match = re.search(r'server=([^&]+)', config)
            port_match = re.search(r'port=(\d+)', config)
            if ip_match and port_match:
                return ip_match.group(1), port_match.group(1)
    except:
        pass
    return None, None

def check_port(ip, port, timeout=4.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def get_country_and_flag(ip_list):
    result = {}
    valid_ips = [ip for ip in ip_list if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip)]
    if not valid_ips:
        return {ip: {"code": "", "flag": "🌐"} for ip in ip_list}

    try:
        payload = [{"query": ip, "fields": "query,countryCode"} for ip in valid_ips]
        res = requests.post("http://ip-api.com/batch", json=payload, timeout=12).json()
        for item in res:
            ip = item.get("query")
            code = item.get("countryCode", "") or ""
            if len(code) == 2:
                flag = chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))
            else:
                flag = "🌐"
            result[ip] = {"code": code, "flag": flag}
    except:
        pass

    for ip in ip_list:
        if ip not in result:
            result[ip] = {"code": "", "flag": "🌐"}
    return result

def change_remark_v2ray(config, new_remark):
    try:
        if config.startswith("vmess://"):
            b64_str = config.replace("vmess://", "")
            b64_str += '=' * (-len(b64_str) % 4)
            json_data = json.loads(base64.b64decode(b64_str).decode('utf-8'))
            json_data["ps"] = new_remark
            new_b64 = base64.b64encode(json.dumps(json_data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
            return f"vmess://{new_b64}"
        elif config.startswith(("vless://", "trojan://", "ss://")):
            base_url = config.split("#")[0] if "#" in config else config
            encoded_remark = urllib.parse.quote(new_remark)
            return f"{base_url}#{encoded_remark}"
        return config
    except:
        return config

def change_remark_mtproto(link, new_remark):
    clean_link = re.sub(r'&name=[^&]*', '', link)
    return f"{clean_link}&name={urllib.parse.quote(new_remark)}"

def test_single_config(config, sent_ips):
    if not is_valid_config(config):
        return None
    ip, port = extract_ip_port(config)
    if not ip or not port:
        return None
    ip_port_str = f"{ip}:{port}"
    is_new = ip_port_str not in sent_ips
    if check_port(ip, port):
        return {"config": config, "ip_port": ip_port_str, "is_new": is_new, "ip": ip}
    return None

def get_random_header_footer(post_type, date_str, time_str):
    if post_type == "v2ray":
        headers = [
            f"""⚡️ کانفیگ‌های تازه و تست‌شده

آخرین به‌روزرسانی: {date_str} ساعت {time_str}
✅ تست شده و فعال
مناسب اینستاگرام، یوتیوب و دانلود
پشتیبانی از همراه اول، ایرانسل و رایتل

برنامه‌های پیشنهادی: MahsaNG • Hiddify • V2rayNG
با یک ضربه کپی می‌شود 👇
""",
            f"""🚀 ۵ کانفیگ جدید و پایدار

تاریخ: {date_str} | ساعت {time_str}
تست شده روی اپراتورهای مختلف
سرعت خوب و اتصال پایدار

پیشنهاد ما: اول MahsaNG را امتحان کنید
""",
            f"""🔥 کانفیگ‌های امروز آماده شد

به‌روزرسانی: {date_str} ساعت {time_str}
مناسب تمام اپراتورها
تست شده و فعال ✅

برنامه مورد نیاز: Hiddify یا MahsaNG
"""
        ]
        footers = [
            """
روی کدام اپراتور وصل شدی؟
همراه اول ✅  ایرانسل ✅  رایتل ✅

اگر سرعت خوبی داشت برای دوستانت بفرست
نظراتت رو بنویس 👇

#v2ray #فیلترشکن #پروکسی #MahsaNG #Hiddify
@goololgoo
@goololgoo_group
""",
            """
کدام کانفیگ بهتر کار کرد؟
تجربه‌ات رو در نظرات بنویس

برای دانلود آخرین نسخه برنامه‌ها به پست پین‌شده سر بزن

#v2ray #فیلترشکن #اینترنت_آزاد #ایرانسل #همراه‌اول
@goololgoo
""",
            """
اگر قطع شد سریع کانفیگ بعدی رو تست کن
سوالی داشتی تو گروه بپرس

با دوستات به اشتراک بگذار ♻️

#پروکسی #فیلترشکن #v2rayNG #اینترنت_مجانی
@goololgoo
@goololgoo_group
"""
        ]
    else:
        headers = [
            f"""☄ پروکسی‌های جدید تلگرام

آخرین به‌روزرسانی: {date_str} ساعت {time_str}
تست شده و فعال ✅
مناسب تمام اپراتورها

برای اتصال روی لینک مورد نظر کلیک کنید 👇
""",
            f"""🚀 پروکسی MTProto تازه

تاریخ: {date_str} | {time_str}
تست شده روی همراه اول، ایرانسل و رایتل
اتصال سریع و پایدار

روی لینک بزن تا وصل بشی
""",
            f"""🔥 پروکسی‌های امروز آماده شد

به‌روزرسانی: {date_str} ساعت {time_str}
مناسب دور زدن فیلتر تلگرام
تست شده و فعال ✅
"""
        ]
        footers = [
            """
روی کدوم اپراتور وصل شدی؟ بگو 👇

اگر خوب کار کرد برای بقیه هم بفرست

#MTProto #پروکسی_تلگرام #فیلترشکن #تلگرام
@goololgoo
@goololgoo_group
""",
            """
کدام پروکسی بهتر بود؟
نظراتت مهمه

سوالی داشتی تو گروه مطرح کن

#پروکسی #تلگرام #ایرانسل #همراه‌اول #MTProto
@goololgoo
""",
            """
اگر قطع شد پروکسی بعدی رو تست کن
با دوستات به اشتراک بگذار ♻️

#فیلترشکن #پروکسی_تلگرام #v2ray #اینترنت_آزاد
@goololgoo
@goololgoo_group
"""
        ]
    return random.choice(headers), random.choice(footers)

def send_post(configs_to_post, post_type):
    date_str, time_str = get_tehran_time()
    header, footer = get_random_header_footer(post_type, date_str, time_str)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    if post_type == "v2ray":
        all_configs_str = "\n\n".join(configs_to_post)
        safe_configs_str = all_configs_str.replace("<", "&lt;").replace(">", "&gt;")
        configs_text = f"<pre>{safe_configs_str}</pre>"
        full_message = header + configs_text + footer
    else:
        links_html = [f'<a href="{html.escape(cfg)}">🚀 Proxy {i}</a>' for i, cfg in enumerate(configs_to_post, 1)]
        rows = ["  |  ".join(links_html[i:i+3]) for i in range(0, len(links_html), 3)]
        configs_text = "\n\n".join(rows)
        full_message = header + configs_text + footer

    payload = {
        "chat_id": CHANNEL_USERNAME,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            print(f"✅ {len(configs_to_post)} کانفیگ {post_type} با موفقیت پست شد.")
        else:
            print(f"❌ خطا در ارسال {post_type}: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"❌ Error sending {post_type}: {e}")

def collect_from_channel(channel):
    found = []
    tg_url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(tg_url, timeout=15)
        if resp.status_code != 200:
            print(f"  ⚠️ وضعیت پاسخ {resp.status_code} برای @{channel}")
            return found

        soup = BeautifulSoup(resp.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')[-30:]
        pattern = r'(?:^|[\s\n\r\"\'>]|\d+\.\s*)((?:vless|vmess|trojan|ss)://[^\s<>"\']+)'

        for msg in messages:
            # 1. متن کامل پیام (شامل quote و collapse)
            full_text = msg.get_text(separator="\n")
            matches = re.findall(pattern, full_text, flags=re.IGNORECASE | re.MULTILINE)
            found.extend(matches)

            # 2. داخل تگ‌های code و pre
            for tag in msg.find_all(['code', 'pre']):
                code_text = tag.get_text()
                matches = re.findall(pattern, code_text, flags=re.IGNORECASE | re.MULTILINE)
                found.extend(matches)

            # 3. لینک‌های مستقیم
            for a in msg.find_all('a', href=True):
                href = a.get('href', '')
                if any(href.lower().startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://")):
                    found.append(href)

            # 4. خود HTML خام
            raw_html = str(msg)
            matches = re.findall(pattern, raw_html, flags=re.IGNORECASE | re.MULTILINE)
            found.extend(matches)

    except Exception as e:
        print(f"خطا در کانال {channel}: {e}")

    cleaned = []
    for item in found:
        item = item.strip().strip('"').strip("'")
        if is_valid_config(item):
            cleaned.append(item)

    return list(dict.fromkeys(cleaned))

def collect_from_sub(url):
    found = []
    try:
        resp = requests.get(url, timeout=20)
        content = resp.text.strip()
        try:
            decoded = base64.b64decode(content).decode('utf-8')
            lines = decoded.splitlines()
        except:
            lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if is_valid_config(line):
                found.append(line)
    except Exception as e:
        print(f"خطا در دریافت ساب {url}: {e}")
    return found

def update_subscription():
    print("\n" + "="*50)
    print("مرحله ۱: ساخت / به‌روزرسانی ساب")
    print("="*50)

    all_configs = []
    seen = set()

    for ch in SOURCE_CHANNELS:
        print(f"→ در حال دریافت از کانال @{ch} ...")
        configs = collect_from_channel(ch)
        added = 0
        for cfg in configs:
            if is_valid_config(cfg):
                ip, port = extract_ip_port(cfg)
                key = f"{ip}:{port}" if ip else cfg[:80]
                if key not in seen:
                    seen.add(key)
                    modified = change_remark_v2ray(cfg, CUSTOM_REMARK)
                    all_configs.append(modified)
                    added += 1
        print(f"  پیدا شد: {len(configs)} | اضافه شد: {added}")

    for sub_url in SOURCE_SUBS:
        print(f"→ در حال دریافت از لینک ساب ...")
        configs = collect_from_sub(sub_url)
        added = 0
        for cfg in configs:
            if is_valid_config(cfg):
                ip, port = extract_ip_port(cfg)
                key = f"{ip}:{port}" if ip else cfg[:80]
                if key not in seen:
                    seen.add(key)
                    modified = change_remark_v2ray(cfg, CUSTOM_REMARK)
                    all_configs.append(modified)
                    added += 1
        print(f"  پیدا شد: {len(configs)} | اضافه شد: {added}")

    old_sub = load_subscription()
    kept = 0
    for cfg in old_sub:
        ip, port = extract_ip_port(cfg)
        key = f"{ip}:{port}" if ip else cfg[:80]
        if key not in seen:
            seen.add(key)
            all_configs.append(cfg)
            kept += 1
    print(f"→ از ساب قبلی نگه داشته شد: {kept}")

    if len(all_configs) > MAX_SUB_SIZE:
        all_configs = all_configs[-MAX_SUB_SIZE:]

    save_subscription(all_configs)
    return all_configs

def get_v2ray_from_sub(sent_ips):
    print("\n" + "="*50)
    print("مرحله ۲: انتخاب ۵ کانفیگ از ساب (اولویت اروپا)")
    print("="*50)

    sub_configs = load_subscription()
    if not sub_configs:
        print("❌ ساب خالی است.")
        return []

    print(f"تعداد کانفیگ در ساب: {len(sub_configs)}")
    random.shuffle(sub_configs)

    candidates = []
    used_ips = set()
    target_candidates = 20

    for i in range(0, len(sub_configs), BATCH_SIZE):
        batch = sub_configs[i:i + BATCH_SIZE]
        print(f"در حال تست دسته {i // BATCH_SIZE + 1} ({len(batch)} کانفیگ)...")
        with ThreadPoolExecutor(max_workers=40) as executor:
            futures = {executor.submit(test_single_config, cfg, sent_ips): cfg for cfg in batch}
            for future in as_completed(futures):
                result = future.result()
                if result and result["ip_port"] not in used_ips:
                    candidates.append(result)
                    used_ips.add(result["ip_port"])
                    if len(candidates) >= target_candidates:
                        break
        if len(candidates) >= target_candidates:
            break

    print(f"تعداد کاندیدای سالم: {len(candidates)}")
    if not candidates:
        return []

    ips = [c["ip"] for c in candidates]
    country_info = get_country_and_flag(ips)

    europe = []
    others = []
    for c in candidates:
        code = country_info.get(c["ip"], {}).get("code", "")
        c["country_code"] = code
        c["flag"] = country_info.get(c["ip"], {}).get("flag", "🌐")
        if code in PREFERRED_COUNTRIES:
            europe.append(c)
        else:
            others.append(c)

    print(f"اروپایی: {len(europe)} | بقیه: {len(others)}")

    selected = europe[:MAX_V2RAY_POST]
    if len(selected) < MAX_V2RAY_POST:
        needed = MAX_V2RAY_POST - len(selected)
        selected.extend(others[:needed])

    print(f"نهایی انتخاب شده: {len(selected)} (اولویت با اروپا)")
    return selected

def get_mtproto_proxies(sent_ips):
    print("\n" + "="*50)
    print("مرحله ۳: دریافت پروکسی‌های MTProto")
    print("="*50)

    found = []
    for src_chan in MTPROTO_CHANNELS:
        tg_url = f"https://t.me/s/{src_chan}"
        try:
            resp = requests.get(tg_url, timeout=12)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message')[-8:]
            for msg in messages:
                text_div = msg.find('div', class_='tgme_widget_message_text')
                if text_div:
                    matches = re.findall(r'(https://t\.me/proxy\?[^\s<>"\']+|tg://proxy\?[^\s<>"\']+)', text_div.get_text())
                    found.extend(matches)
                for btn in msg.find_all('a', href=True):
                    href = btn['href']
                    if "tg://proxy" in href or "https://t.me/proxy" in href:
                        found.append(href)
        except Exception as e:
            print(f"خطا در کانال {src_chan}: {e}")
            continue

    unique = list(dict.fromkeys(found))
    print(f"تعداد پروکسی یکتا: {len(unique)}")

    new_proxies = []
    old_proxies = []
    for proxy in unique:
        ip, port = extract_ip_port(proxy)
        if not ip:
            continue
        ip_port = f"{ip}:{port}"
        if ip_port not in sent_ips:
            new_proxies.append(proxy)
        else:
            old_proxies.append(proxy)

    selected = new_proxies[:MAX_MTPROTO_POST]
    if len(selected) < MAX_MTPROTO_POST:
        selected.extend(old_proxies[:MAX_MTPROTO_POST - len(selected)])
    if len(selected) < MAX_MTPROTO_POST:
        remaining = [p for p in unique if p not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:MAX_MTPROTO_POST - len(selected)])
    return selected[:MAX_MTPROTO_POST]

def main():
    delay = random.randint(40, 160)
    print(f"ربات برای طبیعی بودن {delay} ثانیه صبر می‌کند...")
    time.sleep(delay)

    sent_ips = get_sent_ips()
    print(f"تعداد IPهای ذخیره‌شده قبلی: {len(sent_ips)}")

    update_subscription()

    v2ray_results = get_v2ray_from_sub(sent_ips)

    if v2ray_results:
        configs_to_post = []
        for item in v2ray_results:
            flag = item.get("flag", "🌐")
            modified = change_remark_v2ray(item["config"], f"{flag} {CUSTOM_REMARK}")
            configs_to_post.append(modified)
            sent_ips.add(item["ip_port"])
        send_post(configs_to_post, "v2ray")
    else:
        print("هیچ کانفیگ V2Ray زنده‌ای پیدا نشد.")

    between_delay = random.randint(180, 720)
    print(f"\n⏳ فاصله رندم بین دو پست: {between_delay // 60} دقیقه و {between_delay % 60} ثانیه...")
    time.sleep(between_delay)

    mt_proxies = get_mtproto_proxies(sent_ips)
    if mt_proxies:
        all_ips = []
        for proxy in mt_proxies:
            ip, _ = extract_ip_port(proxy)
            if ip:
                all_ips.append(ip)
        country_info = get_country_and_flag(all_ips)
        configs_to_post = []
        for proxy in mt_proxies:
            ip, port = extract_ip_port(proxy)
            flag = country_info.get(ip, {}).get("flag", "🌐") if ip else "🌐"
            modified = change_remark_mtproto(proxy, f"{flag} {CUSTOM_REMARK}")
            configs_to_post.append(modified)
            if ip and port:
                sent_ips.add(f"{ip}:{port}")
        send_post(configs_to_post, "mtproto")
    else:
        print("هیچ پروکسی MTProto پیدا نشد.")

    save_sent_ips(sent_ips)
    print(f"\n✅ کار تمام شد. تعداد IPهای ثبت‌شده: {len(sent_ips)}")

if __name__ == "__main__":
    main()
