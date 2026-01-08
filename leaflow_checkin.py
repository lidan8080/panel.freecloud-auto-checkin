#!/usr/bin/env python3
"""
FreeCloud 自动签到（requests 稳定版）
"""

import os
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

LOGIN_URL = "https://panel.freecloud.ltd/dologin.php"
CHECKIN_URL = "https://panel.freecloud.ltd/clientarea.php?action=checkin"

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

def login_and_checkin(email, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://panel.freecloud.ltd/clientarea.php"
    })

    # 登录
    resp = session.post(LOGIN_URL, data={
        "username": email,
        "password": password
    }, timeout=15)

    if "logout" not in resp.text.lower():
        return False, "登录失败"

    # 签到
    r = session.get(CHECKIN_URL, timeout=15)
    text = r.text

    if "签到成功" in text:
        return True, "签到成功"
    if "已经签到" in text:
        return True, "今日已签到"

    return False, "签到状态未知"

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
