import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
# -----------------------------
# 1. 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="전국 전기차 현황 대시보드", layout="wide"
)

# -----------------------------
# 2. 타이틀
# -----------------------------
st.title("전기차 보급 현황 대시보드")
st.markdown("---")

# -----------------------------
# 3. 상단 KPI 영역
# -----------------------------
k1, k2, k3 = st.columns(3)

with k1:
    st.metric("전국 전기차 누적 등록", "-")

with k2:
    st.metric("평균 전년 대비 증감률", "-")

with k3:
    st.metric("평균 전기차 보급률", "-")

st.markdown("---")

# -----------------------------
# 4. 지도 + 추이 영역
# -----------------------------
map_col, trend_col = st.columns([6, 4])

with map_col:
    st.subheader("🗺️ 지역별 보급률 지도")

    empty_map = go.Figure()
    empty_map.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(empty_map, use_container_width=True)

with trend_col:
    st.subheader("📈 지역 성장 추이")

    empty_line = go.Figure()
    empty_line.update_layout(height=500)

    st.plotly_chart(empty_line, use_container_width=True)

st.markdown("---")

# -----------------------------
# 5. 상세 분석 영역
# -----------------------------
st.subheader("🔍 상세 분석")

d1, d2 = st.columns(2)

with d1:
    st.markdown("**연료별 등록 비중**")

    donut = go.Figure()
    donut.update_layout(height=300)

    st.plotly_chart(donut, use_container_width=True)

with d2:
    st.markdown("**차종별 평균 보조금 현황**")

    st.table({
        "차종 구분": [],
        "평균 보조금": [],
        "최대 보조금": []
    })