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
    
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 40)

    try:
        # 1. 登录
        print("开始登录...")
        driver.get("https://panel.orihost.com/auth/login")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(os.environ.get("ORIHOST_USER"))
        driver.find_element(By.NAME, "password").send_keys(os.environ.get("ORIHOST_PASS"))
        driver.find_element(By.XPATH, "//button[contains(., 'Sign In')]").click()
        
        # 2. 跳转详情页
        time.sleep(15) 
        print("跳转至服务器详情页...")
        driver.get("https://panel.orihost.com/server/5939989e")
        time.sleep(15) # 详情页黑屏控制台加载极慢，必须等待

        # 3. 使用 JS 深度扫描并点击续订区域
        print("执行 JS 深度扫描定位...")
        # 逻辑：寻找包含 'RENEWAL' 文本的卡片，并点击该卡片的底部区域
        script = """
        let elements = document.querySelectorAll('div, p, span');
        for (let el of elements) {
            if (el.innerText && el.innerText.includes('RENEWAL')) {
                let parentCard = el.closest('div');
                if (parentCard) {
                    parentCard.scrollIntoView({block: 'center'});
                    parentCard.click();
                    return true;
                }
            }
        }
        return false;
        """
        success = driver.execute_script(script)
        
        if not success:
            print("JS 扫描失败，尝试固定坐标兜底点击...")
            # 根据 1920x1080 分辨率下右侧栏的大致位置进行点击
            driver.execute_script("document.elementFromPoint(1600, 900).click();")
        
        # 4. 确认弹窗
        print("等待确认弹窗...")
        time.sleep(3)
        # 弹窗按钮通常是红色 'Okay'
        ok_xpath = "//button[contains(@class, 'bg-red') or contains(text(), 'Okay') or contains(., 'Okay')]"
        ok_btn = wait.until(EC.element_to_be_clickable((By.XPATH, ok_xpath)))
        ok_btn.click()
        print("续订确认已完成")

        # 5. 结果抓取
        time.sleep(10)
        driver.refresh()
        time.sleep(5)
        # 获取天数
        res = driver.execute_script("return document.body.innerText.match(/(\d+)\s*days/)[0] || '未知';")
        
        msg = f"✅ Orihost 自动续订任务已执行！\n检测到当前：{res}"
        print(msg)
        send_tg(msg)

    except Exception as e:
        driver.save_screenshot("error_screenshot.png")
        err_msg = f"❌ 续订流程异常：{str(e)[:100]}"
        print(err_msg)
        send_tg(err_msg)
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
