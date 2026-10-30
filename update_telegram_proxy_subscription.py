import html
import re
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CHANNELS = ["PinkProxy", "Myporoxy", "ProxyWR", "P500Y", "ProxyMTProto", "webproxy"]
OUTPUT = Path("goololgoo_telegram_proxy.txt")
MAX_PROXIES = 500
LINK_RE = re.compile(
    r"(?:https://t\.me/(?:proxy|webproxy)\?[^\s<>\"']+|"
    r"tg://(?:proxy|webproxy)\?[^\s<>\"']+)",
    re.IGNORECASE,
)


def clean_link(link):
    return html.unescape(link.strip()).replace(r"\&", "&").rstrip(".,);]}")


def parse_proxy(link):
    link = clean_link(link)
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
    if kind == "webproxy":
        key = (kind, server, secret.lower())
    else:
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            return None
        key = (kind, server, port, secret.lower())
    return key, link


def extract_message_metadata(message):
    """Read Server/Port/Secret from the message body above its inline buttons."""
    text_node = message.find("div", class_="tgme_widget_message_text")
    if not text_node:
        return None

    body = html.unescape(text_node.get_text(" ", strip=True)).replace("\u00a0", " ")
    fields = {}
    for label in ("server", "port", "secret"):
        match = re.search(
            rf"\b{label}\s*:\s*[\x60]?([^\s\\\x60]+)",
            body,
            flags=re.IGNORECASE,
        )
        if match:
            fields[label] = match.group(1).strip().strip("\x60.,;")

    if not fields:
        return None

    server = fields.get("server", "")
    port = fields.get("port", "")
    secret = fields.get("secret", "")
    print(
        "Message metadata: "
        f"server={server or 'missing'}, port={port or 'missing'}, "
        f"secret={'present' if secret else 'missing'}"
    )

    if (
        server
        and server.lower() not in {"unknown", "n/a", "none", "-"}
        and port.isdigit()
        and 1 <= int(port) <= 65535
        and secret
    ):
        query = urllib.parse.urlencode({"server": server, "port": port, "secret": secret})
        return "tg://proxy?" + query
    return None


def extract_message_links(message):
    candidates = []
    text_node = message.find("div", class_="tgme_widget_message_text")
    if text_node:
        candidates.extend(LINK_RE.findall(html.unescape(text_node.get_text(" ", strip=True))))

    # Inline keyboard URLs are href attributes; visible button labels do not contain URLs.
    candidates.extend(anchor["href"] for anchor in message.find_all("a", href=True))

    metadata_link = extract_message_metadata(message)
    if metadata_link:
        candidates.append(metadata_link)
    return candidates


def main():
    links = []
    seen = set()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for channel in CHANNELS:
        try:
            response = session.get(f"https://t.me/s/{channel}", timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message")[-20:]

            for message in messages:
                for candidate in extract_message_links(message):
                    parsed = parse_proxy(candidate)
                    if not parsed:
                        continue
                    key, original_link = parsed
                    if key not in seen:
                        seen.add(key)
                        links.append(original_link)
        except Exception as exc:
            print(f"Could not fetch @{channel}: {exc}")

    if not links:
        print("WARNING: no valid proxies found; preserving the previous subscription file.")
        return

    selected = links[:MAX_PROXIES]
    OUTPUT.write_text("".join(link + "\n" for link in selected), encoding="utf-8")
    mtproto_count = sum(1 for link in selected if "tg://proxy?" in link.lower() or "t.me/proxy?" in link.lower())
    web_count = sum(1 for link in selected if "/webproxy?" in link.lower())
    print(f"Saved {len(selected)} unique Telegram proxies ({mtproto_count} MTProto, {web_count} WEB Proxy) to {OUTPUT}")


if __name__ == "__main__":
    main()
