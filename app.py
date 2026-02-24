import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
<<<<<<< HEAD

# 1. 페이지 설정
st.set_page_config(page_title="🌱 전국 친환경차 현황 대시보드", layout="wide")

@st.cache_data
def load_data():
    """데이터 로드 및 전처리 함수"""
    # GeoJSON 로드 (대한민국 시/도 경계 단순화 버전) [1, 2]
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    geojson = requests.get(geojson_url).json()

    # csv 로드
    df_master = pd.read_csv("master_2026.csv", encoding="utf-8-sig")
    df_trend = pd.read_csv("eco_trend.csv", encoding="utf-8-sig")

    #친환경차 합계
    df_master['친환경차_합계'] = df_master['하이브리드'] + df_master['전기'] + df_master['수소']
    

    #전국 누적등록 행 생성
    numeric_cols = df_master.select_dtypes(include=['number']).columns
    total_row = df_master[numeric_cols].sum().to_frame().T
    total_row['지역'] = '전국'

    # 친환경차 데이터만 추출
    eco_only = df_trend[df_trend['차종'] == '친환경차'].groupby('연도')['대수'].sum()
    current_eco = eco_only.get(2026, 0)
    prev_eco = eco_only.get(2025, 1) # 분모 0 방지
    calc_growth_rate = ((current_eco - prev_eco) / prev_eco) * 100

    # 💡 강원도 명칭 불일치 해결 (데이터: 강원특별자치도 -> GeoJSON: 강원도) [2]
    name_map = {
        '강원특별자치도': '강원도',
        '제주특별자치도': '제주도',
        '전라북도': '전라북도', 
        '경상북도': '경상북도',
        '경상남도': '경상남도'
    }
    df_master['지역'] = df_master['지역'].replace(name_map)
    df_trend['지역'] = df_trend['지역'].replace(name_map)

    # 지표 계산: 친환경차 합계 및 보급률 [4, 6]
    df_master['친환경차_합계'] = df_master['전기'] + df_master['수소']
    df_master['보급률'] = (df_master['친환경차_합계'] / df_master['전체합계']) * 100
    
    return geojson, df_master, df_trend, calc_growth_rate

# 데이터 실행
try:
    geojson, df_master, df_trend, calc_growth_rate = load_data()
except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 2. 상태 관리 (Session State) [2, 5, 7] ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "서울특별시"

def sync_region():
    if "region_selectbox" in st.session_state:
        st.session_state.selected_region = st.session_state.region_selectbox

# --- 3. UI 레이아웃 ---
st.title("🌱 전국 친환경차 현황 대시보드")
st.markdown("---")

# 1단
k1, k2, k3 = st.columns(3)
total_eco = df_master['친환경차_합계'].sum()
avg_ratio = (total_eco / df_master['전체합계'].sum()) * 100

target_year = 2026
all_regions = ['전국'] + df_master['지역'].unique().tolist()\


with k1:
    st.metric("전국 친환경차 누적 등록", f"{total_eco:,.0f} 대", delta="2026년 기준")
with k2:
    st.metric("전년 대비 증감율", f"{calc_growth_rate:.1f}%", delta="수정해야함")
with k3:
    st.metric("전체 차량 중 친환경차 비율", f"{avg_ratio:.2f}%", delta="수정해야함")

st.markdown("---", unsafe_allow_html=True)

#2단
map_col, trend_col = st.columns([6, 4]) # 6:4 비율

with map_col:
    # 지도 우측 상단 지역 선택 박스
    m_head_l, m_head_r = st.columns([0.6, 0.4])
    m_head_l.markdown("### 🗺️ 지역별 보급률 지도")
    all_regions = df_master['지역'].unique().tolist()
    st.selectbox("지역 선택", options=all_regions, 
                index=all_regions.index(st.session_state.selected_region),
                key="region_selectbox", on_change=sync_region, label_visibility="collapsed")

    fig_map = px.choropleth_mapbox(
        df_master, geojson=geojson, locations='지역', featureidkey="properties.name",
        color='보급률', color_continuous_scale="Greens", mapbox_style="carto-positron",
        zoom=5.5, center={"lat": 36.3, "lon": 127.7}, opacity=0.8,
        hover_data={'보급률': ':.2f', '친환경차_합계': ':,.0f'}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    #지도 클릭시
    map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
    
    if map_event and isinstance(map_event, dict) and "selection" in map_event:
        points = map_event["selection"].get("points", [])
        if points:
            clicked_region = points.get("location")
            if clicked_region and clicked_region != st.session_state.selected_region:
                st.session_state.selected_region = clicked_region
                st.rerun()

with trend_col:
    st.markdown(f"### 📈 {st.session_state.selected_region} 성장 추이")
    regional_trend = df_trend[df_trend['지역'] == st.session_state.selected_region]
    
    if not regional_trend.empty:
        fig_trend = px.line(regional_trend, x='연도', y='대수', color='차종', markers=True,
                            color_discrete_map={'친환경차': '#2ca02c', '내연기관차': '#7f7f7f'})
        fig_trend.update_layout(xaxis_type='category', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

#3단
st.markdown(f"### 🔍 {st.session_state.selected_region} 상세 분석")

detail_row = df_master[df_master['지역'] == st.session_state.selected_region]

if not detail_row.empty:
    res = detail_row.iloc[0] # TypeError 방지를 위한 명확한 인덱싱 [17]
    
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**연료별 등록 비중**")
        labels = ['휘발유', '경유', '엘피지', '하이브리드', '전기', '수소']
        values = [res['휘발유'], res['경유'], res['엘피지'], res['하이브리드'], res['전기'], res['수소']]
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
        fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20}, height=300)
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with d2:
        st.markdown("**차종별 평균 보조금 (만원)**")
        subsidy_df = pd.DataFrame({
            "차종 구분": ["승용차", "초소형차", "화물차"],
            "평균 지원금": [f"{res['보조금_승용']:,}", f"{res['보조금_초소형']:,}", f"{res['보조금_화물']:,}"]
        })
        st.table(subsidy_df)
=======
import json
from utils.db_manager import db_manager

# 페이지 기본 설정
st.set_page_config(page_title="친환경차 대시보드", page_icon="🌱", layout="wide")

# 지역명 매핑 (DB -> GeoJSON)
REGION_MAP = {
    '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', '인천': '인천광역시',
    '광주': '광주광역시', '대전': '대전광역시', '울산': '울산광역시', '세종': '세종특별자치시',
    '경기': '경기도', '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
    '전북': '전라북도', '전남': '전라남도', '경북': '경상북도', '경남': '경상남도', '제주': '제주특별자치도'
}
REV_REGION_MAP = {v: k for k, v in REGION_MAP.items()}

@st.cache_data
def load_all_data():
    """DB 데이터 및 GeoJSON 로드"""
    # 1. GeoJSON 로드 (인터넷 에러 대비 fallback 준비)
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    try:
        response = requests.get(geojson_url, timeout=5)
        geojson = response.json()
    except Exception as e:
        st.warning(f"지도 데이터를 불러오는 데 실패했습니다 (기본 지도 사용): {e}")
        geojson = None # 지도가 안 보일 수 있으니 None 처리

    # 2. DB 데이터 로드
    try:
        query = "SELECT region, year, count_ev, count_charger FROM regional_ev_status"
        df_db = db_manager.fetch_query(query)
        if not df_db.empty:
            df_db['region_full'] = df_db['region'].map(REGION_MAP)
    except Exception as e:
        st.error(f"데이터베이스 쿼리 중 오류 발생: {e}")
        df_db = pd.DataFrame()
    
    return geojson, df_db

# --- 사이드바 / 시스템 상태 ---
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    with st.expander("🛠️ DB 연결 상태 확인"):
        try:
            conn = db_manager.get_connection()
            if conn.is_connected():
                st.success("데이터베이스 연결 성공!")
                conn.close()
            else:
                st.error("데이터베이스 연결 실패")
        except Exception as e:
            st.error(f"오류: {e}")

# 데이터 로드
geojson, df_db = load_all_data()

if df_db.empty:
    st.title("🌱 전국 친환경차 현황 대시보드")
    st.warning("데이터베이스에 표시할 데이터가 없습니다.")
    st.info("DBeaver에서 [DB_SETUP_GUIDE.md]에 있는 SQL 스크립트를 실행해 주세요.")
    st.stop()

# --- 상태 관리 (세션 스테이트) ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "서울특별시"

def update_region_from_selectbox():
    st.session_state.selected_region = st.session_state.region_selectbox

# ==========================================
# 🌟 1단: KPI Metrics
# ==========================================
st.title("🌱 전국 친환경차 현황 대시보드")
st.markdown("---")

# 최근 연도 데이터 기준 KPI
try:
    latest_year = df_db['year'].max()
    prev_year = latest_year - 1
    df_latest = df_db[df_db['year'] == latest_year]
    df_prev = df_db[df_db['year'] == prev_year]

    total_ev_latest = df_latest['count_ev'].sum()
    total_ev_prev = df_prev['count_ev'].sum()
    diff_ev = total_ev_latest - total_ev_prev
    growth_rate = (diff_ev / total_ev_prev * 100) if total_ev_prev > 0 else 0

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    with kpi_col1:
        st.metric(label=f"{latest_year}년 전국 친환경차 누적 등록 대수", value=f"{total_ev_latest:,.0f} 대", delta=f"+{diff_ev:,.0f} 대")
    with kpi_col2:
        st.metric(label="전년 대비 증가율", value=f"{growth_rate:.1f}%")
    with kpi_col3:
        total_chargers = df_latest['count_charger'].sum()
        st.metric(label="전국 충전기 인프라 합계", value=f"{total_chargers:,.0f} 기")
except Exception as e:
    st.error(f"KPI 계산 중 오류 발생: {e}")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 🗺️ 2단: Map & Trend
# ==========================================
map_col, trend_col = st.columns([6, 4])

with map_col:
    st.markdown("### 🗺️ 지역별 보급 현황 지도")
    
    years = sorted(df_db['year'].unique())
    map_year = st.select_slider("📅 지도 표시 연도 선택", options=years, value=latest_year)
    df_map = df_db[df_db['year'] == map_year]

    if geojson:
        fig_map = px.choropleth_mapbox(
            df_map, 
            geojson=geojson, 
            locations='region_full', 
            featureidkey="properties.name",
            color='count_ev',
            color_continuous_scale="Greens",
            mapbox_style="carto-positron",
            zoom=5.5, 
            center={"lat": 36.3, "lon": 127.7},
            opacity=0.8,
            labels={'count_ev': '친환경차(대)', 'region_full': '지역'}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
        
        if map_event and map_event.get("selection", {}).get("points"):
            clicked_region = map_event["selection"]["points"][0].get("location")
            if clicked_region and clicked_region in REV_REGION_MAP:
                st.session_state.selected_region = clicked_region
                st.session_state.region_selectbox = clicked_region
                st.rerun()
    else:
        st.info("지도를 불러올 수 없어 차트로 대체합니다.")
        st.bar_chart(df_map.set_index('region_full')['count_ev'])

with trend_col:
    st.markdown("### 📈 전국 연도별 성장 추이")
    national_trend = df_db.groupby('year')[['count_ev', 'count_charger']].sum().reset_index()
    fig_trend = px.line(national_trend, x='year', y=['count_ev', 'count_charger'], markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

# ==========================================
# 🔍 3단: 지역별 딥다이브
# ==========================================
st.markdown(f"### 🔍 {st.session_state.selected_region} 상세 데이터")

all_region_fulls = sorted(list(REGION_MAP.values()))
if st.session_state.selected_region not in all_region_fulls:
    st.session_state.selected_region = all_region_fulls[0]

selected_index = all_region_fulls.index(st.session_state.selected_region)

col_select, _ = st.columns([1, 2])
with col_select:
    st.selectbox(
        "분석 지역 선택:", 
        options=all_region_fulls, 
        index=selected_index,
        key="region_selectbox",
        on_change=update_region_from_selectbox
    )

region_short = REV_REGION_MAP[st.session_state.selected_region]
df_target = df_db[(df_db['region'] == region_short) & (df_db['year'] == latest_year)]

if not df_target.empty:
    df_reg_latest = df_target.iloc[0]
    detail_col1, detail_col2 = st.columns([1, 1])

    with detail_col1:
        st.markdown(f"**[{st.session_state.selected_region}] 인프라 구성**")
        fig_donut = go.Figure(data=[go.Pie(labels=['친환경차', '충전기'], values=[df_reg_latest['count_ev'], df_reg_latest['count_charger']], hole=.5)])
        st.plotly_chart(fig_donut, use_container_width=True)

    with detail_col2:
        st.markdown(f"**[{st.session_state.selected_region}] 연도별 데이터**")
        reg_trend = df_db[df_db['region'] == region_short].sort_values('year')
        st.dataframe(reg_trend[['year', 'count_ev', 'count_charger']].set_index('year'), use_container_width=True)
else:
    st.warning(f"{st.session_state.selected_region} 지역의 {latest_year}년 데이터가 없습니다.")
>>>>>>> origin/dev
