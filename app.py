import streamlit as st

# 페이지 기본 설정 (가장 위에 와야 함)
st.set_page_config(page_title="친환경 모빌리티 대시보드", page_icon="🌍", layout="wide")

st.title("🗺️ 전국 친환경 모빌리티 보급 현황")
st.write("이곳에는 Plotly를 활용한 전국 색상 지도와 지역별 핵심 요약 지표가 들어갈 예정입니다.")

# 임시 레이아웃 분할
col1, col2 = st.columns([2, 1])
with col1:
    st.info("지도 시각화 영역 (공공데이터 CSV 연동 예정)")
with col2:
    st.success("지역별 세부 그래프 영역")