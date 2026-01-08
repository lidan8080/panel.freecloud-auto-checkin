#!/usr/bin/env python3
"""
FreeCloud 自动签到（WHMCS · requests 终局稳定版）
"""

import os
import re
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE = "https://panel.freecloud.ltd"
LOGIN_PAGE = f"{BASE}/clientarea.php"
LOGIN_POST = f"{BASE}/dologin.php"
CHECKIN_URL = f"{BASE}/clientarea.php?action=checkin"

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": msg},
        timeout=10
    )

def extract_token(html: str):
    """
    WHMCS 登录页里有：
    <input type="hidden" name="token" value="xxxx">
    """
    m = re.search(r'name="token"\s+value="([^"]+)"', html)
    return m.group(1) if m else None

def login_and_checkin(email, password):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Referer": LOGIN_PAGE,
    })

    # 1️⃣ 访问登录页，拿 token
    r = s.get(LOGIN_PAGE, timeout=15)
    token = extract_token(r.text)
    if not token:
        return False, "未获取到登录 token"

    # 2️⃣ 正确登录（WHMCS）
    resp = s.post(LOGIN_POST, data={
        "username": email,
        "password": password,
        "token": token
    }, timeout=15)

    if "logout" not in resp.text.lower():
        return False, "登录失败"

    # 3️⃣ 签到
    c = s.get(CHECKIN_URL, timeout=15)
    t = c.text

    if "签到成功" in t:
        return True, "签到成功"
    if "已经签到" in t:
        return True, "今日已签到"

    return True, "已登录，但签到状态未知"

def main():
    raw = os.getenv("FC_ACCOUNTS", "")
    if not raw:
        raise RuntimeError("未设置 FC_ACCOUNTS")

    results = []
    for pair in raw.split(","):
        email, pwd = pair.split(":", 1)
        ok, msg = login_and_checkin(email.strip(), pwd.strip())
        results.append((email, ok, msg))

    ok_count = sum(1 for _, ok, _ in results)

    message = (
        "🚀【FreeCloud · 新项目】自动签到完成\n"
        f"📊 成功：{ok_count}/{len(results)}\n"
        f"📅 {datetime.now():%Y-%m-%d}\n\n"
    )

    for email, ok, msg in results:
        message += ("✅" if ok else "❌") + f" {email[:3]}***：{msg}\n"

    send_telegram(message)

if __name__ == "__main__":
    main()
