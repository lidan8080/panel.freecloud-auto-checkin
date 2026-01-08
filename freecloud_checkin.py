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
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": msg},
        timeout=10
    )

def run_account(email, password):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(LOGIN_URL)

        # WHMCS 登录
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 登录成功判断
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        if "login" in driver.current_url.lower():
            return "❌ 登录失败"

        # 直接访问签到页（最稳）
        driver.get(CHECKIN_URL)
        time.sleep(5)

        page_text = driver.page_source
        if "已签到" in page_text or "签到成功" in page_text:
            return "✅ 今日已签到"
        if "签到" in page_text:
            return "✅ 签到完成"

        return "⚠️ 未识别签到结果"

    except Exception as e:
        return f"❌ 异常：{str(e)[:120]}"
    finally:
        driver.quit()

def main():
    accounts = os.getenv("FC_ACCOUNTS", "")
    results = []

    for pair in accounts.split(","):
        email, pwd = pair.split(":", 1)
        result = run_account(email.strip(), pwd.strip())
        results.append(f"{email[:3]}***: {result}")
        time.sleep(3)

    msg = "🚀【FreeCloud 自动签到】\n"
    msg += datetime.now().strftime("%Y-%m-%d") + "\n\n"
    msg += "\n".join(results)
    send_telegram(msg)

if __name__ == "__main__":
    main()
