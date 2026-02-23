import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import random

# 페이지 기본 설정
st.set_page_config(page_title="친환경차 대시보드", layout="wide")

@st.cache_data
def load_data():
    """데이터 로드"""
    # GeoJSON 로드 (대한민국 시/도 경계 단순화 버전)
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"
    geojson = requests.get(geojson_url).json()

    # GeoJSON에서 지역명 추출
    regions = [feature['properties']['name'] for feature in geojson['features']]
    
    df_elec = pd.read_csv("region_elec.csv", encoding="utf-8-sig") #지역별 전기차 현황
    df_diesel = pd.read_csv("region_diesel.csv", encoding="utf-8-sig") # 지역별 일반차 현황
    df_submn = pd.read_csv("submn_region.csv", encoding="utf-8-sig") #지역별 전기차 보조금

    df_elect_region = df_elec[df_elect_region[:0] == '지역총합']
    df_

    
    random.seed(42)

    # 1. 시도별 친환경차 보급대수 및 보급률 등 기본 데이터
    current_data = [] #각 지역의 정보가 딕셔너리 형태로 리스트에 저장됨
    for region in regions: #지역수만큼 반복
        eco_cars = 0  #친환경차 보급대수
        total_cars = eco_cars +1  #전체 차량대수
        ratio = round((eco_cars / total_cars) * 100, 1) #보급률
        current_data.append({
            '지역': region,
            '보급대수': eco_cars,
            '전체대수': total_cars,
            '보급률': ratio
        })
    df_current = pd.DataFrame(current_data)

    # 2. 지역별 연도별 추이 데이터 (최근 5년: 2019 ~ 2023)
    # 내연기관과 친환경차 라인 크로스 효과를 위해 조정
    years = [2019, 2020, 2021, 2022, 2023]
    trend_data = []
    for region in regions:
        eco_base = random.randint(2000, 5000)
        ice_base = random.randint(150000, 300000) # 내연기관 베이스
        
        for year in years:
            trend_data.append({
                '지역': region,
                '연도': year,
                '차종': '친환경차',
                '대수': eco_base
            })
            trend_data.append({
                '지역': region,
                '연도': year,
                '차종': '내연기관차',
                '대수': ice_base
            })
            # 친환경차는 급성장, 내연기관차는 완만하게 감소
            eco_base = int(eco_base * random.uniform(1.3, 1.8))
            ice_base = int(ice_base * random.uniform(0.95, 0.99))
            
    df_trend = pd.DataFrame(trend_data)
    
    # 3. 상세 지역(구/군) 데이터 및 차종별 비율 데이터 (서울특별시 예시 생성용)
    fuel_types = ['휘발유', '경유', '전기', '수소']
    detail_data = []
    for region in regions:
        # 차종 비율을 위한 랜덤 값 생성
        petrol = random.randint(40, 60)
        diesel = random.randint(20, 40)
        ev = random.randint(5, 15)
        fcv = max(1, 100 - (petrol + diesel + ev)) # 나머지 수소
        
        # 구/군 순위용 데이터 생성 (지역별 가상의 3개 구)
        sub_regions = [f"{region} A구", f"{region} B구", f"{region} C구"]
        sub_values = [random.randint(1000, 5000) for _ in range(3)]
        sub_values.sort(reverse=True) # 내림차순 정렬
        
        detail_data.append({
            '지역': region,
            '비율_휘발유': petrol,
            '비율_경유': diesel,
            '비율_전기': ev,
            '비율_수소': fcv,
            'Top1_구': sub_regions[0], 'Top1_대수': sub_values[0],
            'Top2_구': sub_regions[1], 'Top2_대수': sub_values[1],
            'Top3_구': sub_regions[2], 'Top3_대수': sub_values[2],
        })
        
    df_detail = pd.DataFrame(detail_data)

    return geojson, df_current, df_trend, df_detail

# 데이터 로드
try:
    geojson, df_current, df_trend, df_detail = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 상태 관리 (세션 스테이트) ---
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "서울특별시"

def update_region_from_selectbox():
    st.session_state.selected_region = st.session_state.region_selectbox

# ==========================================
# 🌟 1단: 시선을 사로잡는 핵심 지표 (KPI Metrics)
# ==========================================
st.title("🌱 전국 친환경차 현황 대시보드")
st.markdown("---")

# 전체 합산 계산 (Mock Data 활용 방식)
total_eco_cars = df_current['보급대수'].sum()
total_all_cars = df_current['전체대수'].sum()
avg_ratio = (total_eco_cars / total_all_cars) * 100

# 3개의 컬럼으로 분할
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

with kpi_col1:
    st.metric(label="전국 친환경차 누적 등록 대수", value=f"{total_eco_cars:,.0f} 대", delta="전년 대비 +42,105 대")
with kpi_col2:
    st.metric(label="전년 동기 대비 증가율", value="24.5%", delta="15.2%", delta_color="normal")
with kpi_col3:
    st.metric(label="전체 차량 중 친환경차 비율", value=f"{avg_ratio:.1f}%", delta="전월 대비 +0.3%p")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 🗺️ 2단: 전국 현황 시각화 (Map & Trend)
# ==========================================
map_col, trend_col = st.columns([6, 4]) # 6:4 비율

with map_col:
    st.markdown("### � 지역별 보급률 지도")
    st.caption("색상이 진할수록 보급률이 높은 지역입니다. (단위: %) 지도를 클릭하여 연동된 상세 정보를 확인하세요.")
    
    # 보급률 기준으로 툴팁 내용 구성
    hover_data_dict = {
        '보급대수': ':,', 
        '보급률': ':.1f'
    }

    # Plotly Choropleth Map (지도 시각화)
    fig_map = px.choropleth_mapbox(
        df_current, 
        geojson=geojson, 
        locations='지역', 
        featureidkey="properties.name",
        color='보급률',
        color_continuous_scale="Greens",
        mapbox_style="carto-positron",
        zoom=5.5, 
        center={"lat": 36.3, "lon": 127.7},
        opacity=0.8,
        hover_data=hover_data_dict,
        labels={'보급률': '친환경차 보급률(%)', '보급대수': '등록 대수(대)'}
    )
    # 툴팁 형태 수정 ("지역명: 값%" 형태)
    fig_map.update_traces(hovertemplate='<b>%{location}</b><br>보급률: %{z:.1f}%<br>등록대수: %{customdata[0]:,}대')
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    # 지도 클릭 시 Session State 연동
    map_event = st.plotly_chart(fig_map, use_container_width=True, on_select="rerun", selection_mode="points")
    
    if map_event and map_event.get("selection", {}).get("points"):
        clicked_region = map_event["selection"]["points"][0].get("location")
        if clicked_region and clicked_region != st.session_state.selected_region:
            st.session_state.selected_region = clicked_region
            # Session State 내 드롭다운 key 값도 함께 동기화
            st.session_state.region_selectbox = clicked_region
            st.rerun()

with trend_col:
    st.markdown("### 📈 전체/친환경차 연도별 성장 추이")
    st.caption("최근 5년간 내연기관차와 친환경차의 추세 크로스(Cross) 라인")
    
    # 친환경차 vs 내연기관차 비교 라인 차트 (전국 데이터 합산 활용)
    national_trend = df_trend.groupby(['연도', '차종'])['대수'].sum().reset_index()
    
    fig_trend = px.line(
        national_trend, 
        x='연도', 
        y='대수', 
        color='차종',
        color_discrete_map={'친환경차': '#2ca02c', '내연기관차': '#7f7f7f'},
        markers=True
    )
    fig_trend.update_layout(
        xaxis_type='category', 
        legend_title_text=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    # y축 두개 효과를 위해 친환경 변화가 잘보이도록 구성하거나 로그스케일 적용 가능, 여기서는 일반
    
    st.plotly_chart(fig_trend, use_container_width=True)


st.markdown("<br><hr>", unsafe_allow_html=True)

# ==========================================
# 🔍 3단: 지역별 딥다이브 (Interactive Selectbox)
# ==========================================
st.markdown("### 🔍 지역별 상세 데이터 (Deep-dive)")

all_regions = df_current['지역'].tolist()
if st.session_state.selected_region not in all_regions:
    st.session_state.selected_region = all_regions[0] if all_regions else None
selected_index = all_regions.index(st.session_state.selected_region)

# 1. 드롭다운 선택 부
col_select, _ = st.columns([1, 2])
with col_select:
    selected_region = st.selectbox(
        "상세 분석할 지역을 선택하세요:", 
        options=all_regions, 
        index=selected_index,
        key="region_selectbox",
        on_change=update_region_from_selectbox
    )

req_detail = df_detail[df_detail['지역'] == st.session_state.selected_region].iloc[0]

# 하단 레이아웃 분할 (도넛 차트 vs Top3 테이블)
detail_col1, detail_col2 = st.columns([1, 1])

with detail_col1:
    st.markdown(f"**[{st.session_state.selected_region}] 차종별 등록 비율**")
    
    # 도넛 차트 생성를 위한 데이터 정리
    labels = ['휘발유', '경유', '전기', '수소']
    values = [req_detail['비율_휘발유'], req_detail['비율_경유'], req_detail['비율_전기'], req_detail['비율_수소']]
    colors = ['#ff9999', '#c2c2f0', '#66b3ff', '#99ff99']
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5, # 도넛 모양
        marker_colors=colors
    )])
    fig_donut.update_layout(margin={"r":20,"t":20,"l":20,"b":20},  height=300)
    st.plotly_chart(fig_donut, use_container_width=True)

with detail_col2:
    st.markdown(f"**[{st.session_state.selected_region}] 친환경차 등록대수 Top 3 구/군**")
    
    # Table 형태로 시각화하기 위한 DataFrame 구성
    top3_df = pd.DataFrame({
        "순위": ["🥇 1위", "🥈 2위", "🥉 3위"],
        "구/군 명칭": [req_detail['Top1_구'], req_detail['Top2_구'], req_detail['Top3_구']],
        "등록 대수(대)": [f"{req_detail['Top1_대수']:,}", f"{req_detail['Top2_대수']:,}", f"{req_detail['Top3_대수']:,}"]
    })
    
    # st.dataframe으로 깔끔하게 표시
    st.dataframe(
        top3_df,
        column_config={
            "순위": st.column_config.Column(width="small"),
            "구/군 명칭": st.column_config.Column(width="medium"),
            "등록 대수(대)": st.column_config.NumberColumn(width="medium")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.info("💡 **ESG 인사이트**: 해당 지역의 친환경차 보급은 주요 도심 및 신도시 위주로 집중되어 상승세를 견인하고 있습니다.")