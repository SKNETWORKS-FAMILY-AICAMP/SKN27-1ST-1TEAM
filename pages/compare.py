import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ==========================================
# 🎨 프리미엄 UI 스타일 설정 (CSS)
# ==========================================
st.markdown("""
<style>
    .main {
        background-color: #fcfdfe;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #0f172a;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #f1f5f9;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 20px;
        padding-left: 10px;
        border-left: 5px solid #3b82f6;
    }
    .report-box {
        background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
        padding: 24px;
        border-radius: 12px;
        border-left: 5px solid #2563eb;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ 친환경차 경제성 분석")
st.markdown("내연기관차와 전기차의 **초기 구입비** 및 **유지비**를 정밀 비교하여 최적의 선택을 도와드립니다.")
st.markdown("---")

# ==========================================
# 📍 1단계: 조건 설정 (사이드바)
# ==========================================
with st.sidebar:
    st.header("⚙️ 시뮬레이션 설정")
    
    st.subheader("1. 주행 패턴")
    mileage = st.slider("연간 주행 거리 (km)", min_value=5000, max_value=50000, value=15000, step=1000)
    
    st.markdown("---")
    st.subheader("2. 차량 비교 데이터")
    
    with st.expander("🚗 내연기관차 (가솔린)", expanded=True):
        ice_price = st.number_input("차량 가격 (만원)", value=3000, step=100, key="ice_v2_p")
        ice_fuel_eff = st.number_input("연비 (km/L)", value=12.5, step=0.1, key="ice_v2_f")
        ice_fuel_cost = st.number_input("연료비 (원/L)", value=1650, step=10, key="ice_v2_c")
    
    with st.expander("⚡ 전기차 (EV)", expanded=True):
        ev_price = st.number_input("차량 실구매가 (만원)", value=3800, step=100, key="ev_v2_p")
        ev_fuel_eff = st.number_input("전비 (km/kWh)", value=5.5, step=0.1, key="ev_v2_f")
        ev_fuel_cost = st.number_input("충전 요금 (원/kWh)", value=340, step=10, key="ev_v2_c")
    
    ice_tax = 52 # 자동차세+지방교육세
    ev_tax = 13  # 전기차 일괄
    st.caption(f"기준: 연간 자동차세 (내연기관 {ice_tax}만, 전기차 {ev_tax}만)")

# ==========================================
# 📊 2단계: 핵심 계산 및 입력 검증
# ==========================================

# 변수 초기화
payback = None

# 입력 값 검증
if ice_fuel_eff <= 0 or ev_fuel_eff <= 0 or ev_fuel_cost > ice_fuel_cost:
    st.error("잘못된 값을 입력했습니다.")
    st.stop()

ice_fuel_annual = (mileage / ice_fuel_eff) * ice_fuel_cost / 10000
ev_fuel_annual = (mileage / ev_fuel_eff) * ev_fuel_cost / 10000

ice_total_annual = ice_fuel_annual + ice_tax
ev_total_annual = ev_fuel_annual + ev_tax

saving_annual = ice_total_annual - ev_total_annual
price_diff = ev_price - ice_price

if saving_annual > 0:
    payback = price_diff / saving_annual

# 누적 비용 데이터
years_arr = np.arange(0, 11)
ice_costs = ice_price + ice_total_annual * years_arr
ev_costs = ev_price + ev_total_annual * years_arr

# ==========================================
# 📉 3단계: 시각화
# ==========================================

# KPI Metrics
st.markdown('<p class="section-title">💡 경제성 요약</p>', unsafe_allow_html=True)
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric("연간 유지비 (내연기관)", f"{ice_total_annual:,.0f} 만원")
with kpi2:
    st.metric("연간 유지비 (전기차)", f"{ev_total_annual:,.0f} 만원", 
              delta=f"{saving_annual:,.0f} 만원 절감", delta_color="normal")
with kpi3:
    if saving_annual > 0:
        if price_diff <= 0:
            st.metric("초기비용 회수 기간", "즉시 이득")
        else:
            st.metric("초기비용 회수 기간", f"{payback:.1f} 년")
    else:
        st.metric("초기비용 회수 기간", "회수 불가")

st.markdown("<br>", unsafe_allow_html=True)

# Charts Section
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 1년 유지비 구성")
    
    fig_bar = go.Figure()
    # 내연기관
    fig_bar.add_trace(go.Bar(
        x=['내연기관', '전기차'], y=[ice_fuel_annual, ev_fuel_annual],
        name='연료비', marker_color='#475569', width=0.4
    ))
    fig_bar.add_trace(go.Bar(
        x=['내연기관', '전기차'], y=[ice_tax, ev_tax],
        name='자동차세', marker_color='#10b981', width=0.4
    ))
    
    fig_bar.update_layout(
        barmode='stack',
        height=400,
        margin=dict(t=10, b=10, l=10, r=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="단위: 만원", gridcolor='#f1f5f9'),
        xaxis=dict(gridcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown("### 📈 누적 보유 총비용")
    
    fig_line = go.Figure()
    
    # 영역 채우기 및 스플라인 곡선
    fig_line.add_trace(go.Scatter(
        x=years_arr, y=ice_costs, name='내연기관차',
        mode='lines', line=dict(color='#94a3b8', width=2, dash='dot'),
    ))
    
    fig_line.add_trace(go.Scatter(
        x=years_arr, y=ev_costs, name='전기차 (EV)',
        mode='lines', line=dict(color='#3b82f6', width=4, shape='spline'),
        fill='tonexty', fillcolor='rgba(59, 130, 246, 0.05)'
    ))

    # 손익분기점 포인트 추가 (있는 경우)
    if payback is not None and 0 < payback <= 10:
        be_cost = ice_price + ice_total_annual * payback
        fig_line.add_trace(go.Scatter(
            x=[payback], y=[be_cost],
            mode='markers+text',
            name='손익분기점',
            text=[f" {payback:.1f}년차 교차"],
            textposition="top right",
            marker=dict(color='#f43f5e', size=12, symbol='star')
        ))

    fig_line.update_layout(
        height=400,
        margin=dict(t=10, b=10, l=10, r=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="보유 연차", gridcolor='#f1f5f9', dtick=1),
        yaxis=dict(title="누적 비용 (만원)", gridcolor='#f1f5f9')
    )
    st.plotly_chart(fig_line, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 💡 4단계: 분석 리포트
# ==========================================
st.markdown('<p class="section-title">📝 시뮬레이션 결과 리포트</p>', unsafe_allow_html=True)

if saving_annual > 0:
    st.markdown(f"- **유지비 절감:** 현재 설정된 주행거리 기준, 전기차는 내연기관차 대비 매년 **약 {saving_annual:,.0f}만 원**의 지출을 줄여줍니다.")
    
    if price_diff > 0:
        st.markdown(f"- **초기 비용 회수:** 전기차 구매 시 더 지불한 초기 비용(**{price_diff:,}만 원**)은 약 **{payback:.1f}년**이 지나면 완전히 회수됩니다.")
    else:
        st.markdown(f"- **가격 경쟁력:** 전기차의 실구매가가 내연기관차와 같거나 더 저렴하여, **구매 즉시** 경제적 이득이 발생합니다.")
        
    st.markdown(f"- **10년 후 결과:** 10년 보유 시, 전기차는 내연기관차보다 총 **약 { (ice_costs[10] - ev_costs[10]):,.0f}만 원** 더 경제적입니다.")
    
    if payback is not None and payback <= 4:
        st.success("✨ **추천:** 운행 거리가 많아 전기차 전환 시 경제적 이득이 매우 빠르게 발생합니다! 강력 추천드립니다.")
    elif price_diff <= 0:
        st.success("✨ **강력 추천:** 초기 비용도 저렴하고 유지비도 절감되므로 망설일 이유가 없는 최고의 선택입니다!")
    elif price_diff >= 0 and price_diff <= 100:
        st.info("✨ **분석:** 장기 보유(5년 이상) 계획이 있으시다면 전기차가 경제적으로 유리한 선택이 됩니다.")
else:
    st.warning("⚠️ **주의:** 현재 입력하신 조건(저연비 혹은 고가의 충전료 등)에서는 전기차의 경제적 이점이 크지 않을 수 있습니다.")

st.markdown('</div>', unsafe_allow_html=True)
