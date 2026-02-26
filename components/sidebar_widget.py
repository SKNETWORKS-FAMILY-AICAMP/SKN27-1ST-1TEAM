import streamlit as st

def render_sidebar_widget():
    html_content = """
    <style>
    .eco-widget-container {
        background-color: #F8FAFC;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
    }
    .eco-top-icons {
        font-size: 28px;
        margin-bottom: 12px;
        display: flex;
        justify-content: center;
        gap: 15px;
        align-items: center;
    }
    .eco-charging-text {
        color: #4ADE80;
        font-weight: 800;
        letter-spacing: 3px;
        font-size: 14px;
        margin-bottom: 20px;
        text-shadow: 0px 1px 2px rgba(0,0,0,0.05);
    }
    .eco-button-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 24px;
        gap: 12px;
    }
    .eco-mode-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px 8px;
        flex: 1;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        border: 1px solid #F1F5F9;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .eco-mode-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .eco-mode-icon {
        font-size: 24px;
        margin-bottom: 8px;
    }
    .eco-mode-text {
        font-size: 11px;
        color: #475569;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .eco-bottom-panel {
        background: linear-gradient(180deg, #E0F2FE 0%, #BAE6FD 100%);
        border-radius: 12px;
        padding: 24px 15px 15px 15px;
        position: relative;
        overflow: hidden;
    }
    /* 하단 애니메이션 랩퍼 추가 (컨테이너 전체 폭 기준) */
    .eco-scene-container {
        position: relative;
        height: 35px;
        margin-bottom: 6px;
        z-index: 2;
        display: flex;
        align-items: flex-end;
    }
    .eco-scene-trees {
        position: absolute;
        width: 100%;
        display: flex;
        justify-content: space-around;
        font-size: 24px;
    }
    .eco-road {
        background-color: #64748B;
        height: 6px;
        border-radius: 3px;
        margin: 0 -5px 16px -5px;
        position: relative;
        z-index: 2;
    }
    .eco-bottom-text {
        color: #0369A1;
        font-weight: 800;
        font-size: 13px;
        letter-spacing: 1px;
        position: relative;
        z-index: 2;
    }
    .eco-lightning {
        color: #F59E0B;
    }
    .eco-cloud {
        position: absolute;
        font-size: 32px;
        opacity: 0.4;
        top: 0px;
        left: 25%;
        z-index: 1;
    }
    
    /* 애니메이션 추가 */
    /* 위쪽 자동차 상하 운동 */
    @keyframes bounceCar {
        0%, 100% { transform: translateY(0) scaleX(-1); }
        50% { transform: translateY(-5px) scaleX(-1); }
    }
    
    /* 아래쪽 자동차 좌우 횡단 (끝에서 끝으로 반복) */
    @keyframes driveCar {
        0% { left: -10%; transform: scaleX(-1); }
        100% { left: 110%; transform: scaleX(-1); }
    }
    
    @keyframes blinkLightning {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(1.1); }
    }

    .bounce-car {
        animation: bounceCar 2s ease-in-out infinite;
        display: inline-block;
        position: relative; /* 번개 배치를 위해 추가 */
    }
    
    /* Bottom Scene 자동차 클래스 */
    .drive-car {
        position: absolute;
        font-size: 24px;
        bottom: 0px;
        animation: driveCar 4s linear infinite;
        z-index: 3;
    }

    .blinking-lightning {
        animation: blinkLightning 1.5s infinite;
        display: inline-block;
        color: #F87171; 
        position: absolute; 
        font-size: 18px; 
        top: -10px;
        right: -8px;
    }
    </style>
    
    <div class="eco-widget-container">
        <div class="eco-top-icons">
            <span style="display:inline-block; transform: scaleX(-1);">🔌</span> 
            <span class="bounce-car">🚘<span class="blinking-lightning">⚡</span></span>
        </div>
        <div class="eco-charging-text">
            C H A R G I N G . . .
        </div>
        <div class="eco-button-container">
            <div class="eco-mode-card">
                <div class="eco-mode-icon">🔋</div>
                <div class="eco-mode-text">MAX POWER</div>
            </div>
            <div class="eco-mode-card">
                <div class="eco-mode-icon">🌿</div>
                <div class="eco-mode-text">ECO MODE</div>
            </div>
        </div>
        <div class="eco-bottom-panel">
            <div class="eco-cloud">☁️</div>
            <div class="eco-scene-container">
                <div class="eco-scene-trees">
                    <span style="visibility:hidden">X</span> <!-- 공간 차지용 투명문자 -->
                    <span style="font-size: 16px;">🌲</span>
                    <span>🌳</span>
                </div>
                <span class="drive-car">🚙</span>
            </div>
            <div class="eco-road"></div>
            <div class="eco-bottom-text">
                ECO CITY FUTURE <span class="eco-lightning">⚡</span>
            </div>
        </div>
    </div>
    """
    
    # Remove newlines to prevent Streamlit from wrapping inner divs with <p> tags
    clean_html = html_content.replace("\n", "")
    st.markdown(clean_html, unsafe_allow_html=True)
