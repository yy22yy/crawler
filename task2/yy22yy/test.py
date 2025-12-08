from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import html
import time
import pandas as pd
import os

# ========================================
# 第一部分：打开浏览器和进入历史交易页面
# ========================================

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

# ========================================
# 第二部分：筛选交易状态并处理每行数据
# ========================================

# 函数：查询已成交交易
def find_completed_deals(driver):
    # 返回值：选择所有满足条件的 <tr> 行
    rows_with_deal = driver.find_elements(By.XPATH, "//table/tbody/tr[td[8]/div[text()='已成交']]")
    return rows_with_deal

# 函数：对符合条件的交易行进行点击
def process_each_deal(driver, rows_with_deal):
    
    # 循环：对满足条件的进行点击
    for i, row in enumerate(rows_with_deal):
        
            # 点击该行最右侧的按钮
            button = row.find_element(By.XPATH, "./td[12]/button")
            button.click()
            
            # 获取所有窗口句柄
            all_handles = driver.window_handles  # 返回所有窗口的句柄列表（按打开顺序）
            
            # 切换到新窗口
            driver.switch_to.window(all_handles[1])  # 切换到第二个窗口

            # 提取数据
            deal_data = catch_data(driver)
            save_to_excel(deal_data)
            
            
            # 关闭当前窗口（新窗口）
            driver.close()
            
            # 返回原窗口
            driver.switch_to.window(all_handles[0])  # 切换回第一个窗口
    

def catch_data(driver):
    """提取交易详情数据并以表格形式输出"""
    
    # 进入嵌套的iframe
    driver.switch_to.frame(0)  # 第一层iframe
    driver.switch_to.frame(0)  # 第二层iframe
    
    try:
        # 提取所有需要的字段并保存到字典
        deal_data = {}
        
        # 1. 成交时间
        deal_time_element = driver.find_element(By.ID, "ctl00_cphContent_lblChengJiaoDate")
        deal_data["成交时间"] = deal_time_element.text
        
        # 2. 竞得人
        winner_element = driver.find_element(By.ID, "ctl00_cphContent_lblJingDeRen")
        deal_data["竞得人"] = winner_element.text
        
        # 3. 交易土地面积
        trade_area_element = driver.find_element(By.ID, "ctl00_cphContent_JiaoYiMianJi_222124")
        deal_data["交易土地面积"] = trade_area_element.text
        
        # 4. 成交地价
        deal_price_element = driver.find_element(By.ID, "ctl00_cphContent_lblChengJiaoInfo")
        deal_data["成交地价"] = deal_price_element.text
        
        # 5. 地块位置
        location_element = driver.find_element(By.ID, "ctl00_cphContent_DiKuaiWeiZhi_222124")
        deal_data["地块位置"] = location_element.text
        
        # 6. 土地实际用途
        land_use_element = driver.find_element(By.ID, "ctl00_cphContent_TuDiShiJiYongTu_222124")
        deal_data["土地实际用途"] = land_use_element.text
        
        # 7. 状态
        deal_data["状态"] = "已成交"
        
        
        
        return deal_data
        
    except Exception as e:
        print(f"提取数据时出错: {e}")
        return None
    
    finally:
        # 确保切换回主文档
        driver.switch_to.default_content()


def save_to_excel(deal_data):
    """将交易数据保存到Excel文件"""
    if deal_data is None:
        print("数据为空，跳过保存")
        return
    
    # Excel文件路径
    excel_file = "交易数据.xlsx"
    
    # 将字典转换为DataFrame
    df_new = pd.DataFrame([deal_data])
    
    # 检查文件是否存在
    if os.path.exists(excel_file):
        # 如果文件存在，读取现有数据并追加新数据
        try:
            df_existing = pd.read_excel(excel_file)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except Exception as e:
            print(f"读取现有Excel文件时出错: {e}")
            df_combined = df_new
    else:
        # 如果文件不存在，直接使用新数据
        df_combined = df_new
    
    # 保存到Excel文件
    try:
        df_combined.to_excel(excel_file, index=False)
        print(f"数据已保存到 {excel_file}")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")


# ========================================
# 主程序执行
# ========================================

def main():
    """主程序"""
    # =========第一部分：浏览器设置和页面导航===================
    driver = setup_browser()
    print("第一步：成功打开浏览器")

    open_website_and_navigate(driver)
    print("第二步：成功打开历史交易页面")

    time.sleep(5)
    # 等待页面加载完成，等待表格元素出现
    for i in range(10):          # 0~9 共 10 次
        # 等待

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr[td[8]/div[text()='已成交']]")))
        completed_deals = find_completed_deals(driver)
        if completed_deals:
            process_each_deal(driver, completed_deals)
            print("第五步：点击交易详情成功执行")
        else:
            print("第五步：未筛选到交易数据")
    
        driver.find_element(By.XPATH,"/html/body/div/div/div/div[2]/div[3]/div/div/div[2]/div[3]/div/ul/li[9]/a").click()
        time.sleep(15)
        
    print("全部完成！！")
    driver.quit()
    

# 运行主程序
if __name__ == "__main__":
    main()


