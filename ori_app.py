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
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    
    driver = uc.Chrome(options=options)
    # 增加全局隐式等待
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 45) # 增加到45秒，详情页渲染较慢

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

# 3. 暴力寻找续订点击位
        print("寻找续订入口...")
        # 方案：定位包含 'DAYS UNTIL RENEWAL' 的 div，并点击它最后一部分
        # 这是为了绕过可能无法直接识别文本 'Click Here To Renew' 的问题
        renew_box_xpath = "//div[p[contains(text(), 'DAYS UNTIL RENEWAL')]]"
        
        try:
            target = wait.until(EC.presence_of_element_located((By.XPATH, renew_box_xpath)))
            print("找到续订区域，执行强制点击...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            time.sleep(2)
            # 点击该容器，通常点击文字周围也会触发跳转
            driver.execute_script("arguments[0].click();", target)
        except:
            # 备选方案：尝试更简单的文本匹配
            print("主要方案失败，尝试备选文本点击...")
            fallback = driver.find_element(By.XPATH, "//*[contains(text(), 'Renew')]")
            driver.execute_script("arguments[0].click();", fallback)

        # 4. 二次确认弹窗
        print("等待 'Okay' 按钮...")
        # 弹窗按钮通常在点击后 1-2 秒出现
        ok_btn_xpath = "//button[text()='Okay' or contains(., 'Okay')]"
        ok_btn = wait.until(EC.element_to_be_clickable((By.XPATH, ok_btn_xpath)))
        ok_btn.click()
        print("确认按钮已点击！")
        
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
