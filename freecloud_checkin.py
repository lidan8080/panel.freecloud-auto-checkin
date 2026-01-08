import os
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup  # 新增：解析HTML获取Token

LOGIN_URL = "https://panel.freecloud.ltd/clientarea.php"
CHECKIN_URL = "https://panel.freecloud.ltd/clientarea.php?action=checkin"

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram推送失败：{str(e)}")

def run_account(email, password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    try:
        # 步骤1：访问登录页，获取CSRF Token
        login_page = session.get(LOGIN_URL, timeout=15)
        soup = BeautifulSoup(login_page.text, "html.parser")
        token = soup.find("input", {"name": "token"})["value"]  # WHMCS登录需要的Token

        # 步骤2：提交登录请求
        login_data = {
            "token": token,
            "email": email,
            "password": password,
            "rememberme": "on",
            "submit": "Login"
        }
        login_res = session.post(LOGIN_URL, data=login_data, timeout=15, allow_redirects=True)

        # 验证登录是否成功（登录后会跳转到/clientarea.php，且页面含“Dashboard”）
        if "Dashboard" not in login_res.text:
            return "❌ 登录失败（账号/密码错误或Token失效）"

        # 步骤3：访问签到页
        checkin_res = session.get(CHECKIN_URL, timeout=15)
        checkin_soup = BeautifulSoup(checkin_res.text, "html.parser")

        # 判断签到结果
        if "已签到" in checkin_res.text:
            return "✅ 今日已签到"
        elif "签到成功" in checkin_res.text:
            return "✅ 签到成功"
        elif "You have successfully checked in" in checkin_res.text:  # 兼容英文提示
            return "✅ 签到成功"
        else:
            return "⚠️ 未识别签到结果（页面内容：" + checkin_soup.title.text[:30] + "）"

    except Exception as e:
        return f"❌ 异常：{str(e)[:120]}"

def main():
    accounts = os.getenv("FC_ACCOUNTS", "")
    results = []

    if not accounts:
        send_telegram("🚀【FreeCloud 自动签到】\n未配置任何账号（FC_ACCOUNTS为空）")
        return

    for pair in accounts.split(","):
        if ":" not in pair:
            results.append(f"⚠️ 账号格式错误：{pair}（正确格式：邮箱:密码）")
            continue
        email, pwd = pair.split(":", 1)
        email = email.strip()
        pwd = pwd.strip()
        result = run_account(email, pwd)
        results.append(f"{email[:3]}***: {result}")
        time.sleep(3)

    msg = "🚀【FreeCloud 自动签到】\n"
    msg += datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
    msg += "\n".join(results)
    send_telegram(msg)

if __name__ == "__main__":
    main()
