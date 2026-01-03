import os
import time
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def send_tg(msg):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          json={"chat_id": chat_id, "text": msg}, timeout=10)
        except Exception as e:
            print(f"发送TG消息失败: {e}")

def run():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 模拟真实浏览器特征
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        print("开始登录...")
        driver.get("https://panel.orihost.com/auth/login")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(os.environ.get("ORIHOST_USER"))
        driver.find_element(By.NAME, "password").send_keys(os.environ.get("ORIHOST_PASS"))
        driver.find_element(By.XPATH, "//button[contains(., 'Sign In')]").click()
        
        print("登录成功，搜索服务器卡片...")
        # 动态定位：点击第一个包含 IP 地址格式（点号）的卡片
        server_entry_xpath = "//div[contains(@class, 'cursor-pointer')]//p[contains(text(), '.')]"
        server_entry = wait.until(EC.element_to_be_clickable((By.XPATH, server_entry_xpath)))
        server_entry.click()

        print("进入服务器详情页，尝试续订...")
        # 续订按钮
        renew_trigger = wait.until(EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Click Here To Renew')]")))
        renew_trigger.click()

        # 二次确认按钮
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Okay')]")))
        confirm_btn.click()
        
        print("续订指令已发送，等待页面刷新...")
        time.sleep(8)
        driver.refresh()
        
        # 抓取最新时间
        days_xpath = "//div[p[contains(text(), 'DAYS UNTIL RENEWAL')]]/p[1]"
        days = wait.until(EC.presence_of_element_located((By.XPATH, days_xpath))).text
        
        success_msg = f"✅ Orihost 自动续订成功！\n当前剩余时间：{days.strip()}"
        print(success_msg)
        send_tg(success_msg)

    except Exception as e:
        driver.save_screenshot("error_screenshot.png") 
        err_msg = f"❌ Orihost 续订失败\n原因：{str(e)}"
        print(err_msg)
        send_tg(err_msg)
        raise e # 抛出异常让 GitHub Actions 显示失败
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
