# Group bot rebuild — 2026-11-01

## Safety boundary
- This branch is isolated from `main`.
- The deployed Cloudflare Worker is not changed by this branch.
- The current deployed Worker source is preserved at `backups/cloudflare-worker-2026-11-01.js`.
- Preserve the current channel scheduler and Durable Object alarm sequence when integrating the group rewrite.

## Main group menu
- 📚 آموزش
- ⚙️ کانفیگ
- 📡 پروکسی تلگرام
- 🔗 ساب

Free-text AI replies are intentionally excluded.

## Data sources
- Configs: `goololgoo.txt` in the repository root. Each request returns five randomly selected URI lines (vless, vmess, trojan, ss, socks, hy2, hysteria2). Do not perform connectivity checks.
- Telegram proxies: `goololgoo_telegram_proxy.txt` in the repository root. Each request returns five randomly selected Telegram proxy links. Do not perform connectivity checks.
- Subscription catalogue: `data/subscriptions.json`, maintained in GitHub. Filter by country and protocol; do not infer country/protocol when metadata is missing.
- Lessons: channel posts containing `#آموزش_گو‌‌لول‌گو`; the Worker must receive `channel_post` and `edited_channel_post` webhook updates and index title/link. Bot API does not provide historical channel-message search, so legacy lessons need a one-time backfill.

## Subscription schema
Each record:
`id`, `title`, `country`, `country_code`, `protocol`, `url`, optional `description`.
The catalogue is intentionally empty until actual subscription URLs and metadata are supplied.

## Random selection rules
- Config button: exactly five random distinct configs where at least five exist; otherwise send all available.
- Proxy button: exactly five random distinct Telegram proxy links where at least five exist; otherwise send all available.
- No connection-status validation or filtering.
- Do not silently drop records based on reachability.

## Subscription UX
- Choose country, then protocol (or protocol, then country).
- Show only records matching both filters.
- Return selected subscription URL and a back button.
- If there are no matching records, explain that no subscription is registered for that combination yet.

## Lesson UX
- Education button shows a paginated list of indexed lessons.
- Selecting a lesson opens the corresponding channel post.
- New tagged channel posts are added automatically; edited posts update their title/link; untagged posts are ignored.
- Avoid duplicate lesson entries by channel message_id.

## Group membership and welcome
- Welcome new non-bot members with the inline main menu.
- Keep membership verification for group and channel.
- Keep ordinary free-text messages ignored; no AI responses.

## Deployment requirements
- Deploy only after reviewing the full Worker and preserving the scheduler/DO behavior.
- Verify webhook allowed_updates includes message, callback_query, channel_post, edited_channel_post.
- Test with a non-admin account: join event, menu, each button, pagination, membership check.
- Verify /health and the channel scheduler state before and after deployment.
