import streamlit as st
import pandas as pd
from utils.db_manager import db_manager
import plotly.express as px


st.title("⚡ 실시간 전기차 충전 인프라")
st.markdown("전국의 전기차 충전소 위치와 현황을 한눈에 확인하세요.")
st.write("---")



# DB 데이터 로드
try:
    df = db_manager.fetch_query("SELECT * FROM charging_stations")
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

if df.empty:
    st.warning("데이터가 없습니다. 상단 '데이터 동기화' 버튼을 눌러주세요.")
    if st.button("🔄 데이터 동기화 시작"):
        with st.spinner("최신 데이터를 가져오는 중..."):
            import subprocess
            import sys
            result = subprocess.run([sys.executable, "scripts/sync_infra.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("동기화 완료!")
                st.rerun()
            else:
                st.error(f"동기화 실패: {result.stderr}")
    st.stop()

# --- 상단 필터 ---
st.markdown("### 🔍 상세 검색 및 필터")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    operators = ["전체"] + sorted(df["operator"].unique().tolist())
    selected_operator = st.selectbox("🏢 운영기관 선택", operators)

with filter_col2:
    charger_type = st.radio("⚡ 충전기 타입", ["전체", "급속 위주", "완속 위주"], horizontal=True)

# 필터링 적용
filtered_df = df.copy()
if selected_operator != "전체":
    filtered_df = filtered_df[filtered_df["operator"] == selected_operator]

if charger_type == "급속 위주":
    filtered_df = filtered_df[filtered_df["fast_count"] > 0]
elif charger_type == "완속 위주":
    filtered_df = filtered_df[filtered_df["slow_count"] > 0]

# --- 통계 대시보드 ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("총 충전소", f"{len(filtered_df)}개")
col2.metric("총 급속 충전기", f"{filtered_df['fast_count'].sum()}개")
col3.metric("총 완속 충전기", f"{filtered_df['slow_count'].sum()}개")
col4.metric("평균 충전기 수", f"{filtered_df['fast_count'].mean() + filtered_df['slow_count'].mean():.1f}개")

st.write("---")

# --- 지도 시각화 ---
st.subheader("📍 충전소 위치 지도")
if not filtered_df.empty:
    # 좌표가 있는 데이터만 마커로 표시
    map_df = filtered_df[(filtered_df["lat"] != 0.0) & (filtered_df["lng"] != 0.0)]
    
    if map_df.empty:
        st.info("현재 선택된 충전소 중 지도 좌표가 제공된 데이터가 없습니다.")
    else:
        # Plotly를 이용한 지도 (더 유연함)
        fig = px.scatter_mapbox(
            map_df, 
            lat="lat", 
            lon="lng", 
            hover_name="name", 
            hover_data={
                "lat": False,
                "lng": False,
                "address": True, 
                "fast_count": True, 
                "slow_count": True, 
                "operator": True
            },
            labels={
                "address": "주소",
                "fast_count": "급속 충전기",
                "slow_count": "완속 충전기",
                "operator": "운영기관",
                "size": "충전기 수(규모)"
            },
            color="fast_count",
            size=map_df["fast_count"] + map_df["slow_count"],
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=15, 
            zoom=10,
            center={"lat": 37.65956, "lon": 126.8429},
            mapbox_style="carto-positron"
        )
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0}, 
            height=500,
            coloraxis_colorbar_title_text="충전기 수(규모)"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("선택된 조건에 맞는 충전소가 없습니다.")

# --- 충전소 목록 ---
st.write("---")
st.subheader("📋 충전소 상세 목록")
# 가독성을 위해 일부 컬럼만 표시
display_df = filtered_df[["name", "address", "fast_count", "slow_count", "operator"]]
display_df.columns = ["이름", "주소", "급속", "완속", "운영기관"]
st.dataframe(display_df, use_container_width=True, hide_index=True)
