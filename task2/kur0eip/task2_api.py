
# coding: utf-8

# In[7]:


import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# API配置
API_URL = "http://fw.ggzy.foshan.gov.cn:8080/EpointPhoneService_Web/api/web/Web_GetList"
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "http://jy.ggzy.foshan.gov.cn:3680"
}

# 配置重试策略（关键改进点）
retry_strategy = Retry(
    total=3,  # 最大重试次数
    backoff_factor=1,  # 重试等待时间：1, 2, 4秒
    status_forcelist=[500, 502, 503, 504, 408],
    allowed_methods=["POST"]
)

# 创建带重试的Session
session = requests.Session()
session.mount("http://", HTTPAdapter(max_retries=retry_strategy))
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

def get_api_data(page):
    """获取API数据（改进超时处理）"""
    payload = {
        "ValidateData": "Epoint_WebSerivce_**##0601",
        "paras": {
            "UseType": "tdjyjyls",
            "CurrentPageIndex": page,
            "PageSize": 10
        }
    }
    try:
        # 设置连接超时5秒，读取超时30秒（原10秒）
        resp = session.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            timeout=(5, 30)  # 连接超时5秒，读取超时30秒
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print(f"第{page}页请求超时（30秒），已重试仍失败")
        return None
    except Exception as e:
        print(f"第{page}页请求失败: {str(e)}")
        return None

def transform_url(original_url):
    """转换URL格式"""
    guid = original_url.split("BiaoDiGuid=")[1]
    return f"http://jy.ggzy.foshan.gov.cn:3680/TPBank/TDJYZtbMis_FS/Pages/WebShow/TDJY_BasicInfoHistory.aspx?IsYuanXing=1&DiKuaiGuid={guid}&RowGuid={guid}&PreDiKuaiGuid="

def get_land_area(detail_url):
    """从详情页获取土地面积（增加超时保护）"""
    try:
        resp = session.get(detail_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        area_selector = "#ctl00_cphContent_JiaoYiMianJi_222124"
        area_element = soup.select_one(area_selector)
        return area_element.text.strip() if area_element else "NULL"
    except Exception as e:
        print(f"获取土地面积失败: {detail_url} - {str(e)}")
        return "NULL"

def parse_item(item):
    """解析单条数据"""
    detail_url = transform_url(item["Url"])
    return {
        "交易编号": item.get("DiKuaiBianHao", ""),
        "成交时间": item.get("ChengJiaoDate", "").split()[0].replace("/", "-"),
        "竞得人": item.get("JingDeRen", ""),
        "成交地价(万元)": item.get("ChengJiaoPrice", "").replace("地价:", "").replace("万元", ""),
        "地块位置": item.get("DiKuaiWeiZhi", ""),
        "土地实际用途": item.get("TuDiYongTuType1Code", "").replace("用地·", ""),
        "交易土地面积": get_land_area(detail_url)
    }

def main():
    all_data = []
    
    for page in range(1, 11):
        # 智能延迟（2-5秒随机）
        delay = random.uniform(2, 5)
        print(f"正在处理第{page}页，等待{delay:.1f}秒...")
        time.sleep(delay)
        
        json_data = get_api_data(page)
        if not json_data or "UserArea" not in json_data:
            continue
            
        for item in json_data["UserArea"]["InfoList"]:
            if item.get("Status") == "已成交":
                all_data.append(parse_item(item))
    
    # 保存结果
    df = pd.DataFrame(all_data)
    df.to_excel("task2Date_api.xlsx", index=False)
    print(f"数据已保存，成功获取{len(df)}条数据")

if __name__ == "__main__":
    main()

