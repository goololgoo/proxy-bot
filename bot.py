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
from datetime import datetime
from bs4 import BeautifulSoup


# ==========================================
# تنظیمات ربات
# ==========================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_USERNAME = "@goololgoo"

SOURCE_CHANNELS = [
    "persianvpnhub",
    "proxy_kafee",
    "daily_configs",
    "v2rayNG_Matsuri",
    "ConfigsHUB",
    "FreakConfig",
    "Capoit",
    "meliproxyy",
    "prrofile_purple",
    "proxy_mtm",
    "mehrosaboran"
]

SOURCE_SUBS = [
    "https://raw.githubusercontent.com/0xRadikal/Free-v2ray-Configs/refs/heads/main/top100.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs_tested.txt",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/mix/sub.html",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_BASE64.txt"
]

MTPROTO_CHANNELS = [
    "PinkProxy",
    "Myporoxy",
    "ProxyWR",
    "P500Y",
    "ProxyMTProto",
    "webproxy"
]

CUSTOM_REMARK = "@goololgoo 🔐 وی‌پی‌ان رایگان | Free Proxy💥"

MAX_V2RAY_POST = 5
MAX_MTPROTO_POST = 12
MAX_SUB_SIZE = 1000

PREFERRED_COUNTRIES = {
    "NL", "DE", "FI", "FR", "SE", "GB", "PL", "IT", "ES", "BE",
    "AT", "CH", "NO", "DK", "CZ", "RO", "HU", "IE", "PT", "GR"
}

SENT_IPS_FILE = "sent_ips.txt"
SUBSCRIPTION_FILE = "subscription.txt"


# ==========================================
# تاریخ و زمان
# ==========================================

def to_persian_digits(text):
    mapping = str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    )
    return text.translate(mapping)


def get_tehran_time():
    tz = pytz.timezone("Asia/Tehran")

    now = jdatetime.datetime.fromtimestamp(
        datetime.now(tz).timestamp(),
        tz
    )

    day = to_persian_digits(str(now.day))
    month = jdatetime.date.j_months_fa[now.month - 1]

    date_str = f"{day} {month}"

    hour = to_persian_digits(
        str(now.hour).zfill(2)
    )

    minute = to_persian_digits(
        str(now.minute).zfill(2)
    )

    time_str = f"{hour}:{minute}"

    return date_str, time_str


# ==========================================
# مدیریت IPهای ارسال‌شده
# ==========================================

def get_sent_ips():

    if not os.path.exists(SENT_IPS_FILE):
        return set()

    try:
        with open(
            SENT_IPS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return {
                line.strip()
                for line in f
                if line.strip()
            }

    except Exception:
        return set()


def save_sent_ips(ip_set):

    try:
        with open(
            SENT_IPS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            for ip_port in sorted(ip_set):
                f.write(f"{ip_port}\n")

    except Exception as e:

        print(
            f"⚠️ خطا در ذخیره IPها: {e}"
        )


# ==========================================
# مدیریت Subscription
# ==========================================

def load_subscription():

    if not os.path.exists(SUBSCRIPTION_FILE):
        return []

    try:

        with open(
            SUBSCRIPTION_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return [
                line.strip()
                for line in f
                if line.strip()
            ]

    except Exception as e:

        print(
            f"⚠️ خطا در خواندن Subscription: {e}"
        )

        return []


def save_subscription(configs):

    configs = configs[:MAX_SUB_SIZE]

    try:

        with open(
            SUBSCRIPTION_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            for cfg in configs:
                f.write(cfg + "\n")

        print(
            f"✅ ساب ذخیره شد. تعداد: {len(configs)}"
        )

    except Exception as e:

        print(
            f"❌ خطا در ذخیره Subscription: {e}"
        )


# ==========================================
# تشخیص پروتکل
# ==========================================

def get_protocol(config):

    if not config:
        return ""

    config = config.strip().lower()

    for protocol in (
        "vless",
        "vmess",
        "hysteria2",
        "trojan",
        "ss"
    ):

        if config.startswith(protocol + "://"):
            return protocol

    return ""


def is_valid_config(config: str) -> bool:

    return bool(get_protocol(config))


# ==========================================
# Base64 Decode
# ==========================================

def decode_base64_text(value):

    value = value.strip()

    if not value:
        return ""

    # حذف فاصله و newline
    value = re.sub(
        r"\s+",
        "",
        value
    )

    # Base64 معمولی
    padded = value + "=" * (
        -len(value) % 4
    )

    try:

        decoded = base64.b64decode(
            padded
        ).decode(
            "utf-8",
            errors="ignore"
        )

        if decoded:
            return decoded

    except Exception:
        pass

    # Base64 URL Safe
    try:

        decoded = base64.urlsafe_b64decode(
            padded
        ).decode(
            "utf-8",
            errors="ignore"
        )

        if decoded:
            return decoded

    except Exception:
        pass

    return ""


# ==========================================
# استخراج IP و Port
# ==========================================

def extract_ip_port(config):

    if not config:
        return None, None

    try:

        config = config.strip()

        protocol = get_protocol(config)

        # ----------------------------------
        # VMess
        # ----------------------------------

        if protocol == "vmess":

            b64_str = config[
                len("vmess://"):
            ]

            decoded = decode_base64_text(
                b64_str
            )

            if not decoded:
                return None, None

            json_data = json.loads(
                decoded
            )

            address = str(
                json_data.get(
                    "add",
                    ""
                )
            ).strip()

            port = str(
                json_data.get(
                    "port",
                    ""
                )
            ).strip()

            if address and port:
                return address, port

            return None, None

        # ----------------------------------
        # MTProto
        # ----------------------------------

        if (
            "tg://proxy" in config
            or "https://t.me/proxy" in config
            or "https://t.me/webproxy" in config
            or "tg://webproxy" in config
        ):

            parsed = urllib.parse.urlparse(
                config
            )

            query = urllib.parse.parse_qs(
                parsed.query
            )

            server = query.get(
                "server",
                [""]
            )[0]

            port = query.get(
                "port",
                [""]
            )[0]

            if server and port:
                return server, str(port)

            return None, None

        # ----------------------------------
        # VLESS / Trojan / Hysteria2
        # ----------------------------------

        if protocol in (
            "vless",
            "trojan",
            "hysteria2"
        ):

            parsed = urllib.parse.urlparse(
                config
            )

            hostname = parsed.hostname
            port = parsed.port

            if hostname and port:
                return hostname, str(port)

            # fallback
            match = re.search(
                r"@\[([0-9a-fA-F:]+)\]:(\d+)",
                config
            )

            if match:

                return (
                    match.group(1),
                    match.group(2)
                )

            match = re.search(
                r"@([^:/?#]+):(\d+)",
                config
            )

            if match:

                return (
                    match.group(1),
                    match.group(2)
                )

            return None, None

        # ----------------------------------
        # SS
        # ----------------------------------

        if protocol == "ss":

            # حالت معمول:
            # ss://base64@host:port
            after_scheme = config[
                len("ss://"):
            ]

            if "@" in after_scheme:

                user_part, server_part = (
                    after_scheme.rsplit(
                        "@",
                        1
                    )
                )

                server_part = server_part.split(
                    "?",
                    1
                )[0]

                server_part = server_part.split(
                    "#",
                    1
                )[0]

                # IPv6
                match = re.match(
                    r"^\[([0-9a-fA-F:]+)\]:(\d+)",
                    server_part
                )

                if match:

                    return (
                        match.group(1),
                        match.group(2)
                    )

                # IPv4 / domain
                match = re.match(
                    r"^([^:]+):(\d+)",
                    server_part
                )

                if match:

                    return (
                        match.group(1),
                        match.group(2)
                    )

            # SS قدیمی به شکل Base64 کامل باشد
            decoded = decode_base64_text(
                after_scheme
            )

            if decoded and "@" in decoded:

                match = re.search(
                    r"@([^:/?#]+):(\d+)",
                    decoded
                )

                if match:

                    return (
                        match.group(1),
                        match.group(2)
                    )

            return None, None

    except Exception:
        pass

    return None, None


# ==========================================
# ساخت کلید یکتا
# ==========================================

def get_config_key(config):

    ip, port = extract_ip_port(
        config
    )

    if ip and port:

        return (
            f"{ip.strip().lower()}:"
            f"{str(port).strip()}"
        )

    # اگر نتوانستیم IP/Port استخراج کنیم
    # خود کانفیگ کلید می‌شود
    return (
        config.strip()
        .lower()
    )


# ==========================================
# استخراج پرچم از Remark
# ==========================================

def get_flag_from_remark(config):

    try:

        remark = ""

        protocol = get_protocol(config)

        # VMess
        if protocol == "vmess":

            b64_str = config[
                len("vmess://"):
            ]

            decoded = decode_base64_text(
                b64_str
            )

            if decoded:

                json_data = json.loads(
                    decoded
                )

                remark = json_data.get(
                    "ps",
                    ""
                )

        # سایر پروتکل‌ها
        elif "#" in config:

            remark = urllib.parse.unquote(
                config.split(
                    "#",
                    1
                )[1]
            )

        match = re.match(
            r"^([\U0001F1E6-\U0001F1FF]{2}|🌐)",
            remark
        )

        return (
            match.group(1)
            if match
            else ""
        )

    except Exception:
        return ""


# ==========================================
# دریافت کشور و پرچم IP
# ==========================================

def get_country_and_flag(ip_list):

    result = {}

    # حذف تکراری‌ها
    ip_list = list(
        dict.fromkeys(
            ip_list
        )
    )

    valid_ips = [
        ip
        for ip in ip_list
        if ip
        and re.match(
            r"^\d{1,3}\."
            r"\d{1,3}\."
            r"\d{1,3}\."
            r"\d{1,3}$",
            ip
        )
    ]

    # برای دامنه‌ها
    for ip in ip_list:

        if ip not in valid_ips:

            result[ip] = {
                "code": "",
                "flag": "🌐"
            }

    if not valid_ips:
        return result

    for j in range(
        0,
        len(valid_ips),
        100
    ):

        chunk = valid_ips[
            j:j + 100
        ]

        try:

            payload = [
                {
                    "query": ip,
                    "fields": "query,countryCode"
                }
                for ip in chunk
            ]

            response = requests.post(
                "http://ip-api.com/batch",
                json=payload,
                timeout=12
            )

            if response.status_code != 200:

                print(
                    f"  ⚠️ ip-api status: "
                    f"{response.status_code}"
                )

                continue

            data = response.json()

            for item in data:

                ip = item.get(
                    "query",
                    ""
                )

                code = (
                    item.get(
                        "countryCode",
                        ""
                    )
                    or ""
                ).upper()

                if len(code) == 2:

                    flag = (
                        chr(
                            0x1F1E6
                            + ord(code[0])
                            - ord("A")
                        )
                        +
                        chr(
                            0x1F1E6
                            + ord(code[1])
                            - ord("A")
                        )
                    )

                else:

                    flag = "🌐"

                result[ip] = {
                    "code": code,
                    "flag": flag
                }

        except Exception as e:

            print(
                f"  ⚠️ خطا در دریافت پرچم: {e}"
            )

    for ip in ip_list:

        if ip not in result:

            result[ip] = {
                "code": "",
                "flag": "🌐"
            }

    return result


# ==========================================
# تغییر Remark V2Ray
# ==========================================

def change_remark_v2ray(
    config,
    new_remark
):

    try:

        protocol = get_protocol(config)

        # ----------------------------------
        # VMess
        # ----------------------------------

        if protocol == "vmess":

            b64_str = config[
                len("vmess://"):
            ]

            decoded = decode_base64_text(
                b64_str
            )

            if not decoded:
                return config

            json_data = json.loads(
                decoded
            )

            json_data["ps"] = new_remark

            new_b64 = base64.b64encode(
                json.dumps(
                    json_data,
                    ensure_ascii=False,
                    separators=(
                        ",",
                        ":"
                    )
                ).encode(
                    "utf-8"
                )
            ).decode(
                "utf-8"
            )

            return (
                f"vmess://{new_b64}"
            )

        # ----------------------------------
        # VLESS / Trojan / SS / Hysteria2
        # ----------------------------------

        if protocol in (
            "vless",
            "trojan",
            "ss",
            "hysteria2"
        ):

            base_url = config.split(
                "#",
                1
            )[0]

            encoded_remark = urllib.parse.quote(
                new_remark,
                safe=""
            )

            return (
                f"{base_url}"
                f"#{encoded_remark}"
            )

        return config

    except Exception as e:

        print(
            f"⚠️ خطا در تغییر Remark: {e}"
        )

        return config


# ==========================================
# تغییر Remark MTProto
# ==========================================

def change_remark_mtproto(
    link,
    new_remark
):

    try:

        clean_link = re.sub(
            r"&name=[^&]*",
            "",
            link
        )

        separator = (
            "&"
            if "?" in clean_link
            else "?"
        )

        return (
            f"{clean_link}"
            f"{separator}name="
            f"{urllib.parse.quote(new_remark)}"
        )

    except Exception:
        return link


# ==========================================
# متن پست
# ==========================================

def get_random_header_footer(
    post_type,
    date_str,
    time_str
):

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

            f"""☄  webproxy . mtporoto پروکسی‌های جدید تلگرام

آخرین به‌روزرسانی: {date_str} ساعت {time_str}
تست شده و فعال ✅
مناسب تمام اپراتورها

برای اتصال روی لینک مورد نظر کلیک کنید 👇
""",

            f"""🚀 پروکسی webproxy . mtporoto تازه

تاریخ: {date_str} | {time_str}
تست شده روی همراه اول، ایرانسل و رایتل
اتصال سریع و پایدار

روی لینک بزن تا وصل بشی
""",

            f"""🔥 پروکسی‌های webproxy . mtporoto امروز آماده شد

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

    return (
        random.choice(headers),
        random.choice(footers)
    )


# ==========================================
# ارسال پست
# ==========================================

def send_post(
    configs_to_post,
    post_type
):

    date_str, time_str = get_tehran_time()

    header, footer = get_random_header_footer(
        post_type,
        date_str,
        time_str
    )

    url = (
        f"https://api.telegram.org/bot"
        f"{BOT_TOKEN}/sendMessage"
    )

    if post_type == "v2ray":

        all_configs_str = "\n\n".join(
            configs_to_post
        )

        safe_configs_str = (
            all_configs_str
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        configs_text = (
            f"<pre>{safe_configs_str}</pre>"
        )

        full_message = (
            header
            + configs_text
            + footer
        )

    else:

        links_html = [
            f'<a href="{html.escape(cfg)}">'
            f'🚀 Proxy {i}</a>'
            for i, cfg
            in enumerate(
                configs_to_post,
                1
            )
        ]

        rows = [
            "  |  ".join(
                links_html[i:i + 3]
            )
            for i in range(
                0,
                len(links_html),
                3
            )
        ]

        configs_text = "\n\n".join(
            rows
        )

        full_message = (
            header
            + configs_text
            + footer
        )

    payload = {
        "chat_id": CHANNEL_USERNAME,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:

        r = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if r.status_code == 200:

            print(
                f"✅ {len(configs_to_post)} "
                f"کانفیگ {post_type} "
                f"با موفقیت پست شد."
            )

            return True

        print(
            f"❌ خطا در ارسال {post_type}: "
            f"{r.status_code} - "
            f"{r.text[:300]}"
        )

        return False

    except Exception as e:

        print(
            f"❌ Error sending {post_type}: {e}"
        )

        return False


# ==========================================
# Regex استخراج کانفیگ
# ==========================================

CONFIG_PATTERN = re.compile(
    r"(?:vless|vmess|trojan|ss|hysteria2)"
    r"://[^\s<>'\"`]+",
    re.IGNORECASE
)


def extract_configs_from_text(text):

    if not text:
        return []

    found = []

    matches = CONFIG_PATTERN.findall(
        text
    )

    found.extend(matches)

    return found


# ==========================================
# جمع‌آوری کانفیگ از کانال تلگرام
# ==========================================

def collect_from_channel(channel):

    found = []

    tg_url = (
        f"https://t.me/s/{channel}"
    )

    try:

        resp = requests.get(
            tg_url,
            timeout=15,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        if resp.status_code != 200:

            print(
                f"  ⚠️ وضعیت پاسخ "
                f"{resp.status_code} "
                f"برای @{channel}"
            )

            return []

        soup = BeautifulSoup(
            resp.text,
            "html.parser"
        )

        messages = soup.find_all(
            "div",
            class_="tgme_widget_message"
        )[-30:]

        for msg in messages:

            # متن پیام
            full_text = msg.get_text(
                separator="\n"
            )

            found.extend(
                extract_configs_from_text(
                    full_text
                )
            )

            # code / pre
            for tag in msg.find_all(
                ["code", "pre"]
            ):

                found.extend(
                    extract_configs_from_text(
                        tag.get_text()
                    )
                )

            # لینک مستقیم
            for a in msg.find_all(
                "a",
                href=True
            ):

                href = a.get(
                    "href",
                    ""
                ).strip()

                if is_valid_config(href):

                    found.append(
                        href
                    )

            # HTML خام
            raw_html = str(msg)

            found.extend(
                extract_configs_from_text(
                    raw_html
                )
            )

    except Exception as e:

        print(
            f"  ❌ خطا در کانال @{channel}: {e}"
        )

        return []

    # ----------------------------------
    # پاکسازی
    # ----------------------------------

    cleaned = []

    seen = set()

    for item in found:

        item = (
            item.strip()
            .strip("\"'")
            .strip()
            .rstrip(
                ".,;،؛)>"
            )
        )

        if not is_valid_config(item):
            continue

        key = get_config_key(
            item
        )

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(
            item
        )

    return cleaned


# ==========================================
# دریافت Subscription
# ==========================================

def collect_from_sub(url):

    found = []

    try:

        resp = requests.get(
            url,
            timeout=25,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        if resp.status_code != 200:

            print(
                f"  ⚠️ وضعیت ساب: "
                f"{resp.status_code}"
            )

            return []

        content = resp.text.strip()

        # ----------------------------------
        # اول متن خام
        # ----------------------------------

        found.extend(
            extract_configs_from_text(
                content
            )
        )

        # ----------------------------------
        # تلاش برای Base64
        # ----------------------------------

        decoded = decode_base64_text(
            content
        )

        if decoded:

            found.extend(
                extract_configs_from_text(
                    decoded
                )
            )

            # خطوط جداگانه
            for line in decoded.splitlines():

                line = line.strip()

                if is_valid_config(line):

                    found.append(
                        line
                    )

        # ----------------------------------
        # خطوط متن خام
        # ----------------------------------

        for line in content.splitlines():

            line = line.strip()

            if is_valid_config(line):

                found.append(
                    line
                )

        # ----------------------------------
        # HTML
        # ----------------------------------

        if "<html" in content.lower():

            soup = BeautifulSoup(
                content,
                "html.parser"
            )

            text = soup.get_text(
                separator="\n"
            )

            found.extend(
                extract_configs_from_text(
                    text
                )
            )
            for a in soup.find_all(
                "a",
                href=True
            ):

                href = a.get(
                    "href",
                    ""
                ).strip()

                if is_valid_config(href):

                    found.append(
                        href
                    )

    except Exception as e:

        print(
            f"  ❌ خطا در دریافت ساب: {e}"
        )

        return []

    # ----------------------------------
    # پاکسازی و Dedup
    # ----------------------------------

    cleaned = []

    seen = set()

    for cfg in found:

        cfg = (
            cfg.strip()
            .strip("\"'")
            .rstrip(
                ".,;،؛)>"
            )
        )

        if not is_valid_config(cfg):
            continue

        key = get_config_key(
            cfg
        )

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(
            cfg
        )

    return cleaned


# ==========================================
# ساخت / به‌روزرسانی Subscription
# ==========================================

def update_subscription():

    print("\n" + "=" * 50)
    print(
        "مرحله ۱: ساخت / به‌روزرسانی ساب"
    )
    print("=" * 50)

    # ----------------------------------
    # ساب قبلی
    # ----------------------------------

    old_sub = load_subscription()

    print(
        f"ساب قبلی: {len(old_sub)} کانفیگ"
    )

    old_by_key = {}

    for cfg in old_sub:

        if not is_valid_config(cfg):
            continue

        key = get_config_key(
            cfg
        )

        if key not in old_by_key:

            old_by_key[key] = cfg

    # ----------------------------------
    # کانفیگ‌های جدید
    # ----------------------------------

    new_configs = []

    new_keys = set()

    total_found = 0

    total_invalid = 0

    total_duplicate = 0

    source_stats = []

    # ==================================
    # تابع افزودن
    # ==================================

    def process_source_configs(
        configs,
        source_name
    ):

        nonlocal total_found
        nonlocal total_invalid
        nonlocal total_duplicate

        source_new = 0
        source_invalid = 0
        source_duplicate = 0

        total_found += len(configs)

        for cfg in configs:

            if not is_valid_config(cfg):

                source_invalid += 1
                total_invalid += 1

                continue

            ip, port = extract_ip_port(
                cfg
            )

            if not ip or not port:

                source_invalid += 1
                total_invalid += 1

                continue

            key = get_config_key(
                cfg
            )

            # قبلاً در منابع همین اجرا
            if key in new_keys:

                source_duplicate += 1
                total_duplicate += 1

                continue

            new_keys.add(key)

            # اگر در ساب قبلی بوده
            if key in old_by_key:

                # فعلاً اضافه نمی‌کنیم؛
                # نسخه قبلی را بعداً حفظ می‌کنیم
                source_duplicate += 1
                total_duplicate += 1

                continue

            new_configs.append(cfg)

            source_new += 1

        source_stats.append({
            "name": source_name,
            "found": len(configs),
            "new": source_new,
            "invalid": source_invalid,
            "duplicate": source_duplicate
        })

    # ==================================
    # کانال‌ها
    # ==================================

    for ch in SOURCE_CHANNELS:

        print(
            f"\n→ در حال دریافت از "
            f"کانال @{ch} ..."
        )

        configs = collect_from_channel(
            ch
        )

        process_source_configs(
            configs,
            f"@{ch}"
        )

        stat = source_stats[-1]

        print(
            f"  پیدا شد: {stat['found']}"
            f" | جدید: {stat['new']}"
            f" | تکراری/قدیمی: {stat['duplicate']}"
            f" | نامعتبر: {stat['invalid']}"
        )

    # ==================================
    # Subscriptionهای خارجی
    # ==================================

    for index, sub_url in enumerate(
        SOURCE_SUBS,
        1
    ):

        print(
            f"\n→ در حال دریافت از لینک ساب "
            f"#{index} ..."
        )

        configs = collect_from_sub(
            sub_url
        )

        process_source_configs(
            configs,
            f"SUB#{index}"
        )

        stat = source_stats[-1]

        print(
            f"  پیدا شد: {stat['found']}"
            f" | جدید: {stat['new']}"
            f" | تکراری/قدیمی: {stat['duplicate']}"
            f" | نامعتبر: {stat['invalid']}"
        )

    # ==================================
    # آماده‌سازی جدیدها
    # ==================================

    print("\n" + "-" * 50)

    print(
        f"مجموع پیدا شده: {total_found}"
    )

    print(
        f"جدید و قابل اضافه شدن: "
        f"{len(new_configs)}"
    )

    print(
        f"تکراری یا موجود در ساب قبلی: "
        f"{total_duplicate}"
    )

    print(
        f"نامعتبر / بدون IP یا Port: "
        f"{total_invalid}"
    )

    # ==================================
    # دریافت پرچم جدیدها
    # ==================================

    new_flagged = []

    if new_configs:

        unique_ips = []

        seen_ip = set()

        for cfg in new_configs:

            ip, _ = extract_ip_port(
                cfg
            )

            if (
                ip
                and ip not in seen_ip
            ):

                seen_ip.add(ip)
                unique_ips.append(ip)

        print(
            f"\n→ دریافت پرچم برای "
            f"{len(new_configs)} کانفیگ جدید "
            f"({len(unique_ips)} IP یکتا) ..."
        )

        country_info = get_country_and_flag(
            unique_ips
        )

        for cfg in new_configs:

            ip, _ = extract_ip_port(
                cfg
            )

            flag = (
                country_info
                .get(ip, {})
                .get(
                    "flag",
                    "🌐"
                )
            )

            modified = change_remark_v2ray(
                cfg,
                f"{flag} {CUSTOM_REMARK}"
            )

            new_flagged.append(
                modified
            )

        print(
            f"  ✅ پرچم برای "
            f"{len(new_flagged)} کانفیگ اضافه شد"
        )

    # ==================================
    # آماده‌سازی قدیمی‌ها
    # ==================================

    old_kept = list(
        old_by_key.values()
    )

    print(
        f"\n→ کانفیگ‌های قدیمی قابل حفظ: "
        f"{len(old_kept)}"
    )

    # ==================================
    # اولویت‌بندی صحیح
    #
    # NEW → OLD
    # ==================================

    all_configs = (
        new_flagged
        + old_kept
    )

    total_before_limit = len(
        all_configs
    )

    # نکته مهم:
    # قبلاً [-1000:] بود که اشتباه بود.
    # الان [:1000] است.
    # بنابراین جدیدها اولویت دارند.
    all_configs = all_configs[
        :MAX_SUB_SIZE
    ]

    removed_by_limit = (
        total_before_limit
        - len(all_configs)
    )

    print(
        f"\nتعداد قبل از محدودیت: "
        f"{total_before_limit}"
    )

    print(
        f"ظرفیت Subscription: "
        f"{MAX_SUB_SIZE}"
    )

    print(
        f"به علت محدودیت ظرفیت حذف شد: "
        f"{removed_by_limit}"
    )

    print(
        f"تعداد نهایی: "
        f"{len(all_configs)}"
    )

    save_subscription(
        all_configs
    )

    print("\n" + "=" * 50)

    return all_configs


# ==========================================
# انتخاب V2Ray
# ==========================================

def get_v2ray_from_sub(sent_ips):

    print("\n" + "=" * 50)

    print(
        "مرحله ۲: انتخاب ۵ کانفیگ "
        "از ساب (بدون تست پورت | اولویت اروپا)"
    )

    print("=" * 50)

    sub_configs = load_subscription()

    if not sub_configs:

        print(
            "❌ ساب خالی است."
        )

        return []

    print(
        f"تعداد کانفیگ در ساب: "
        f"{len(sub_configs)}"
    )

    # ----------------------------------
    # ابتدا همه را مرتب می‌کنیم
    # جدید بودن بر اساس sent_ips
    # ----------------------------------

    candidates = []

    seen = set()

    for cfg in sub_configs:

        if not is_valid_config(cfg):
            continue

        ip, port = extract_ip_port(
            cfg
        )

        if not ip or not port:
            continue

        ip_port = (
            f"{ip}:{port}"
        )

        if ip_port in seen:
            continue

        seen.add(ip_port)

        candidates.append({
            "config": cfg,
            "ip_port": ip_port,
            "is_new": (
                ip_port not in sent_ips
            ),
            "ip": ip
        })

    # ----------------------------------
    # جدیدها اول
    # ----------------------------------

    new_candidates = [
        c
        for c in candidates
        if c["is_new"]
    ]

    old_candidates = [
        c
        for c in candidates
        if not c["is_new"]
    ]

    random.shuffle(
        new_candidates
    )

    random.shuffle(
        old_candidates
    )

    candidates = (
        new_candidates
        + old_candidates
    )

    # حداکثر 50 کاندید برای بررسی کشور
    candidates = candidates[:50]

    print(
        f"کاندیداهای جدید: "
        f"{len(new_candidates[:50])}"
    )

    print(
        f"کاندیداهای قبلی: "
        f"{len(old_candidates[:50])}"
    )

    print(
        f"تعداد کاندیدای بررسی‌شده: "
        f"{len(candidates)}"
    )

    if not candidates:
        return []

    # ----------------------------------
    # کشور
    # ----------------------------------

    ips = [
        c["ip"]
        for c in candidates
    ]

    country_info = get_country_and_flag(
        ips
    )

    europe = []
    others = []

    for c in candidates:

        info = country_info.get(
            c["ip"],
            {}
        )

        code = info.get(
            "code",
            ""
        )

        c["country_code"] = code

        c["flag"] = info.get(
            "flag",
            "🌐"
        )

        if code in PREFERRED_COUNTRIES:

            europe.append(c)

        else:

            others.append(c)

    print(
        f"اروپایی: {len(europe)} "
        f"| بقیه: {len(others)}"
    )

    selected = []

    # اروپا اول
    selected.extend(
        europe[:MAX_V2RAY_POST]
    )

    # اگر کم بود، بقیه
    if len(selected) < MAX_V2RAY_POST:

        needed = (
            MAX_V2RAY_POST
            - len(selected)
        )

        selected.extend(
            others[:needed]
        )

    print(
        f"نهایی انتخاب شده: "
        f"{len(selected)}"
    )

    return selected


# ==========================================
# دریافت MTProto
# ==========================================

def get_mtproto_proxies(sent_ips):

    print("\n" + "=" * 50)

    print(
        "مرحله ۳: دریافت پروکسی‌های MTProto"
    )

    print("=" * 50)

    found = []

    for src_chan in MTPROTO_CHANNELS:

        tg_url = (
            f"https://t.me/s/{src_chan}"
        )

        try:

            resp = requests.get(
                tg_url,
                timeout=12,
                headers={
                    "User-Agent":
                    "Mozilla/5.0"
                }
            )

            if resp.status_code != 200:

                print(
                    f"  ⚠️ @{src_chan}: "
                    f"{resp.status_code}"
                )

                continue

            soup = BeautifulSoup(
                resp.text,
                "html.parser"
            )

            messages = soup.find_all(
                "div",
                class_="tgme_widget_message"
            )[-8:]

            for msg in messages:

                text_div = msg.find(
                    "div",
                    class_="tgme_widget_message_text"
                )

                if text_div:

                    matches = re.findall(
                        r"(https://t\.me/proxy\?[^\s<>\"']+|"
                        r"tg://proxy\?[^\s<>\"']+)",
                        text_div.get_text()
                    )

                    found.extend(
                        matches
                    )

                for btn in msg.find_all(
                    "a",
                    href=True
                ):

                    href = btn.get(
                        "href",
                        ""
                    )

                    if (
                        "tg://proxy" in href
                        or
                        "https://t.me/proxy" in href
                    ):

                        found.append(
                            href
                        )

        except Exception as e:

            print(
                f"  ❌ خطا در @{src_chan}: {e}"
            )

    # ----------------------------------
    # Dedup
    # ----------------------------------

    unique = []

    seen = set()

    for proxy in found:

        proxy = proxy.strip()

        ip, port = extract_ip_port(
            proxy
        )

        if not ip or not port:
            continue

        key = (
            f"{ip}:{port}"
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            proxy
        )

    print(
        f"تعداد پروکسی یکتا: "
        f"{len(unique)}"
    )

    # ----------------------------------
    # جدید / قدیمی
    # ----------------------------------

    new_proxies = []
    old_proxies = []

    for proxy in unique:

        ip, port = extract_ip_port(
            proxy
        )

        ip_port = (
            f"{ip}:{port}"
        )

        if ip_port not in sent_ips:

            new_proxies.append(
                proxy
            )

        else:

            old_proxies.append(
                proxy
            )

    print(
        f"جدید: {len(new_proxies)} "
        f"| قبلی: {len(old_proxies)}"
    )

    random.shuffle(
        new_proxies
    )

    random.shuffle(
        old_proxies
    )

    selected = new_proxies[
        :MAX_MTPROTO_POST
    ]

    if len(selected) < MAX_MTPROTO_POST:

        needed = (
            MAX_MTPROTO_POST
            - len(selected)
        )

        selected.extend(
            old_proxies[:needed]
        )

    return selected[
        :MAX_MTPROTO_POST
    ]


# ==========================================
# Main
# ==========================================

def main():

    delay = random.randint(
        40,
        160
    )

    print(
        f"ربات برای طبیعی بودن "
        f"{delay} ثانیه صبر می‌کند..."
    )

    time.sleep(delay)

    sent_ips = get_sent_ips()

    print(
        f"تعداد IPهای ذخیره‌شده قبلی: "
        f"{len(sent_ips)}"
    )

    # ======================================
    # Subscription
    # ======================================

    update_subscription()

    # ======================================
    # V2Ray
    # ======================================

    v2ray_results = get_v2ray_from_sub(
        sent_ips
    )

    if v2ray_results:

        configs_to_post = []

        for item in v2ray_results:

            flag = item.get(
                "flag",
                "🌐"
            )

            modified = change_remark_v2ray(
                item["config"],
                f"{flag} {CUSTOM_REMARK}"
            )

            configs_to_post.append(
                modified
            )

        success = send_post(
            configs_to_post,
            "v2ray"
        )

        # فقط اگر ارسال موفق بود
        # IPها ثبت شوند
        if success:

            for item in v2ray_results:

                sent_ips.add(
                    item["ip_port"]
                )

    else:

        print(
            "هیچ کانفیگ V2Ray پیدا نشد."
        )

    # ======================================
    # فاصله بین دو پست
    # ======================================

    between_delay = random.randint(
        180,
        720
    )

    print(
        f"\n⏳ فاصله رندم بین دو پست: "
        f"{between_delay // 60} دقیقه "
        f"و {between_delay % 60} ثانیه..."
    )

    time.sleep(
        between_delay
    )

    # ======================================
    # MTProto
    # ======================================

    mt_proxies = get_mtproto_proxies(
        sent_ips
    )

    if mt_proxies:

        all_ips = []

        for proxy in mt_proxies:

            ip, _ = extract_ip_port(
                proxy
            )

            if ip:
                all_ips.append(
                    ip
                )

        country_info = get_country_and_flag(
            all_ips
        )

        configs_to_post = []

        for proxy in mt_proxies:

            ip, port = extract_ip_port(
                proxy
            )

            flag = (
                country_info
                .get(ip, {})
                .get(
                    "flag",
                    "🌐"
                )
                if ip
                else "🌐"
            )

            modified = change_remark_mtproto(
                proxy,
                f"{flag} {CUSTOM_REMARK}"
            )

            configs_to_post.append(
                modified
            )

        success = send_post(
            configs_to_post,
            "mtproto"
        )

        if success:

            for proxy in mt_proxies:

                ip, port = extract_ip_port(
                    proxy
                )

                if ip and port:

                    sent_ips.add(
                        f"{ip}:{port}"
                    )

    else:

        print(
            "هیچ پروکسی MTProto پیدا نشد."
        )

    # ======================================
    # ذخیره IPهای ارسال‌شده
    # ======================================

    save_sent_ips(
        sent_ips
    )

    print(
        f"\n✅ کار تمام شد. "
        f"تعداد IPهای ثبت‌شده: "
        f"{len(sent_ips)}"
    )


# ==========================================
# اجرای برنامه
# ==========================================

if __name__ == "__main__":
    main()
