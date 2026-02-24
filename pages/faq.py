import streamlit as st
import traceback

try:
    from utils.db_manager import db_manager
    import pandas as pd

    # 페이지 설정 (사이드바 메뉴 유지는 위해 필요)
    # st.set_page_config(page_title="현대자동차 FAQ", page_icon="📝", layout="wide")

    st.title("📝 친환경차 통합 FAQ")
    st.markdown("다양한 브랜드와 기관의 자주 묻는 질문을 한곳에서 모아보세요.")
    st.write("---")

    # DB 데이터 로드
    try:
        df = db_manager.fetch_query("SELECT * FROM faq_data")
    except Exception as db_err:
        st.error(f"DB 연결 실패: {db_err}")
        st.stop()

    if df.empty:
        st.warning("수집된 데이터가 없습니다.")
        if st.button("데이터 수집 시작 (전체 브렌드)"):
            with st.spinner("데이터를 수집 중입니다..."):
                import subprocess
                import sys
                result = subprocess.run([sys.executable, "scripts/crawl_faq.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("수집 완료!")
                    st.rerun()
                else:
                    st.error(f"수집 실패: {result.stderr}")
        st.stop()

    # 상단 필터 (브랜드 및 카테고리)
    col1, col2 = st.columns(2)
    
    with col1:
        sources = ["전체"] + sorted(df["source"].unique().tolist())
        selected_source = st.selectbox("📌 브랜드/출처 선택", sources)
    
    # 필터링 1: 브랜드
    if selected_source != "전체":
        df = df[df["source"] == selected_source]

    with col2:
        categories = ["전체"] + sorted(df["category"].unique().tolist())
        selected_category = st.selectbox("📂 카테고리 선택", categories)

    # 필터링 2: 카테고리
    if selected_category != "전체":
        df = df[df["category"] == selected_category]

    st.info(f"선택된 조건에 맞는 질문이 **{len(df)}개** 검색되었습니다.")

    # FAQ 목록 표시
    for _, row in df.iterrows():
        source_label = f"[{row['source']}] " if selected_source == "전체" else ""
        with st.expander(f"{source_label}{row['question']}"):
            st.markdown(f"**카테고리:** {row['category']}")
            st.markdown("---")
            st.markdown(row['answer'], unsafe_allow_html=True)

    # 데이터 수집 버튼 (하단)
    st.write("---")
    if st.button("🔄 최신 데이터로 업데이트 (크롤링 실행)"):
        with st.spinner("전체 사이트에서 최신 FAQ를 가져오는 중입니다..."):
            import subprocess
            import sys
            subprocess.run([sys.executable, "scripts/crawl_faq.py"])
            st.success("업데이트 완료!")
            st.rerun()

except Exception as global_err:
    st.error("페이지 실행 중 오류가 발생했습니다.")
    st.code(traceback.format_exc())
