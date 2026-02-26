# 전국 친환경차 현황 대시보드 셋업 가이드

이 프로젝트는 Streamlit 기반의 대시보드와 MySQL 데이터베이스(Docker)로 구성되어 있습니다. 처음 저장소를 클론(Clone) 받은 후, 로컬 환경에서 데이터베이스를 세팅하고 앱을 실행하는 전체 과정을 안내합니다.

## 1. 프로젝트 클론 및 폴더 이동

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN27-1ST-1TEAM.git
cd SKN27-1ST-1TEAM
```

## 2. 파이썬 가상환경 설정 및 패키지 설치

가상환경을 생성하고, 프로젝트에 필요한 파이썬 라이브러리들을 설치합니다.

### Windows
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Mac/Linux
```bash
uv venv .venv --python 3.13 
.\.venv\Scripts\activate
uv pip install -r .\requirements.txt
```

## 3. Docker 버전을 이용한 MySQL DB 실행

이 프로젝트는 로컬 DB 환경을 쉽게 구축하기 위해 `docker-compose`를 사용합니다. (Docker Desktop이 실행 중이어야 합니다.)

```bash
# 백그라운드 모드로 컨테이너 실행
docker-compose up -d
```
> **참고:** 최초 실행 시 DB 이미지를 다운로드하고 초기화하는 데 약간의 시간이 소요될 수 있습니다.

## 4. 데이터베이스 마이그레이션 (DB 세팅)

앱은 DB에서 데이터를 읽어오도록 설계되어 있습니다. 프로젝트 내에 포함된 CSV 파일들의 데이터를 MySQL 데이터베이스로 밀어넣는 작업을 수행해야 합니다.

가상환경이 활성화된 터미널에서 아래 스크립트를 실행합니다:

```bash
python migrate_data.py
```
> 실행이 완료되면 `All database migrations completed successfully!` 메시지가 출력됩니다.

## 5. 최신 인프라(충전소 등) 데이터 동기화 (선택 사항)

API를 통해 실시간/최신 인프라 데이터를 불러와 DB에 적재하려면 아래 스크립트를 실행합니다.

```bash
python scripts/sync_infra.py
```

## 6. Streamlit 대시보드 실행

모든 데이터 세팅이 완료되었습니다! 이제 앱을 실행하여 대시보드를 확인합니다.

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 대시보드를 확인할 수 있습니다.
