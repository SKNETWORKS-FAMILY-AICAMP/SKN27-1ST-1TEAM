import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from utils.db_manager import db_manager


# 1. 페이지 설정 (가장 상단에 위치)
st.set_page_config(page_title="전국 친환경차 현황 대시보드", layout="wide")

# --- 공통 데이터 로드 함수 ---
@st.cache_data
def load_data():
    # 데이터 로드
    df_main = pd.read_csv("전기차_일반차_통합.csv", encoding="utf-8-sig")
    df_fuel = pd.read_csv("지역별_연료별_등록대수_최종.csv", encoding="utf-8-sig")
    
    # [수정] 보조금 tidy 데이터 로드 (인코딩 에러 방지 위해 utf-8-sig 권장)
    try:
        df_subsidy = pd.read_csv("전기차보조금_tidy.csv", encoding="utf-8-sig")
    except:
        df_subsidy = pd.read_csv("전기차보조금_tidy.csv", encoding="cp949")
    
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    geojson = requests.get(geojson_url).json()

    # 명칭 매핑 (지도 연동용)
    name_map = {
        '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
        '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
        '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
        '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
        '전북': '전라북도', '전남': '전라남도', '경북': '경상북도',
        '경남': '경상남도', '제주': '제주특별자치도'
    }
    df_main['region_full'] = df_main['region'].replace(name_map)
    df_fuel['지역_full'] = df_fuel['지역'].replace(name_map)
    # 보조금 데이터에도 지역 풀네임 적용 (필요 시)
    df_subsidy['지역_full'] = df_subsidy['지역'].replace(name_map)

    # 데이터 타입 정제
    df_main['year'] = df_main['year'].astype(int)
    df_fuel['연도'] = pd.to_numeric(df_fuel['연도'], errors='coerce').fillna(0).astype(int)

    # 보급률 계산 로직
    df_main['총자동차'] = df_main['count_ev'] + df_main['일반차']
    df_main['보급률'] = (df_main['count_ev'] / df_main['총자동차']) * 100

    # [중요] 4개의 값을 정확히 반환
    return geojson, df_main, df_fuel, df_subsidy

# --- 메인 대시보드 페이지 함수 정의 ---
def dashboard_page():
    # 데이터 가져오기
    geojson, df_main, df_fuel, df_subsidy = load_data()

    # --- 2. KPI 계산 ---
    target_year = 2026
    df_2026 = df_main[df_main['year'] == target_year].drop_duplicates(['region'])
    df_2025 = df_main[df_main['year'] == 2025].drop_duplicates(['region'])

    total_ev_2026 = df_2026['count_ev'].sum()
    total_cars_2026 = df_2026['총자동차'].sum()
    total_ev_2025 = df_2025['count_ev'].sum()

    avg_ratio = (total_ev_2026 / total_cars_2026) * 100
    total_growth = ((total_ev_2026 - total_ev_2025) / total_ev_2025) * 100

# --- 3. UI 레이아웃 ---
    st.title(f"전국 친환경차 현황 대시보드")
    st.markdown("---")

    # KPI 표시
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("전국 전기차 누적 등록", f"{total_ev_2026:,.0f} 대")
    with k2:
        st.metric("전국 통합 증감율 (25년 대비)", f"{total_growth:.1f}%")
    with k3:
        st.metric("전체 차량 중 전기차 비중", f"{avg_ratio:.2f}%")

    st.markdown("---")

    # --- 4. 지도 및 추이 섹션 ---
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "서울특별시"

    map_col, trend_col = st.columns([6, 4])

    with map_col:
        st.markdown("### 지역별 보급률 지도 (%)")
        fig_map = px.choropleth_mapbox(
            df_2026, geojson=geojson, locations='region_full', featureidkey="properties.name",
            color='보급률', color_continuous_scale="YlGn", mapbox_style="carto-positron",
            zoom=5.5, center={"lat": 35.9, "lon": 127.7}, opacity=0.7,
            hover_name='region_full',
            hover_data={
                'region_full': False, 
                '총자동차': ':,.0f',
                '일반차': ':,.0f',
                'count_ev': ':,.0f',
                '보급률': ':.2f'
            },
            labels={
                "총자동차": "전체 차량 대수",
                "일반차": "일반 차량 대수",
                "count_ev": "전기차 등록 대수",
                "보급률": "친환경차 보급률(%)"
            }
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
        
        if map_event and "selection" in map_event:
            points = map_event["selection"].get("points", [])
            if points:
                clicked_region = points[0].get("location")
                if clicked_region in df_main['region_full'].values:
                    # 선택된 값이 기존과 다를 때만 갱신 (무의미한 재실행 방지)
                    if st.session_state.selected_region != clicked_region:
                        st.session_state.selected_region = clicked_region
                        st.rerun()

    with trend_col:
        st.markdown(f"### {st.session_state.selected_region} 등록 추이")
        reg_trend = df_main[df_main['region_full'] == st.session_state.selected_region].sort_values('year')
        
        if not reg_trend.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=reg_trend['year'], y=reg_trend['일반차'], name="비전기차(일반)", line=dict(color='#3498DB', width=3)))
            fig_trend.add_trace(go.Scatter(x=reg_trend['year'], y=reg_trend['count_ev'], name="전기차", line=dict(color='#E74C3C', width=4)))
            
            fig_trend.update_layout(
                xaxis=dict(type='category'),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0), height=400
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # --- 5. 연료별 비중 및 보조금 현황 ---
    donut, dframe = st.columns(2)
    with donut:
        st.markdown(f"### {st.session_state.selected_region} 연료별 비중")
        region_fuel = df_fuel[(df_fuel['지역_full'] == st.session_state.selected_region) & (df_fuel['연도'] == 2026)]

        if not region_fuel.empty:
            fig_donut = px.pie(region_fuel, values='대수', names='연료', hole=.4,
                                color_discrete_sequence=px.colors.qualitative.Safe)
            fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20}, height=400)
            st.plotly_chart(fig_donut, use_container_width=True)

    with dframe:
        st.markdown(f"### {st.session_state.selected_region} 보조금 현황")
        
        # 1. 정확한 지역 풀네임으로 필터링
        sub = df_subsidy[df_subsidy['지역_full'] == st.session_state.selected_region].copy()
        
        if not sub.empty:
            # 2. 차종/항목 분리
            sub[['차종', '항목']] = sub['보조금항목'].str.extract(r'(승용|초소형|화물)(.*)')

            # 3. 피벗 및 구조 고정
            res = sub.pivot(index='차종', columns='항목', values='금액')
            res = res.reindex(index=['승용', '초소형', '화물'], 
                            columns=['최대보조금', '최소보조금', '보조금평균값']).fillna(0).astype(int)

            st.table(res)
        else:
            st.warning("해당 지역의 보조금 데이터가 없습니다.")
# --- 네비게이션 설정 ---

pg = st.navigation([
    st.Page(dashboard_page, title="전국 보급 현황", icon="🌱"),
    st.Page("pages/compare.py", title="차량 유지비 비교", icon="🔍"),
    st.Page("pages/faq.py", title="친환경차 통합 FAQ", icon="📝"),
])
pg.run()
