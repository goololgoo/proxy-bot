import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CHANNELS = [
    "PinkProxy",
    "Myporoxy",
    "ProxyWR",
    "P500Y",
    "ProxyMTProto",
    "webproxy",
]
OUTPUT = Path("goololgoo_telegram_proxy.txt")
MAX_PROXIES = 500
LINK_RE = re.compile(
    r"(?:https://t\.me/(?:proxy|webproxy)\?[^\s<>\"']+|"
    r"tg://(?:proxy|webproxy)\?[^\s<>\"']+)",
    re.IGNORECASE,
)


def parse_proxy(link):
    link = link.strip()
    parsed = urllib.parse.urlparse(link)
    scheme = parsed.scheme.lower()
    if scheme == "https":
        if parsed.netloc.lower() != "t.me" or parsed.path.strip("/") not in ("proxy", "webproxy"):
            return None
        kind = parsed.path.strip("/").lower()
    elif scheme == "tg":
        kind = parsed.netloc.lower()
        if kind not in ("proxy", "webproxy"):
            return None
    else:
        return None

    query = urllib.parse.parse_qs(parsed.query)
    server = query.get("server", [""])[0].strip().lower()
    port = query.get("port", [""])[0].strip()
    secret = query.get("secret", [""])[0].strip()
    if not server or not secret:
        return None

    # WEB Proxy links intentionally have no port parameter; Telegram uses 443.
    if kind == "webproxy":
        key = (kind, server, secret.lower())
    else:
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return None
        key = (kind, server, port, secret.lower())
    return key, link


def main():
    links = []
    seen = set()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for channel in CHANNELS:
        try:
            response = session.get(f"https://t.me/s/{channel}", timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")[-12:]

            for message in messages:
                text_node = message.find("div", class_="tgme_widget_message_text")
                candidates = []
                if text_node:
                    candidates.extend(LINK_RE.findall(text_node.get_text(" ", strip=True)))
                candidates.extend(a.get("href", "") for a in message.find_all("a", href=True))

                for candidate in candidates:
                    candidate = candidate.strip().rstrip(".,);]}>")
                    parsed = parse_proxy(candidate)
                    if not parsed:
                        continue
                    key, original_link = parsed
                    if key not in seen:
                        seen.add(key)
                        # Keep /webproxy links intact; do not rewrite them as MTProto /proxy links.
                        links.append(original_link)
        except Exception as exc:
            print(f"Could not fetch @{channel}: {exc}")

    if not links:
        print("WARNING: no valid proxies found; preserving the previous subscription file.")
        return

    selected = links[:MAX_PROXIES]
    OUTPUT.write_text("".join(link + "\n" for link in selected), encoding="utf-8")
    print(
        f"Saved {len(selected)} unique Telegram proxies "
        f"({sum(1 for link in selected if 'webproxy?' in link.lower())} WEB Proxy) "
        f"to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
