#!/usr/bin/env python3
"""
FreeCloud 多账号自动签到脚本
环境变量：
FC_ACCOUNTS = 账号1:密码1,账号2:密码2
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ================= 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

CHROME_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"


class FreeCloudAutoCheckin:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        options = Options()

        # ✅ GitHub Actions 必备参数
        options.binary_location = CHROME_BINARY
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = Service(CHROMEDRIVER_PATH)

        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self):
        logger.info("登录 FreeCloud")

        self.driver.get("https://panel.freecloud.ltd/clientarea.php")
        time.sleep(3)

        self.driver.find_element(By.NAME, "username").send_keys(self.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        self.driver.find_element(By.NAME, "password").submit()

        time.sleep(5)

        if "logout" in self.driver.page_source.lower():
            logger.info("登录成功")
            return True
        raise Exception("登录失败")

    def checkin(self):
        logger.info("执行签到")

        self.driver.get("https://panel.freecloud.ltd/clientarea.php?action=checkin")
        time.sleep(3)

        html = self.driver.page_source

        if "签到成功" in html:
            return "签到成功"
        if "已经签到" in html:
            return "今日已签到"
        if "首次奖励" in html:
            return "已领取首次奖励"

        return "签到完成（未识别状态）"

    def run(self):
        try:
            self.login()
            result = self.checkin()
            return True, result
        except Exception as e:
            logger.error(str(e))
            return False, str(e)
        finally:
            if self.driver:
                self.driver.quit()


class MultiAccountManager:
    def __init__(self):
        self.accounts = self.load_accounts()

    def load_accounts(self):
        raw = os.getenv("FC_ACCOUNTS", "").strip()
        if not raw:
            raise ValueError("未设置 FC_ACCOUNTS")

        accounts = []
        for pair in raw.split(","):
            if ":" in pair:
                user, pwd = pair.split(":", 1)
                accounts.append((user.strip(), pwd.strip()))

        if not accounts:
            raise ValueError("账号格式错误")

        return accounts

    def run_all(self):
        results = []
        for idx, (user, pwd) in enumerate(self.accounts, 1):
            logger.info(f"处理账号 {idx}/{len(self.accounts)}")
            checker = FreeCloudAutoCheckin(user, pwd)
            success, result = checker.run()
            results.append((user, success, result))
            time.sleep(5)
        return results


def main():
    logger.info("开始 FreeCloud 多账号签到")
    manager = MultiAccountManager()
    results = manager.run_all()

    success_count = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    logger.info(f"完成：{success_count}/{total}")

    for user, ok, msg in results:
        masked = user[:3] + "***"
        status = "✅" if ok else "❌"
        logger.info(f"{status} {masked} - {msg}")

    exit(0)


if __name__ == "__main__":
    main()
