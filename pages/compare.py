import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db_manager import db_manager

# 페이지 기본 설정
st.set_page_config(page_title="유지비 비교 분석", page_icon="⚖️", layout="wide")

st.title("⚖️ 내연기관 vs 친환경차 유지비 비교")
st.markdown("사용자의 주행 거리에 따른 **연료비** 및 **N년차 누적 유지비**를 직관적으로 비교해 드립니다.")
st.markdown("---")

# ==========================================
# 📍 1단계: 조건 설정 (Sidebar 또는 Expander 활용)
# ==========================================
with st.sidebar:
    st.header("⚙️ 시뮬레이션 설정")
    
    st.subheader("1. 연간 주행 거리 (km)")
    mileage = st.slider("연간 몇 km를 주행하시나요?", min_value=5000, max_value=50000, value=15000, step=1000)
    
    st.markdown("---")
    st.subheader("2. 차량 기본 정보 세팅")
    
    # 📌 베이스라인 차량(내연기관) 설정
    st.markdown("**🔹 내연기관차 (가솔린 기준)**")
    ice_price = st.number_input("차량 가격 (만원)", value=3000, step=100)
    ice_fuel_eff = st.number_input("연비 (km/L)", value=12.0, step=0.1)
    ice_fuel_cost = st.number_input("가솔린 가격 (원/L)", value=1600, step=10)
    
    st.markdown("**🔹 친환경차 (전기차 기준)**")
    # 보조금을 반영한 실구매가 입력 권장
    ev_price = st.number_input("차량 가격 (보조금 적용 후, 만원)", value=3800, step=100)
    ev_fuel_eff = st.number_input("전비 (km/kWh)", value=5.5, step=0.1)
    ev_fuel_cost = st.number_input("전기차 충전 요금 (원/kWh)", value=320, step=10)
    
    # 자동차세 등 고정비 (연간) - 편의상 간략화
    st.markdown("---")
    
    # [TODO] 향후 이 고정값들도 MySQL 테이블(settings 등)에서 관리 가능
    ice_tax = 50  # 약 50만원 (2000cc 기준)
    ev_tax = 13   # 약 13만원 (전기차 일괄)
    st.info(f"연간 자동차세: 내연기관(약 {ice_tax}만 원) / 전기차(약 {ev_tax}만 원)")

# ==========================================
# 📊 2단계: 데이터 계산
# ==========================================
# 1년치 연료비 계산 (단위: 만원)
# (연간 주행거리 / 연비) * 리터당 가격 / 10000
ice_annual_fuel = (mileage / ice_fuel_eff) * ice_fuel_cost / 10000
ev_annual_fuel = (mileage / ev_fuel_eff) * ev_fuel_cost / 10000

# 연간 총 유지비 (연료비 + 자동차세)
ice_annual_total = ice_annual_fuel + ice_tax
ev_annual_total = ev_annual_fuel + ev_tax

# 5년치 누적 데이터 프레임 생성
# X년차 누적 = 차량가격 + (연간유지비 * X년)
years = range(1, 11) # 1년부터 10년까지
data = []

for y in years:
    data.append({
        "년차": f"{y}년차",
        "차종": "내연기관차",
        "누적 비용 (만원)": ice_price + (ice_annual_total * y)
    })
    data.append({
        "년차": f"{y}년차",
        "차종": "친환경차(EV)",
        "누적 비용 (만원)": ev_price + (ev_annual_total * y)
    })

df_cumulative = pd.DataFrame(data)

# ==========================================
# 📈 3단계: 결과 시각화
# ==========================================

# 상단: 1년 유지비 KPI 요약
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("내연기관차 1년 유지비", f"{ice_annual_total:,.0f} 만원")
with col2:
    st.metric("친환경차 1년 유지비", f"{ev_annual_total:,.0f} 만원", delta=f"{ev_annual_total - ice_annual_total:,.0f} 만원 (절감액)", delta_color="inverse")
with col3:
    # 역전 시기 (Payback Period) 계산
    # (EV차량가 - ICE차량가) / (ICE연간유지비 - EV연간유지비)
    price_diff = ev_price - ice_price
    cost_saving = ice_annual_total - ev_annual_total
    
    if cost_saving > 0 and price_diff > 0:
        payback_year = price_diff / cost_saving
        st.metric("손익 분기점 (초기비용 회수)", f"약 {payback_year:.1f}년 후")
    elif price_diff <= 0:
         st.metric("손익 분기점", "구매 즉시 이득!")
    else:
        st.metric("손익 분기점", "회수 불가 (유지비 동일/비쌈)")


st.markdown("<br>", unsafe_allow_html=True)

# 차트 영역: 2개의 열로 나누어 Bar 차트와 Line 차트 배치
chart_col1, chart_col2 = st.columns([1, 1])

with chart_col1:
    st.subheader("📊 1년 유지비 상세 비교")
    
    # 누적 막대 그래프용 데이터 (연료비, 세금)
    bar_data = pd.DataFrame({
        "차종": ["내연기관차", "친환경차(EV)"],
        "연료비 (만원)": [ice_annual_fuel, ev_annual_fuel],
        "자동차세 (만원)": [ice_tax, ev_tax]
    })
    
    fig_bar = px.bar(
        bar_data, 
        x="차종", 
        y=["연료비 (만원)", "자동차세 (만원)"],
        title=f"연간 주행거리 {mileage:,}km 기준",
        barmode='stack',
        color_discrete_sequence=['#ff9999', '#ffcc99'] # 커스텀 컬러
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.subheader("📈 N년차 누적 총비용 (차량가 + 유지비)")
    
    fig_line = px.line(
        df_cumulative, 
        x="년차", 
        y="누적 비용 (만원)", 
        color="차종",
        markers=True,
        color_discrete_map={"내연기관차": "#7f7f7f", "친환경차(EV)": "#00cc96"}
    )
    
    # 역전 포인트(교차점) 강조 시각화 효과
    fig_line.update_layout(hovermode="x unified")
    fig_line.update_traces(line=dict(width=3))
    st.plotly_chart(fig_line, use_container_width=True)

# ==========================================
# 💡 4단계: 동적 인사이트 메세지
# ==========================================
st.markdown("---")
st.subheader("💡 맞춤형 분석 리포트")

if cost_saving > 0 and price_diff > 0:
    st.success(f"현재 선택하신 연간 **{mileage:,}km** 주행 기준으로, 친환경차를 구매하시면 매년 **약 {cost_saving:,.0f}만 원**의 유지비를 절약할 수 있습니다. 초기 차량 가격 차이({price_diff:,}만 원)를 감안할 때, **약 {payback_year:.1f}년** 이상 차량을 운행하신다면 친환경차가 경제적으로 훨씬 유리합니다!")
elif price_diff <= 0:
    st.success(f"친환경차의 실 구매가가 더 저렴하며, 매년 유지비도 **{cost_saving:,.0f}만 원** 절약되므로 완벽한 경제적 선택입니다!")
else:
    st.warning("현재 주행거리 및 설정 기준으로는 초기 차량 가격 차이를 상쇄하기 어렵습니다. 연간 주행거리가 더 길거나 충전/보조금 혜택이 클수록 친환경차가 유리해집니다.")
