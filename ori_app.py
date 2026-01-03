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
        
# --- 找到 [2. 动态进入服务器详情页] 这一段，替换为以下内容 ---
        print("登录成功，直接跳转至服务器详情页...")
        # 直接使用你截图中的服务器详情地址，避开首页点击不稳定的问题
        target_url = "https://panel.orihost.com/server/5939989e"
        driver.get(target_url)
        time.sleep(5) # 等待页面加载完成

# 3. 增强版续订点击逻辑
        print("正在寻找续订按钮...")
        # 优化 XPath：只要包含该文本的元素都匹配，不限标签
        renew_xpath = "//*[contains(text(), 'Click Here To Renew')]"
        
        # 等待元素存在（不仅仅是可点击）
        renew_element = wait.until(EC.presence_of_element_located((By.XPATH, renew_xpath)))
        
        # 滚动并使用 JS 强制执行，无视遮挡或可见性
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", renew_element)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", renew_element)
        print("已触发续订弹窗...")

        # 4. 二次确认
        confirm_btn_xpath = "//button[contains(text(), 'Okay')]"
        # 有时弹窗动画需要时间，先等待存在再点击
        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_btn_xpath)))
        confirm_btn.click()
        print("续订确认已点击")
        
        # 抓取最新时间
# 获取最终时间
        time.sleep(5)
        days_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[p[contains(text(), 'DAYS UNTIL RENEWAL')]]/p[1]")))
        current_days = days_element.text.strip()
        
        # 这里的消息会告诉你续订后的具体天数
        success_msg = f"✅ Orihost 自动续订成功！\n当前剩余：{current_days} (上限21天)"
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
