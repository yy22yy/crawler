
# coding: utf-8

# In[5]:


import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service  # 修改为Edge的Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

# 初始化数据存储
data = {
    "交易编号": [],
    "成交时间": [],
    "竞得人": [],
    "交易土地面积": [],
    "成交地价": [],
    "地块位置": [],
    "土地实际用途": []
}

def wait_for_element(driver, selector, timeout=30):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException:
        print(f"等待元素超时: {selector}")
        return None

def get_element_text(driver, selector, default="NULL"):
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        return element.text.strip() if element.text.strip() else default
    except NoSuchElementException:
        return default

def scrape_page(driver):
    # 等待表格加载
    wait_for_element(driver, "#lsjyDom > tr:nth-child(1) > td:nth-child(1) > span")
    
    # 获取当前窗口句柄
    main_window = driver.current_window_handle
    
    # 遍历每一行
    for i in range(1, 11):
        print(f"正在处理第{i}行...")
        
        # 检查状态是否为"已成交"
        status_selector = f"#lsjyDom > tr:nth-child({i}) > td:nth-child(8) > div"
        status = get_element_text(driver, status_selector)
        
        if status == "已成交":
            try:
                # 点击查看按钮
                view_btn_selector = f"#lsjyDom > tr:nth-child({i}) > td:nth-child(12) > button"
                view_btn = wait_for_element(driver, view_btn_selector)
                if view_btn:
                    view_btn.click()
                    time.sleep(1)  # 等待新窗口打开
                    
                    # 切换到新窗口
                    new_window = [window for window in driver.window_handles if window != main_window][0]
                    driver.switch_to.window(new_window)
                    
                    try:
                        # 等待并切换到第一层iframe
                        wait_for_element(driver, "iframe[src*='TDJY_BasicInfoFrame.aspx']")
                        iframe1 = driver.find_element(By.CSS_SELECTOR, "iframe[src*='TDJY_BasicInfoFrame.aspx']")
                        driver.switch_to.frame(iframe1)
                        
                        # 等待并切换到第二层iframe
                        wait_for_element(driver, "iframe[src*='TDJY_BasicInfoHistory.aspx']")
                        iframe2 = driver.find_element(By.CSS_SELECTOR, "iframe[src*='TDJY_BasicInfoHistory.aspx']")
                        driver.switch_to.frame(iframe2)
                        
                        # 提取数据
                        data["交易编号"].append(get_element_text(driver, "#ctl00_cphContent_DiKuaiBianHao_222124"))
                        data["成交时间"].append(get_element_text(driver, "#ctl00_cphContent_lblChengJiaoDate"))
                        data["竞得人"].append(get_element_text(driver, "#ctl00_cphContent_lblJingDeRen"))
                        data["交易土地面积"].append(get_element_text(driver, "#ctl00_cphContent_tdContainer > div:nth-child(1) > div.openwin-accordion-right > div.openwin-accordion-content > table > tbody > tr:nth-child(8) > td:nth-child(2)"))
                        data["成交地价"].append(get_element_text(driver, "#ctl00_cphContent_lblChengJiaoInfo"))
                        data["地块位置"].append(get_element_text(driver, "#ctl00_cphContent_DiKuaiWeiZhi_222124"))
                        data["土地实际用途"].append(get_element_text(driver, "#ctl00_cphContent_TuDiShiJiYongTu_222124"))
                        
                    except Exception as e:
                        print(f"提取数据时出错: {str(e)}")
                        # 添加空数据以保持数据对齐
                        for key in data:
                            data[key].append("NULL")
                    
                    finally:
                        # 切换回默认内容并关闭当前窗口
                        driver.switch_to.default_content()
                        driver.close()
                        driver.switch_to.window(main_window)
                        time.sleep(1)  # 请求间隔
                
            except Exception as e:
                print(f"处理行{i}时出错: {str(e)}")
                continue

def main():
    # 初始化Edge浏览器
    options = webdriver.EdgeOptions()  # 修改为EdgeOptions
    options.add_argument("--start-maximized")
    
    # 指定EdgeDriver路径（重要！修改为你的实际路径）
    
    service = Service(executable_path=r'C:\Myapps\Egddriver\edgedriver_win64\msedgedriver.exe')  # 修改为EdgeDriver路径
    
    driver = webdriver.Edge(service=service, options=options)  # 修改为Edge
    
    try:
        # 打开网址
        driver.get("http://jy.ggzy.foshan.gov.cn:3680/TPBank/newweb/framehtml/onlineTradex/index.html")
        
        # 点击历史交易按钮
        history_btn = wait_for_element(driver, "body > div > div > div > div.ewb-fa > ul > li:nth-child(3) > a")
        if history_btn:
            history_btn.click()
            time.sleep(3)  # 等待页面加载
            
            # 遍历1-10页
            for page in range(1, 11):
                print(f"\n正在处理第{page}页...")
                
                # 输入页码并跳转
                page_input = wait_for_element(driver, "#page-three > div.m-pagination-jump > div > input[type=text]")
                go_btn = wait_for_element(driver, "#page-three > div.m-pagination-jump > div > button")
                
                if page_input and go_btn:
                    page_input.clear()
                    page_input.send_keys(str(page))
                    go_btn.click()
                    time.sleep(3)  # 等待页面加载
                    
                    # 爬取当前页
                    scrape_page(driver)
        
        # 保存数据到Excel
        df = pd.DataFrame(data)
        df.to_excel("task2Date.xlsx", index=False)
        print("\n数据已保存到task2Date_selenium.xlsx")
        
    except Exception as e:
        print(f"主程序出错: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()

