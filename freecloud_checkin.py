import os, time, requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 固定配置（适配Docker镜像的Chrome）
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 30)

LOGIN_URL = "https://panel.freecloud.ltd/clientarea.php"
CHECKIN_URL = "https://panel.freecloud.ltd/clientarea.php?action=checkin"

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat_id, "text": msg}, timeout=10)
        except:
            pass

def main():
    accounts = os.getenv("FC_ACCOUNTS", "").split(",")
    results = []
    if not accounts or accounts == [""]:
        send_telegram("🚀 FreeCloud签到：未配置账号")
        return

    for pair in accounts:
        if ":" not in pair:
            results.append(f"⚠️ {pair}：账号格式错误（邮箱:密码）")
            continue
        email, pwd = pair.split(":", 1)
        email, pwd = email.strip(), pwd.strip()
        try:
            # 登录
            driver.get(LOGIN_URL)
            wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
            driver.find_element(By.NAME, "password").send_keys(pwd)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(3)
            
            # 签到
            if "login" not in driver.current_url.lower():
                driver.get(CHECKIN_URL)
                time.sleep(5)
                page_text = driver.page_source
                if "已签到" in page_text:
                    results.append(f"{email[:3]}***：✅ 已签到")
                elif "签到成功" in page_text:
                    results.append(f"{email[:3]}***：✅ 签到成功")
                else:
                    results.append(f"{email[:3]}***：⚠️ 结果未知")
            else:
                results.append(f"{email[:3]}***：❌ 登录失败")
        except Exception as e:
            results.append(f"{email[:3]}***：❌ 异常{str(e)[:50]}")
        time.sleep(2)

    # 推送结果
    msg = f"🚀 FreeCloud签到 {datetime.now().strftime('%Y-%m-%d')}\n" + "\n".join(results)
    send_telegram(msg)
    driver.quit()

if __name__ == "__main__":
    main()
