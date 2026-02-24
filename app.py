import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. 페이지 설정
st.set_page_config(page_title="🌱 전국 친환경차 현황 대시보드", layout="wide")

@st.cache_data
def load_data():
    """파일 데이터 로드 및 전처리"""
    # GeoJSON (지도용)
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    geojson = requests.get(geojson_url).json()

    # CSV 로드
    df_master = pd.read_csv("master.csv", encoding="utf-8-sig")
    df_trend = pd.read_csv("지역별_연료별_등록대수_최종.csv", encoding="utf-8-sig")

    # 데이터 타입 정제
    df_master['연도'] = df_master['연도'].astype(int)
    df_trend['연도'] = df_trend['연도'].astype(float).astype(int)

    # 이름 매핑 (데이터셋 '서울' -> 지도 '서울특별시')
    name_map = {
        '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
        '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
        '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
        '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
        '전북': '전라북도', '전남': '전라남도', '경북': '경상북도',
        '경남': '경상남도', '제주': '제주특별자치도'
    }
    df_master['지역'] = df_master['지역'].replace(name_map)
    df_trend['지역'] = df_trend['지역'].replace(name_map)

    # 💡 [핵심 수정] 전기차 vs 비전기차 계산
    # master.csv의 컬럼명을 기준으로 계산합니다.
    df_master['비전기차 등록수'] = df_master['총 자동차 등록수'] - df_master['전기차 등록수']
    df_master['보급률'] = (df_master['전기차 등록수'] / df_master['총 자동차 등록수']) * 100
    
    # 증감율 계산 (2026 vs 2025)
    df_2026 = df_master[df_master['연도'] == 2026].set_index('지역')['전기차 등록수']
    df_2025 = df_master[df_master['연도'] == 2025].set_index('지역')['전기차 등록수']
    calc_growth_rate = ((df_2026 - df_2025) / df_2025) * 100
    
    return geojson, df_master, df_trend, calc_growth_rate

# 데이터 로딩
try:
    geojson, df_master, df_trend, calc_growth_rate = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 2. 상태 관리 ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "서울특별시"

# --- 3. UI 레이아웃 ---
st.title("🌱 전국 친환경차 현황 대시보드 (2026)")
st.markdown("---")

# 1단: KPI 메트릭
k1, k2, k3 = st.columns(3)
latest_df = df_master[df_master['연도'] == 2026]
total_ev = latest_df['전기차 등록수'].sum()
avg_ratio = (total_ev / latest_df['총 자동차 등록수'].sum()) * 100
avg_growth = calc_growth_rate.mean()

with k1:
    st.metric("전국 전기차 누적 등록 (2026)", f"{total_ev:,.0f} 대")
with k2:
    st.metric("전국 평균 증감율 (25년 대비)", f"{avg_growth:.1f}%")
with k3:
    st.metric("전체 차량 중 전기차 비율", f"{avg_ratio:.2f}%")

st.markdown("---")

# 2단: 지도 및 연도별 추이 (전기 vs 비전기)
map_col, trend_col = st.columns([6, 4])

with map_col:
    st.markdown("### 🗺️ 지역별 보급률 지도 (%)")
    fig_map = px.choropleth_mapbox(
        latest_df, geojson=geojson, locations='지역', featureidkey="properties.name",
        color='보급률', color_continuous_scale="YlGn", mapbox_style="carto-positron",
        zoom=5.5, center={"lat": 35.9, "lon": 127.7}, opacity=0.7,
        hover_data={'보급률': ':.2f', '전기차 등록수': ':,.0f'}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
    
    if map_event and "selection" in map_event:
        points = map_event["selection"].get("points", [])
        if points:
            clicked_region = points[0].get("location")
            if clicked_region in df_master['지역'].values:
                st.session_state.selected_region = clicked_region
                st.rerun()

with trend_col:
    # 💡 [핵심 수정] 꺾은선 그래프: 전기차 vs 비전기차
    st.markdown(f"### 📈 {st.session_state.selected_region} 연도별 등록 추이")
    reg_master_trend = df_master[df_master['지역'] == st.session_state.selected_region].sort_values('연도')
    
    if not reg_master_trend.empty:
        fig_trend = go.Figure()
        
        # 비전기차 라인 (파란색 계열)
        fig_trend.add_trace(go.Scatter(
            x=reg_master_trend['연도'], y=reg_master_trend['비전기차 등록수'],
            name="비전기차", line=dict(color='#3498DB', width=3), mode='lines+markers'
        ))
        
        # 전기차 라인 (핑크색 계열)
        fig_trend.add_trace(go.Scatter(
            x=reg_master_trend['연도'], y=reg_master_trend['전기차 등록수'],
            name="전기차", line=dict(color='#E74C3C', width=4), mode='lines+markers'
        ))
        
        fig_trend.update_layout(
            xaxis=dict(type='category'),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
            height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# 3단: 상세 분석 (도넛 차트는 연료별 유지)
st.markdown(f"### 🔍 {st.session_state.selected_region} 상세 분석")

col_left, col_right = st.columns(2)

# 해당 지역의 2026년 상세 데이터
region_master_2026 = latest_df[latest_df['지역'] == st.session_state.selected_region].iloc[0]
region_trend_2026 = df_trend[(df_trend['지역'] == st.session_state.selected_region) & (df_trend['연도'] == 2026)]

with col_left:
    # 💡 도넛 차트는 기존처럼 연료별(휘발유, 경유, 수소 등)로 표시
    st.markdown("**연료별 등록 비중 (2026)**")
    if not region_trend_2026.empty:
        fig_donut = px.pie(region_trend_2026, values='대수', names='연료', hole=.4,
                        color_discrete_sequence=px.colors.qualitative.Safe)
        fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20}, height=350)
        st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.markdown("**차종별 최대 보조금 (2026)**")
    subsidy_df = pd.DataFrame({
        "차종 구분": ["승용차", "화물차"],
        "지원금 (만원)": [
            f"{region_master_2026['최대 보조금(승용/만원)']:,.0f}", 
            f"{region_master_2026['최대 보조금(화물/만원)']:,.0f}"
        ]
    })
    st.table(subsidy_df)
    
    # 충전기 수 정보 (master.csv에 N/A가 있을 수 있으므로 처리)
    charger_val = region_master_2026['충전기 수']
    charger_text = f"{charger_val:,.0f}대" if pd.notnull(charger_val) and charger_val != "N/A" else "정보 없음"
    st.info(f"💡 {st.session_state.selected_region}의 2026년 충전기 수는 {charger_text} 입니다.")