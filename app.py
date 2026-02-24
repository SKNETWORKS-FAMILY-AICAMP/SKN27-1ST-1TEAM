import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

<<<<<<< HEAD
# --- 페이지 공통 설정 ---
st.set_page_config(page_title="친환경차 대시보드", page_icon="🌱", layout="wide")

# 지역명 매핑 (DB -> GeoJSON)
REGION_MAP = {
    '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시', '인천': '인천광역시',
    '광주': '광주광역시', '대전': '대전광역시', '울산': '울산광역시', '세종': '세종특별자치시',
    '경기': '경기도', '강원': '강원도', '충북': '충청북도', '충남': '충청남도',
    '전북': '전라북도', '전남': '전라남도', '경북': '경상북도', '경남': '경상남도', '제주': '제주특별자치도'
}
REV_REGION_MAP = {v: k for k, v in REGION_MAP.items()}

# --- 메인 대시보드 페이지 함수 ---
def dashboard_page():
    @st.cache_data
    def load_all_data():
        """DB 데이터 및 GeoJSON 로드"""
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

    # 데이터 로드
    geojson, df_db = load_all_data()

    if df_db.empty:
        st.title("🌱 전국 친환경차 현황 대시보드")
        st.warning("데이터베이스에 표시할 데이터가 없습니다.")
        st.info("데이터베이스 상태와 초기 데이터(Crawl) 여부를 확인해 주세요.")
        return

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

# --- 네비게이션 설정 ---
pg = st.navigation([
    st.Page(dashboard_page, title="전국 보급 현황", icon="🌱"),
    st.Page("pages/compare.py", title="차량 유지비 비교", icon="🔍"),
    st.Page("pages/faq.py", title="친환경차 통합 FAQ", icon="📝"),
    st.Page("pages/infrastructure.py", title="충전소 인프라 현황", icon="⚡"),
])
pg.run()
=======
# 1. 페이지 설정
st.set_page_config(page_title="🌱 전국 친환경차 현황 대시보드", layout="wide")

@st.cache_data
def load_data():
    # 데이터 로드
    df_main = pd.read_csv("전기차_일반차_통합.csv", encoding="utf-8-sig")
    df_fuel = pd.read_csv("지역별_연료별_등록대수_최종.csv", encoding="utf-8-sig")
    
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

    # 데이터 타입 정제
    df_main['year'] = df_main['year'].astype(int)
    df_fuel['연도'] = df_fuel['연도'].astype(float).astype(int)

    # 💡 [연산 교정] 보급률 계산 로직 수정
    # '일반차' 데이터가 이미 '전체 차량수'를 의미하는 경우가 많으므로 확인이 필요합니다.
    # 여기서는 '일반차'를 '내연기관+기타'로 보고 전체 대수를 산출합니다.
    df_main['총자동차'] = df_main['count_ev'] + df_main['일반차']
    df_main['보급률'] = (df_main['count_ev'] / df_main['총자동차']) * 100

    return geojson, df_main, df_fuel

geojson, df_main, df_fuel = load_data()

# --- 2. KPI 계산 (연산 오류 방지를 위한 정밀 계산) ---
target_year = 2026
# 중복 방지를 위해 연도별로 정확히 분리
df_2026 = df_main[df_main['year'] == target_year].drop_duplicates(['region'])
df_2025 = df_main[df_main['year'] == 2025].drop_duplicates(['region'])

# 전국 단위 총합 계산
total_ev_2026 = df_2026['count_ev'].sum()
total_cars_2026 = df_2026['총자동차'].sum()
total_ev_2025 = df_2025['count_ev'].sum()

# 전국 지표 산출
avg_ratio = (total_ev_2026 / total_cars_2026) * 100
# (금년 총합 - 전년 총합) / 전년 총합
total_growth = ((total_ev_2026 - total_ev_2025) / total_ev_2025) * 100

# --- 3. UI 레이아웃 ---
st.title(f"🌱 전국 친환경차 현황 대시보드 ({target_year})")
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
    st.markdown("### 🗺️ 지역별 보급률 지도 (%)")
    fig_map = px.choropleth_mapbox(
        df_2026, geojson=geojson, locations='region_full', featureidkey="properties.name",
        color='보급률', color_continuous_scale="YlGn", mapbox_style="carto-positron",
        zoom=5.5, center={"lat": 35.9, "lon": 127.7}, opacity=0.7,
        hover_name='region_full',
        hover_data={'region_full': False, '보급률': ':.2f', 'count_ev': ':,.0f'}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
    
    if map_event and "selection" in map_event:
        points = map_event["selection"].get("points", [])
        if points:
            clicked_region = points[0].get("location")
            if clicked_region in df_main['region_full'].values:
                st.session_state.selected_region = clicked_region
                st.rerun()

with trend_col:
    st.markdown(f"### 📈 {st.session_state.selected_region} 등록 추이")
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

# --- 5. 연료별 도넛 차트 ---
st.markdown(f"### 🔍 {st.session_state.selected_region} 연료별 비중 (2026)")
region_fuel = df_fuel[(df_fuel['지역_full'] == st.session_state.selected_region) & (df_fuel['연도'] == 2026)]

if not region_fuel.empty:
    fig_donut = px.pie(region_fuel, values='대수', names='연료', hole=.4,
                    color_discrete_sequence=px.colors.qualitative.Safe)
    fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20}, height=400)
    st.plotly_chart(fig_donut, use_container_width=True)
>>>>>>> origin/feature-23
