import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from utils.db_manager import db_manager

# --- 메인 대시보드 페이지 함수 ---
def dashboard_page():
    # 지역명 매핑
    REGION_MAP = {
        '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', '인천': '인천광역시',
        '광주': '광주광역시', '대전': '대전광역시', '울산': '울산광역시', '세종': '세종특별자치시',
        '경기': '경기도', '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
        '전북': '전라북도', '전남': '전라남도', '경북': '경상북도', '경남': '경상남도', '제주': '제주특별자치도'
    }

    @st.cache_data
    def load_all_data():
        geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
        try:
            response = requests.get(geojson_url, timeout=5)
            geojson = response.json()
        except:
            geojson = None
        try:
            query = "SELECT region, year, count_ev, count_charger FROM regional_ev_status"
            df_db = db_manager.fetch_query(query)
            if not df_db.empty:
                df_db['region_full'] = df_db['region'].map(REGION_MAP)
        except:
            df_db = pd.DataFrame()
        return geojson, df_db

    geojson, df_db = load_all_data()

    if df_db.empty:
        st.title("🌱 전국 친환경차 현황 대시보드")
        st.warning("데이터베이스에 표시할 데이터가 없습니다.")
        st.info("MySQL 컨테이너를 실행하고 기초 데이터를 넣어주세요.")
        return

    st.title("🌱 전국 친환경차 현황 대시보드")
    
    latest_year = df_db['year'].max()
    df_latest = df_db[df_db['year'] == latest_year]
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric("전국 친환경차 등록 대수", f"{df_latest['count_ev'].sum():,.0f} 대")
    with kpi_col2:
        st.metric("전국 충전기 인프라 합계", f"{df_latest['count_charger'].sum():,.0f} 기")
    with kpi_col3:
        st.metric("기준 연도", f"{latest_year}년")

    st.markdown("---")
    st.info("왼쪽 사이드바의 메뉴를 통해 FAQ 및 유지비 비교 페이지로 이동할 수 있습니다.")

# --- 네비게이션 설정 ---
pg = st.navigation([
    st.Page(dashboard_page, title="전국 보급 현황", icon="🌱"),
    st.Page("pages/compare.py", title="차량 유지비 비교", icon="🔍"),
    st.Page("pages/faq.py", title="친환경차 통합 FAQ", icon="📝"),
])
pg.run()
