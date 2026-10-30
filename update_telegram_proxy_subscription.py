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
LINK_RE = re.compile(
    r"(?:https://t\.me/(?:proxy|webproxy)\?[^\s<>\"']+|"
    r"tg://(?:proxy|webproxy)\?[^\s<>\"']+)",
    re.IGNORECASE,
)


def proxy_key(link):
    parsed = urllib.parse.urlparse(link.strip())
    query = urllib.parse.parse_qs(parsed.query)
    server = query.get("server", [""])[0].strip().lower()
    port = query.get("port", [""])[0].strip()
    secret = query.get("secret", [""])[0].strip().lower()
    if not server or not port.isdigit():
        return None
    return server, port, secret


def main():
    links = []
    seen = set()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for channel in CHANNELS:
        try:
            response = session.get(
                f"https://t.me/s/{channel}",
                timeout=15,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.find_all(
                "div", class_="tgme_widget_message"
            )[-12:]

            for message in messages:
                text_node = message.find(
                    "div", class_="tgme_widget_message_text"
                )
                candidates = []
                if text_node:
                    candidates.extend(LINK_RE.findall(
                        text_node.get_text(" ", strip=True)
                    ))
                candidates.extend(
                    a.get("href", "")
                    for a in message.find_all("a", href=True)
                )

                for candidate in candidates:
                    candidate = candidate.strip().rstrip(".,);]")
                    if not candidate.lower().startswith(
                        ("https://t.me/proxy?", "https://t.me/webproxy?",
                         "tg://proxy?", "tg://webproxy?")
                    ):
                        continue
                    key = proxy_key(candidate)
                    if key and key not in seen:
                        seen.add(key)
                        # Standard Telegram deep link; retain the full query.
                        parsed = urllib.parse.urlparse(candidate)
                        canonical = urllib.parse.urlunparse((
                            "https" if parsed.scheme == "https" else "tg",
                            "t.me" if parsed.scheme == "https" else "",
                            "/proxy" if parsed.path.endswith(("proxy", "webproxy")) else parsed.path,
                            "", parsed.query, ""
                        )) if parsed.scheme == "https" else candidate
                        links.append(canonical)
        except Exception as exc:
            print(f"Could not fetch @{channel}: {exc}")

    # Always write the file so the workflow can safely preserve it.
    OUTPUT.write_text(
        "".join(link + "\n" for link in links),
        encoding="utf-8",
    )
    print(f"Saved {len(links)} unique Telegram MTProto proxies to {OUTPUT}")
    if not links:
        print("WARNING: no valid MTProto links were found; output file is empty.")


if __name__ == "__main__":
    main()
