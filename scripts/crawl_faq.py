import requests
import sys
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import db_manager

def save_faq(question, answer, category, source):
    """DB에 FAQ 데이터 저장"""
    if not question or not answer:
        return
    
    # 확실히 문자열로 변환
    question = str(question).strip()
    answer = str(answer).strip()
    category = str(category or "General").strip()
    source = str(source).strip()
    
    query = """
    INSERT INTO faq_data (question, answer, category, source)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    answer = VALUES(answer),
    category = VALUES(category)
    """
    try:
        db_manager.execute_query(query, (question, answer, category, source))
    except Exception as e:
        print(f"[{source}] DB Save Error: {e}")

def crawl_hyundai():
    print("[Hyundai] Starting crawl...")
    url = "https://www.hyundai.com/kr/ko/gw/customer-support/v1/customer-support/faq/list"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "ep-channel": "homepage",
        "referer": "https://www.hyundai.com/kr/ko/e/customer/center/faq",
        "origin": "https://www.hyundai.com",
        "accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    categories = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
    count = 0
    for cat in categories:
        page = 1
        while page <= 2:
            payload = {"siteTypeCode": "H", "faqCategoryCode": cat, "pageNo": page, "pageSize": 10}
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                data = response.json()
                faq_list = data.get("data", {}).get("list", [])
                if not faq_list: break
                for item in faq_list:
                    save_faq(item.get("faqQuestion"), item.get("faqAnswer"), item.get("faqCategoryName"), "Hyundai")
                    count += 1
                page += 1
            except: break
    print(f"[Hyundai] Total {count} items.")

def crawl_kia():
    print("[Kia] Starting crawl...")
    url = "https://www.kia.com/kr/services/ko/faq.search?searchTag=kwp:kr/faq/top10"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        faq_list = data.get("data", {}).get("faqList", {}).get("items", [])
        count = 0
        for item in faq_list:
            save_faq(item.get("question"), item.get("answer"), "인기 FAQ", "Kia")
            count += 1
        print(f"[Kia] Total {count} items.")
    except Exception as e: print(f"[Kia] Error: {e}")

def crawl_kepco():
    print("[KEPCO] Starting crawl...")
    url = "https://plug.kepco.co.kr:23001/api/v1/faq"
    try:
        response = requests.get(url, timeout=10)
        faq_list = response.json()
        for item in faq_list:
            save_faq(item.get("question"), item.get("answer"), item.get("category"), "KEPCO")
        print(f"[KEPCO] Total {len(faq_list)} items.")
    except Exception as e: print(f"[KEPCO] Error: {e}")

def crawl_ev_portal():
    print("[EV Portal] Starting crawl...")
    url = "https://www.ev.or.kr/nportal/partcptn/initFaqAction.do"
    try:
        response = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        dts = soup.find_all('dt')
        dds = soup.find_all('dd')
        count = 0
        for q, a in zip(dts, dds):
            q_txt = q.get_text(strip=True)
            if q_txt and len(q_txt) > 5:
                save_faq(re.sub(r'^[QA]\.?\s*', '', q_txt), str(a), "환경부 정책", "EV Portal")
                count += 1
        print(f"[EV Portal] Total {count} items.")
    except Exception as e: print(f"[EV Portal] Error: {e}")

if __name__ == "__main__":
    crawl_hyundai()
    crawl_kia()
    crawl_kepco()
    crawl_ev_portal()
