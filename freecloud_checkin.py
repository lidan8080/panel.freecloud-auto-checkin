import os
import time
import requests
from datetime import datetime
from requests_html import HTMLSession  # 支持JS渲染的请求库

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
    # 初始化支持JS渲染的会话
    session = HTMLSession()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1"
    })

    try:
        # 步骤1：访问登录页并渲染JS（获取动态Token）
        login_page = session.get(LOGIN_URL, timeout=20)
        login_page.html.render(timeout=20)  # 执行页面JS，渲染动态内容

        # 查找多种可能的Token元素
        token_elem = login_page.html.find("input[name='token'], input[name='_token'], input[name='whmcs_token']", first=True)
        if not token_elem:
            return "❌ Token获取失败（页面无匹配元素，可能被反爬拦截）"
        token = token_elem.attrs.get("value")
        if not token:
            return "❌ Token值为空"

        # 步骤2：提交登录请求
        login_data = {
            "token": token,
            "email": email,
            "password": password,
            "rememberme": "on",
            "submit": "Login"
        }
        login_res = session.post(LOGIN_URL, data=login_data, timeout=20, allow_redirects=True)
        login_res.html.render(timeout=20)  # 渲染登录后页面

        # 验证登录状态
        if "Welcome," not in login_res.html.text and "Dashboard" not in login_res.html.text:
            return "❌ 登录失败（账号/密码错误或反爬拦截）"

        # 步骤3：访问签到页
        checkin_res = session.get(CHECKIN_URL, timeout=20)
        checkin_res.html.render(timeout=20)

        # 判断签到结果
        checkin_text = checkin_res.html.text
        if "已签到" in checkin_text:
            return "✅ 今日已签到"
        elif "签到成功" in checkin_text or "You have successfully checked in" in checkin_text:
            return "✅ 签到成功"
        else:
            return "⚠️ 未识别签到结果（页面预览：" + checkin_text[:60].replace("\n", " ") + "）"

    except Exception as e:
        return f"❌ 异常：{str(e)[:120]}"
    finally:
        session.close()

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
        time.sleep(5)  # 延长间隔，降低反爬风险

    msg = "🚀【FreeCloud 自动签到】\n"
    msg += datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
    msg += "\n".join(results)
    send_telegram(msg)

if __name__ == "__main__":
    main()
