import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from utils.db_manager import db_manager


# 1. 페이지 설정
st.set_page_config(page_title="전국 친환경차 현황 대시보드", layout="wide")

# --- 공통 데이터 로드 함수 ---
@st.cache_data
def load_data():
    # 데이터 로드
    try:
        # 1. 전기차/일반차 통합 데이터 (regional_ev_status)
        df_main = db_manager.fetch_query("SELECT region, year, count_ev, count_ice as 일반차 FROM regional_ev_status")
        # 2. 보조금 데이터 (ev_subsidy_status)
        df_subsidy = db_manager.fetch_query("SELECT region as 지역, category as 보조금항목, amount as 금액 FROM ev_subsidy_status")
    
    except Exception as e:
        st.error(f"DB 데이터 로드 중 오류 발생: {e}")
        st.stop()

    # GeoJSON
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
    df_subsidy['region_full'] = df_subsidy['지역'].replace(name_map)

    # 데이터 타입 정제
    df_main['year'] = df_main['year'].astype(int)

    #지역별 총자동차 대수 컬럼 생성
    df_main['총자동차'] = df_main['count_ev'] + df_main['일반차']
    #지역별 보급률 컬럼 생성
    df_main['보급률'] = (df_main['count_ev'] / df_main['총자동차']).fillna(0) * 100

    return geojson, df_main, df_subsidy

# --- 메인 대시보드 페이지 함수 정의 ---================================================================
def dashboard_page():
    # 데이터 가져오기
    geojson, df_main, df_subsidy = load_data()

    # --- 2. 지표계산 ---
    #각 연도별로 데이터 슬라이싱 
    df_2026 = df_main[df_main['year'] == 2026].drop_duplicates(['region'])
    df_2025 = df_main[df_main['year'] == 2025].drop_duplicates(['region'])
    df_2024 = df_main[df_main['year'] == 2024].drop_duplicates(['region'])

    #전국 합계/ 각 연도별 전기차 총 등록 대수
    total_ev_2026 = df_2026['count_ev'].sum()
    total_ev_2025 = df_2025['count_ev'].sum()
    total_ev_2024 = df_2024['count_ev'].sum()

    #단순 증감/ 전년대비 전기차 등록 대수 차이
    ev_delta_count = total_ev_2026 - total_ev_2025
    
    #해당연도 등록 차량 중 전기차가 차지했던 비율 (전국 보급율)
    avg_ratio_2026 = (total_ev_2026 / df_2026['총자동차'].sum() * 100) if df_2026['총자동차'].sum() != 0 else 0
    avg_ratio_2025 = (total_ev_2025 / df_2025['총자동차'].sum() * 100) if df_2025['총자동차'].sum() != 0 else 0
    
    #전년 대비 전기차 등록 대수의 증가 (성장율)
    growth_2026 = ((total_ev_2026 - total_ev_2025) / total_ev_2025) * 100 if total_ev_2025 != 0 else 0
    growth_2025 = ((total_ev_2025 - total_ev_2024) / total_ev_2024) * 100 if total_ev_2024 != 0 else 0
    
    #보급 확대 폭/ 전년 대비 보급률 자체가 얼마나 상승했는가
    ratio_delta_points = avg_ratio_2026 - avg_ratio_2025
    

# --- 3. UI 레이아웃 ---===============================================================================
    st.title("전국 친환경차 현황 대시보드")
    st.divider()

    # 중앙 좌측-----------------------------------------------------------------------
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "서울특별시"

    trend_col, map_col = st.columns([4, 6])

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

    #중앙 오른쪽-----------------------------------------------------------------------------------
    with trend_col:
        st.metric(
                label="전국 전기차 누적 등록", 
                value=f"{total_ev_2026:,.0f} 대", 
                delta=f"{ev_delta_count:,.0f} 대"
            )
        st.divider()

        st.metric(
            label="전국 통합 성장률", 
            value=f"{growth_2026:.1f}%",
            delta=f"{growth_2026 - growth_2025:.1f}%" if 'growth_2026' in locals() else "상승세" 
        )
        st.divider()

        st.metric(
            label="전체 차량 중 전기차 비중", 
            value=f"{avg_ratio_2026:.2f}%", 
            delta=f"{ratio_delta_points:.2f}%p"
        )
    # 하단
    st.divider()
    #보조금현황
    mmchart,dframe = st.columns(2)
    with dframe:
        st.markdown(f"### {st.session_state.selected_region} 보조금 현황")
        
        sub = df_subsidy[df_subsidy['region_full'] == st.session_state.selected_region].copy()
        
        if not sub.empty:
            # 차종/항목 분리
            sub[['차종', '항목']] = sub['보조금항목'].str.extract(r'(승용|초소형|화물)(.*)')

            res = (sub.pivot(index='차종', columns='항목', values='금액')
                .reindex(index=['승용', '초소형', '화물'], 
                            columns=['최대보조금', '최소보조금', '보조금평균값'])
                .fillna(0)
                .astype(int))

            st.table(res)
            
            st.markdown('''
            1. 법적 근거
                
            「환경친화적 자동차의 개발 및 보급 촉진에 관한 법률」 제10조 및 「대기환경보전법」 제58조에 기반하여 구매 보조금 지원.
            
            2 .보조금 구조
                
            국비 보조금(환경부)과 지방비 보조금(지자체)을 합산하여 지급.
            
            3 .지급 대상
                
            전기승용차, 전기화물차, 전기승합차 등 보급평가 기준을 충족한 차량.
        

            ''')
        else:
            st.warning("해당 지역의 보조금 데이터가 없습니다.")

    with mmchart:
        # 해당지역 전기차, 비전기차 등록 추이 비교 차트
        # min-max scaling
        st.markdown(f"### {st.session_state.selected_region} 등록 추이 (Scaled)")
        reg_trend = df_main[df_main['region_full'] == st.session_state.selected_region].sort_values('year')
        
        if not reg_trend.empty:
            scale_fn = lambda x: (x - x.min()) / (x.max() - x.min()) if (x.max() - x.min()) != 0 else x * 0
            
            fig_trend = go.Figure()

            fig_trend.add_trace(go.Scatter(
                x=reg_trend['year'], 
                y=scale_fn(reg_trend['일반차']), 
                name="비전기차", line=dict(color='#3498DB', width=3)
            ))
            
            fig_trend.add_trace(go.Scatter(
                x=reg_trend['year'], 
                y=scale_fn(reg_trend['count_ev']), 
                name="전기차", line=dict(color='#E74C3C', width=4)
            ))
            
            fig_trend.update_layout(
                xaxis=dict(type='category'),
                yaxis=dict(showticklabels=False),
                hovermode="x unified",
                height=400, margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

# --- 네비게이션 설정 ---
from components.sidebar_widget import render_sidebar_widget

with st.sidebar:
    render_sidebar_widget()

pg = st.navigation([
    st.Page(dashboard_page, title="전국 보급 현황", icon="🌱"),
    st.Page("pages/compare.py", title="차량 유지비 비교", icon="🔍"),
    st.Page("pages/faq.py", title="친환경차 통합 FAQ", icon="📝"),
    st.Page("pages/infrastructure.py", title="충전소 인프라 현황", icon="⚡"),
])
pg.run()