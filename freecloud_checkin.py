import os, time, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

FC_URL = "https://panel.freecloud.ltd/clientarea.php"

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": msg}
    )

def run_account(email, password):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(FC_URL)

        # 登录
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(email)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        # 等 dashboard
        wait.until(lambda d: "clientarea.php" in d.current_url)

        # 签到按钮（FreeCloud 实际就是一个按钮）
        time.sleep(3)
        buttons = driver.find_elements(By.XPATH, "//button")
        for b in buttons:
            if "签到" in b.text:
                b.click()
                break

        time.sleep(5)
        return "✅ 签到完成 / 已签到"

    except Exception as e:
        return f"❌ 失败：{str(e)[:120]}"
    finally:
        driver.quit()

def main():
    accounts = os.getenv("FC_ACCOUNTS", "")
    results = []
    for pair in accounts.split(","):
        email, pwd = pair.split(":", 1)
        res = run_account(email.strip(), pwd.strip())
        results.append(f"{email[:3]}***: {res}")

    msg = "🚀【FreeCloud 自动签到】\n" + datetime.now().strftime("%Y-%m-%d") + "\n\n"
    msg += "\n".join(results)
    send_telegram(msg)

if __name__ == "__main__":
    main()
