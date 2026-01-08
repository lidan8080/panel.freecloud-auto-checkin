import os, time, requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
    options = Options()
    # 适配无界面环境的核心参数
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 屏蔽无关日志

    # 核心修改：移除固定版本，让webdriver-manager自动匹配当前Chrome版本
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(LOGIN_URL)

        # WHMCS 登录
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys(email)
        pwd_input = driver.find_element(By.NAME, "password")
        pwd_input.send_keys(password)
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # 登录成功判断
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        if "login" in driver.current_url.lower():
            return "❌ 登录失败（账号/密码错误）"

        # 直接访问签到页
        driver.get(CHECKIN_URL)
        time.sleep(5)

        page_text = driver.page_source
        if "已签到" in page_text:
            return "✅ 今日已签到"
        elif "签到成功" in page_text:
            return "✅ 签到成功"
        elif "签到" in page_text:
            return "✅ 签到完成"
        else:
            return "⚠️ 未识别签到结果（页面无关键关键词）"

    except Exception as e:
        return f"❌ 异常：{str(e)[:120]}"
    finally:
        driver.quit()

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
