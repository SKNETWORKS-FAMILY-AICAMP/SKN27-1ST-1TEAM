# 🚗 친환경차 모빌리티 대시보드 프로젝트 가이드

이 프로젝트는 전국 친환경차(EV) 보급 현황을 시각화하고, FAQ를 제공하며, 내연기관차와의 유지비를 비교할 수 있는 스트림릿(Streamlit) 기반 웹 애플리케이션입니다.

---

## 🚀 시작하기 (Setup Guide)

새로운 환경에서 프로젝트를 실행하기 위해 다음 단계를 순서대로 진행해 주세요.

### 1. 필수 요구사항 (Prerequisites)
- **Git**: 소스 코드 복제용
- **Docker & Docker Desktop**: MySQL 데이터베이스 실행용
- **Python 3.9+**: 로컬 실행용 (가상환경 권장)

### 2. 저장소 클론 (Clone Repository)
```bash
git clone [repository_url]
cd SKN27-1ST-1TEAM
```

### 3. 가상환경 및 패키지 설치
컴퓨터에 필요한 라이브러리를 설치합니다.
```bash
# 가상환경 생성 (선택 사항)
python -m venv .venv
source .venv/Scripts/activate  # Windows

# 필수 패키지 설치
pip install -r requirements.txt
```

### 4. 데이터베이스 실행 (Docker)
Docker Compose를 사용하여 MySQL DB를 실행합니다.
```bash
docker-compose up -d
```
> [!NOTE]
> DB가 실행되면 `localhost:3306`에서 접속 가능합니다. (유저: `user`, 비번: `password`)

### 5. 초기 데이터 수집 (Crawling)
FAQ 및 기초 데이터를 DB에 저장하기 위해 크롤러를 한 번 실행해야 합니다.
```bash
python scripts/crawl_faq.py
```
*현대차, 기아차, 한전 등의 FAQ 데이터를 자동으로 수집하여 DB에 저장합니다.*

### 6. 애플리케이션 실행
모든 준비가 끝났습니다! 스트림릿 서버를 실행합니다.
```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501`로 접속하여 확인하세요.

---

## 📂 주요 폴더 구조
- `app.py`: 메인 대시보드 및 내비게이션 설정
- `pages/`: 
    - `compare.py`: 차량 유지비 비교 시뮬레이터
    - `faq.py`: 통합 FAQ 조회 페이지
- `scripts/`:
    - `crawl_faq.py`: 멀티 소스 FAQ 크롤러
- `utils/`:
    - `db_manager.py`: MySQL 연결 관리 도구
- `docker-compose.yml`: DB 및 앱 서비스 정의

---

## 🛠️ 개발 팁 (Hot-Reload)
Docker를 통해 실행 중일 때 로컬 코드를 수정하면 실시간으로 반영됩니다. (`volumes` 설정 완료)
수정 후 저장(Ctrl+S)하고 브라우저에서 'Always rerun'을 클릭하세요.