from unittest import result
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from PIL import Image 
import time
import pandas as pd
import os
import io
import json
import re
import base64
import requests
from config import API_URL, API_TOKEN
from page import page_begin, page_end


# ========================================
# 初始化设置：配置环境变量与加载城市文件
# 1. 千问大模型配置
def get_qianwen_config():
    """获取千问大模型配置"""
    return {
        "api_url": API_URL,
        "api_token": API_TOKEN
    }

# 2. 加载城市配置文件
def load_city_config():
    """加载城市配置文件"""
    try:
        with open('city_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("配置文件 city_config.json 不存在，请先创建配置文件")
        return None
    except json.JSONDecodeError:
        print("配置文件格式错误，请检查JSON格式")
        return None
# 初始化设置：配置环境变量与加载城市文件
# ========================================



# ========================================
# 第一部分：打开浏览器和进入历史交易页面


# 1. 启动浏览器
def setup_browser():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)  # 保持浏览器打开
    driver = webdriver.Chrome(options=chrome_options) #Chrome浏览器
    return driver

# 2.打开城市选择框
def open_city_selector(driver):
    """打开城市选择框"""
    try:
        wait = WebDriverWait(driver, 10)
        city_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/header/div/div[1]/div[2]/button')))
        city_button.click()
        print("成功打开城市选择框")
        return True
    except Exception as e:
        print(f"打开城市选择框失败: {e}")
        return False

# 3. 依据config文件，在selector中选择对应城市
def select_city(driver, city_name, city_config):
    try:
        # 检查城市是否在配置中
        if city_name not in city_config['cities']:
            print(f"城市 '{city_name}' 不在配置文件中")
            return False
        
        city_info = city_config['cities'][city_name]
        city_xpath = city_info['xpath']
        
        # 等待城市选择框出现
        wait = WebDriverWait(driver, 10)
        
        # 等待城市列表加载
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "site-list")))
        
        # 点击指定城市
        city_element = wait.until(EC.element_to_be_clickable((By.XPATH, city_xpath)))
        city_element.click()
        
        print(f"成功选择城市: {city_name}")
        return True

    except Exception as e:
        print(f"选择城市时出错: {e}")
        return False


# 4.进入土地矿业并且选择"土地使用权交易公告"
def navigate_to_land_page(driver):
    try:
        wait = WebDriverWait(driver, 10)
        land_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/article/main/div/div[1]/div/aside/ul/li[2]')))
        land_button.click()
        print("成功进入土地矿业页面")
        
        # 点击"土地交易结果"
        # 由于结果会改变 所以要进行特殊处理
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//ul[@class="item-right"]//li[contains(text(), "土地使用权交易结果公告")]')))
            next_button.click()
            print("成功点击交易结果")
            return True
        except Exception as e:
            print(f"该城市没有土地使用权交易结果公告: {e}")
            return False

    except Exception as e:
        print(f"点击交易结果失败: {e}")
        return False

# 5.调用函数（2-4）完成进入城市对应结果的页面
def process_single_city(driver, city_name, city_config):
    """处理单个城市 - 只进行城市选择和页面导航"""
    print(f"\n开始处理城市: {city_name}")
    
    try:
        # 1.打开网站
        url = "https://ygp.gdzwfw.gov.cn/#/44/jygg"
        driver.get(url)
        print(f"打开网站: {url}")
        
        # 等待页面加载
        time.sleep(2)
        
        # 2.打开城市选择框
        if not open_city_selector(driver):
            return False
        
        # 3.选择城市
        if not select_city(driver, city_name, city_config):
            return False
        
        # 等待页面跳转完成
        time.sleep(3)
        
        # 4.进入土地矿业页面并且选择结果
        if not navigate_to_land_page(driver):
            return False
        
        # 等待页面加载完成
        time.sleep(2)
        
        print(f"城市 {city_name} 处理完成 - 已成功进入土地矿业页面")
        return True
        
    except Exception as e:
        print(f"处理城市 {city_name} 时出错: {e}")
        return False

# 6.对页面上的10个项目进行点击并提取数据
def click_and_catch(driver):

    print("开始爬取")
    list_items = driver.find_elements(By.XPATH, "/html/body/div[1]/article/main/section/ul/li")

    # 循环处理每个列表项
    for idx, item in enumerate(list_items, start=1):
        try:
            # 构建每个项目的h2按钮的XPath
            button_xpath = f"/html/body/div[1]/article/main/section/ul/li[{idx}]/h2"
            button = driver.find_element(By.XPATH, button_xpath)
            button.click()
            # 获取所有窗口句柄
            all_handles = driver.window_handles
            # 切换到新窗口（如果有新窗口打开）
            if len(all_handles) > 1:
                # 切换标签页
                driver.switch_to.window(all_handles[1])
                # 调用截图函数
                driver.wait = WebDriverWait(driver, 10)
                image_path = catch_photo(driver)
                if image_path:
                    # 调用千问大模型进行图像识别
                    extracted_data = extract_data_with_qianwen(image_path)
                    
                    print("提取的数据:", extracted_data)
                    
                    # 将提取的数据保存到Excel
                    save_to_excel(extracted_data)

                # 关闭当前窗口（新窗口）
                driver.close()
                
                # 返回原窗口
                driver.switch_to.window(all_handles[0])
            
        except Exception as e:
            print(f"处理第 {idx} 个项目时出错: {str(e)}")
            continue

    print("全部点击完成！")


## 6.1--截图程序，对shadow--root 进行截图
def catch_photo(driver):
    print("开始截图")
    try:
        # 1. 使用显式等待确保元素出现
        wait = WebDriverWait(driver, 15)
        
        # 等待主要内容区域加载完成
        element = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/main/div[3]/section[2]")))
        
        # 等待元素可见
        wait.until(EC.visibility_of(element))
        
        # 2. 点击到对应区域
        
        driver.find_element(By.XPATH, "//html/body/div[1]/main/div[3]/div/div/div/div/div/div[2]/a").click()

        # 3. 直接截取元素截图并保存为 "临时截取.png"
        save_path = "临时截取.png"
        element.screenshot(save_path)  # 直接保存元素截图到文件
        print(f"截图已保存: {save_path}")
        return save_path  # 返回图片路径
        
    except Exception as e:
        print(f"截图失败: {e}")
        return None

## 6.2--使用千问大模型从图片中提取文字和数据
def extract_data_with_qianwen(image_path):
    """使用千问大模型从图片提取结构化数据"""
    try:
        # 获取配置
        config = get_qianwen_config()
        
        # 将图片转换为base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 构建请求数据
        headers = {
            "Authorization": f"Bearer {config['api_token']}",
            "Content-Type": "application/json"
        }
        
        # 构建提示词
        prompt = """
        请分析这张土地交易结果公告的图片，提取以下关键信息并以JSON格式返回：
        
        需要提取的字段：
        1. 竞得人：获得土地的公司或个人名称
        2. 成交总价：土地成交的总价格（包含单位）
        3. 成交时间：土地成交的具体时间
        4. 宗地编号：土地的编号
        5. 宗地位置：土地的具体位置或地址
        6. 土地用途：土地的用途类型
        7. 用地面积：土地的面积（包含单位）
        
        请严格按照以下JSON格式返回，如果某个字段无法识别，请设置为null：
        {
            "竞得人": "提取的竞得人信息",
            "成交总价": "提取的成交总价",
            "成交时间": "提取的成交时间",
            "宗地编号": "提取的宗地编号", 
            "宗地位置": "提取的宗地位置",
            "土地用途": "提取的土地用途",
            "用地面积": "提取的用地面积"
        }
        
        请仔细识别图片中的文字内容，确保提取的信息准确无误。
        """
        
        data = {
            "model": "qwen-vl-plus",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        # 发送请求
        response = requests.post(f"{config['api_url']}/chat/completions", 
                               headers=headers, 
                               json=data, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分（可能包含在代码块中）
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    json_content = content[json_start:json_end].strip()
                elif '{' in content and '}' in content:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                extracted_data = json.loads(json_content)
                print("千问大模型识别成功")
                
                # 删除临时图片文件
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"已删除临时文件: {image_path}")
                
                return extracted_data
                
            except json.JSONDecodeError as e:
                print(f"解析JSON响应失败: {e}")
                print(f"原始响应: {content}")
                return create_empty_result()
        else:
            print(f"API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return create_empty_result()
            
    except Exception as e:
        print(f"千问大模型识别失败: {e}")
        return create_empty_result()

def create_empty_result():
    """创建空的结果字典"""
    return {
        "竞得人": None,
        "成交总价": None,
        "成交时间": None,
        "宗地编号": None,
        "宗地位置": None,
        "土地用途": None,
        "用地面积": None
    }

# 6.4--将文字保存到excel
def save_to_excel(deal_data):
    """将交易数据保存到Excel文件"""
    if deal_data is None:
        print("数据为空，跳过保存")
        return

    # Excel文件路径
    excel_file = "交易结果.xlsx"
    
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
    """主程序 - 循环处理多个城市"""
    # 加载 所有城市的 配置文件
    city_config = load_city_config()
    if not city_config:
        return
    
    # 获取目标城市列表
    target_cities = city_config['target_cities']
    print(f"准备处理以下城市: {', '.join(target_cities)}")
    
    # 启动浏览器
    driver = setup_browser()
    print("成功启动浏览器")
    
    # 循环处理每个城市
    successful_cities = []
    failed_cities = []
    no_data_cities = []  # 新增：记录没有土地使用权交易结果公告的城市
    
    for i, city_name in enumerate(target_cities, 1):
        print(f"\n处理进度: {i}/{len(target_cities)}")
        
        # 处理单个城市
        success = process_single_city(driver, city_name, city_config)
        
        if not success:
            # 如果城市处理失败（包括没有土地使用权交易结果公告），记录并继续下一个城市
            print(f"城市 {city_name} 没有土地使用权交易结果公告，跳过该城市")
            no_data_cities.append(city_name)
            
            # 如果不是最后一个城市，继续处理下一个城市
            if i < len(target_cities):
                print("继续处理下一个城市...")
                time.sleep(2)
            continue
        
        # 如果城市处理成功，进行数据爬取
        try:
            for j in range(page_begin, page_end):
                # 点击对应页面并且进行爬取
                if j == page_begin:
                    wait = WebDriverWait(driver, 10)
                    page_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/article/main/section/div[2]/div/div/input")))
                    # 2. 清空输入框并输入页码
                    page_input.clear()
                    page_input.send_keys(str(page_begin))

                driver.find_element(By.XPATH, "/html/body/div[1]/article/main/section/div[2]/div/button").click()

                time.sleep(3)  # 等待页面加载
               
                if j == page_end:
                    click_and_catch(driver)
                else:
                    click_and_catch(driver)
                    driver.find_element(By.XPATH, "/html/body/div[1]/article/main/section/div[2]/button[2]").click()
                    time.sleep(1)
            
            successful_cities.append(city_name)
            
        except Exception as e:
            print(f"爬取城市 {city_name} 数据时出错: {e}")
            failed_cities.append(city_name)
        
        # 如果不是最后一个城市，等待后处理下一个城市
        if i < len(target_cities):
            print("等待5秒后处理下一个城市...")
            time.sleep(5)
    
    # 输出处理结果
    print(f"\n{'='*60}")
    print("所有城市处理完成！")
    print(f"成功处理的城市 ({len(successful_cities)}): {', '.join(successful_cities)}")
    if failed_cities:
        print(f"处理失败的城市 ({len(failed_cities)}): {', '.join(failed_cities)}")
    print(f"{'='*60}")
    
    # 关闭浏览器
    driver.quit()
    print("浏览器已关闭")

# 运行主程序
if __name__ == "__main__":
    main()


