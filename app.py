import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. 페이지 설정
st.set_page_config(page_title="🌱 전국 친환경차 현황 대시보드", layout="wide")

@st.cache_data
def load_data():
    """통합된 데이터 로드 및 전처리"""
    # GeoJSON 로드 (지역명 매핑용)
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    geojson = requests.get(geojson_url).json()

    # CSV 로드
    df_integrated = pd.read_csv("전기차_일반차_통합.csv", encoding="utf-8-sig")
    df_fuel = pd.read_csv("지역별_연료별_등록대수_최종.csv", encoding="utf-8-sig")

    # [중요] 이름 매핑: '서울' -> '서울특별시' (지도 연동 필수)
    name_map = {
        '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
        '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
        '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
        '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
        '전북': '전라북도', '전남': '전라남도', '경북': '경상북도',
        '경남': '경상남도', '제주': '제주특별자치도'
    }
    
    # 두 데이터셋 모두 지역명 변환
    df_integrated['region'] = df_integrated['region'].replace(name_map)
    df_fuel['지역'] = df_fuel['지역'].replace(name_map)

    # 데이터 타입 통일
    df_integrated['year'] = df_integrated['year'].astype(int)
    df_fuel['연도'] = df_fuel['연도'].astype(float).astype(int)

    # 보급률 계산 (통합 파일 기준)
    # 전체 자동차 = 전기차(count_ev) + 일반차
    df_integrated['총자동차'] = df_integrated['count_ev'] + df_integrated['일반차']
    df_integrated['보급률'] = (df_integrated['count_ev'] / df_integrated['총자동차']) * 100
    
    # 2026 vs 2025 증감율 계산
    df_2026 = df_integrated[df_integrated['year'] == 2026].set_index('region')['count_ev']
    df_2025 = df_integrated[df_integrated['year'] == 2025].set_index('region')['count_ev']
    growth_rate = ((df_2026 - df_2025) / df_2025) * 100
    
    return geojson, df_integrated, df_fuel, growth_rate

# 데이터 로딩
try:
    geojson, df_main, df_fuel, growth_rate = load_data()
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

# --- 상태 관리 ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "서울특별시"

# --- UI 레이아웃 ---
st.title("🌱 전국 친환경차 현황 대시보드 (2026)")
st.markdown("---")

# 1단: KPI 메트릭 (2026년 기준)
latest_df = df_main[df_main['year'] == 2026]
total_ev = latest_df['count_ev'].sum()
avg_ratio = (total_ev / latest_df['총자동차'].sum()) * 100
avg_growth = growth_rate.mean()

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("전국 전기차 누적 등록", f"{total_ev:,.0f} 대")
with k2:
    st.metric("평균 증감율 (25년 대비)", f"{avg_growth:.1f}%")
with k3:
    st.metric("전체 대비 전기차 비중", f"{avg_ratio:.2f}%")

st.markdown("---")

# 2단: 지도 및 추이 차트
map_col, trend_col = st.columns([6, 4])

with map_col:
    st.markdown("### 🗺️ 지역별 보급률 지도 (%)")
    fig_map = px.choropleth_mapbox(
        latest_df, geojson=geojson, locations='region', featureidkey="properties.name",
        color='보급률', color_continuous_scale="YlGn", mapbox_style="carto-positron",
        zoom=5.5, center={"lat": 35.9, "lon": 127.7}, opacity=0.7,
        hover_data={'region': True, '보급률': ':.2f', 'count_ev': ':,.0f'}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
    
    if map_event and "selection" in map_event:
        points = map_event["selection"].get("points", [])
        if points:
            clicked_region = points[0].get("location")
            if clicked_region in df_main['region'].values:
                st.session_state.selected_region = clicked_region
                st.rerun()

with trend_col:
    # 💡 통합 데이터를 활용한 전기차 vs 일반차 추이
    st.markdown(f"### 📈 {st.session_state.selected_region} 등록 추이")
    reg_trend = df_main[df_main['region'] == st.session_state.selected_region].sort_values('year')
    
    if not reg_trend.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=reg_trend['year'], y=reg_trend['일반차'], name="일반차", line=dict(color='#3498DB', width=3)))
        fig_trend.add_trace(go.Scatter(x=reg_trend['year'], y=reg_trend['count_ev'], name="전기차", line=dict(color='#E74C3C', width=4)))
        
        fig_trend.update_layout(
            xaxis=dict(type='category'),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=0, r=0, t=30, b=0), height=400
        )
        st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# 3단: 연료별 상세 분석 (도넛 차트)
st.markdown(f"### 🔍 {st.session_state.selected_region} 세부 연료별 비중 (2026)")
region_fuel = df_fuel[(df_fuel['지역'] == st.session_state.selected_region) & (df_fuel['연도'] == 2026)]

if not region_fuel.empty:
    fig_donut = px.pie(region_fuel, values='대수', names='연료', hole=.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20}, height=400)
    st.plotly_chart(fig_donut, use_container_width=True)
else:
    st.warning("해당 지역의 상세 연료 데이터가 없습니다.")