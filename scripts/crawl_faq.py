import os
import sys
import requests
import asyncio
from playwright.async_api import async_playwright
# 프로젝트 루트를 path에 추가하여 utils 호출 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import db_manager

async def crawl_kia(browser):
    print("Crawling Kia...")
    page = await browser.new_page()
    await page.goto("https://www.kia.com/kr/vehicles/kia-ev/guide/faq")
    
    # 아코디언 버튼들이 로드될 때까지 기다림
    await page.wait_for_selector("button.cmp-accordion__button")
    
    faq_items = await page.query_selector_all(".cmp-accordion__item")
    results = []
    
    for item in faq_items:
        question_btn = await item.query_selector("button.cmp-accordion__button")
        question = await question_btn.inner_text()
        
        # 답변을 보려면 클릭이 필요할 수 있으나, DOM에 이미 존재할 수도 있음
        answer_panel = await item.query_selector(".cmp-accordion__panel")
        answer = await answer_panel.inner_html()
        
        results.append({
            "question": question.strip(),
            "answer": answer.strip(),
            "category": "Kia EV Guide",
            "source": "기아"
        })
    await page.close()
    return results

async def crawl_ev_portal(browser):
    print("Crawling EV Portal...")
    page = await browser.new_page()
    await page.goto("https://ev.or.kr/nportal/partcptn/initFaqAction.do")
    
    # 1페이지 데이터 수집
    faq_list = await page.query_selector_all(".faq_list > dl")
    results = []
    
    for item in faq_list:
        question_el = await item.query_selector("dt")
        question_text = await question_el.inner_text()
        
        # 'Q' 텍스트 제거 및 카테고리 분리 시도
        # 형식: [카테고리] 질문내용
        question = question_text.replace("Q", "", 1).strip()
        
        category = "기타"
        if "]" in question:
            category, question = question.split("]", 1)
            category = category.replace("[", "").strip()
            question = question.strip()

        answer_el = await item.query_selector("dd")
        answer = await answer_el.inner_html()
        
        results.append({
            "question": question,
            "answer": answer.strip(),
            "category": category,
            "source": "무공해차 통합누리집"
        })
    await page.close()
    return results

def crawl_kepco():
    print("Crawling KEPCO (API)...")
    url = "https://plug.kepco.co.kr:23001/api/v1/faq"
    try:
        response = requests.get(url, verify=False) # SSL 이슈 대비
        data = response.json()
        results = []
        for item in data:
            results.append({
                "question": item.get("question", "").strip(),
                "answer": item.get("answer", "").strip(),
                "category": "KEPCO PLUG FAQ",
                "source": "한전"
            })
        return results
    except Exception as e:
        print(f"KEPCO crawling failed: {e}")
        return []

async def main():
    # 기존 데이터 삭제 (중복 방지)
    db_manager.execute_query("DELETE FROM faq_data")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 기아 수집
        kia_data = await crawl_kia(browser)
        # EV 포털 수집
        ev_data = await crawl_ev_portal(browser)
        # 한전 수집
        kepco_data = crawl_kepco()
        
        all_data = kia_data + ev_data + kepco_data
        
        print(f"Total collected: {len(all_data)}")
        
        # DB 저장
        for item in all_data:
            db_manager.execute_query(
                "INSERT INTO faq_data (question, answer, category, source) VALUES (%s, %s, %s, %s)",
                (item["question"], item["answer"], item["category"], item["source"])
            )
        
        await browser.close()
    print("Crawling finished and data saved.")

if __name__ == "__main__":
    asyncio.run(main())
