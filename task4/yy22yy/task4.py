import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from lxml import etree
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html
import time
import pandas as pd
import os

# 邮件配置
SENDER_EMAIL = "发送邮件"
SENDER_AUTH_CODE =  "授权码"
RECEIVER_EMAIL = "接受邮件" 

# 全局变量
xlh0 = ""  # 旧的序列号
xlh1 = ""  # 新的序列号

def setup_browser():
    """设置并启动浏览器"""
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)  # 保持浏览器打开
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def open_website_and_navigate(driver):
    """打开网站并进入历史交易页面"""
    # 打开主页
    url = "http://jy.ggzy.foshan.gov.cn:3680/TPBank/newweb/framehtml/onlineTradex/index.html"
    driver.get(url)    
    # 点击进入历史交易页面
    button = driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/ul/li[3]/a")
    button.click()
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/div[2]/div[3]/div/div/div[2]/div[2]/div/table/tbody/tr[1]/td[2]/span")))
    return driver

def get_serial_number(driver):
    """获取序列号并比较变化"""
    global xlh0, xlh1
    
    # 获取页面源码
    page_source = driver.page_source
    tree = etree.HTML(page_source)
    
    # 获取序列号
    try:
        xpath = "/html/body/div/div/div/div[2]/div[3]/div/div/div[2]/div[2]/div/table/tbody/tr[1]/td[2]/span"
        xlh1 = tree.xpath(xpath)[0].text.strip()
    except:
        xlh1 = "获取失败"
    
    # 比较序列号
    if xlh0 != xlh1:
        if xlh0:  # 如果不是第一次运行
            send_email(f"有内容更新，内容为: {xlh1}")
        xlh0 = xlh1
    else:
        send_email("无内容更新")
    
    return xlh1

def send_email(content):
    """发送邮件函数"""
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "网页监测结果"
    
    try:
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(SENDER_EMAIL, SENDER_AUTH_CODE)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        server.quit()
        print(f"{datetime.now()} - 邮件发送成功: {content}")
    except Exception as e:
        print(f"{datetime.now()} - 邮件发送失败: {str(e)}")

def monitor():
    """主监测函数"""
    print("程序开始运行...")
    
    # 设置监测时间段（1分钟）和间隔（15秒）
    end_time = datetime.now() + timedelta(minutes=1)
    interval = 15  # 秒
    
    driver = setup_browser()
    print("第一步：成功打开浏览器")

    open_website_and_navigate(driver)
    print("第二步：成功打开历史交易页面")

    time.sleep(5)
    
    try:
        while datetime.now() < end_time:
            print(f"{datetime.now()} - 开始监测...")
            serial_number = get_serial_number(driver)
            print(f"当前序列号: {serial_number}")
            
            # 刷新页面
            driver.refresh()
            time.sleep(5)  # 等待页面刷新
            
            # 等待下一个监测周期
            time.sleep(interval)
    finally:
        driver.quit()
        print("程序结束")

if __name__ == "__main__":
    monitor()
