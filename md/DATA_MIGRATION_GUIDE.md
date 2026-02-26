# 데이터 마이그레이션 및 관리 가이드 (CSV to MySQL)

이 가이드는 추출된 CSV 데이터를 MySQL 데이터베이스로 마이그레이션하고 관리하는 방법을 설명합니다. 기존의 `migrate_data.py`가 최신 영어 파일명 패턴을 인식하고 SQLAlchemy를 사용하여 더 빠르고 안전하게 데이터를 처리하도록 업데이트되었습니다.

## 1. 전제 조건
- Python 3.x 가상환경 활성화 (`.venv`)
- Docker Desktop 실행 및 MySQL 컨테이너 가동 (`docker-compose up -d`)
- 프로젝트 루트 폴더에 마이그레이션할 CSV 파일 존재

## 2. 지원되는 CSV 파일 패턴
스크립트는 파일명 뒤에 타임스탬프가 붙은 최신 영어 파일들을 자동으로 찾아 처리합니다:
- `charging_stations_*.csv` -> `charging_stations` 테이블
- `ev_subsidy_status_*.csv` -> `ev_subsidy_status` 테이블
- `faq_data_*.csv` -> `faq_data` 테이블
- `regional_ev_status_*.csv` -> `regional_ev_status` 테이블
- `regional_fuel_status_*.csv` -> `regional_fuel_status` 테이블

## 3. 데이터 마이그레이션 실행
터미널에서 아래 명령어를 실행하면 최신 CSV 데이터를 DB에 반영합니다.

```bash
# Windows
.\.venv\Scripts\python.exe migrate_data.py

# Mac/Linux
source .venv/bin/activate
python migrate_data.py
```

### 마이그레이션 프로세스 요약:
1. **테이블 초기화**: 필요한 테이블이 없는 경우 자동으로 생성합니다.
2. **최신 파일 검색**: 폴더 내에서 각 카테고리별로 가장 최근에 생성된 CSV 파일을 찾습니다.
3. **데이터 초기화 (Truncate)**: 중복 데이터를 방지하기 위해 기존 테이블 데이터를 비웁니다.
4. **고속 적재 (To SQL)**: Pandas와 SQLAlchemy를 사용하여 데이터를 일괄 삽입합니다.

## 4. 문제 해결 (Troubleshooting)
- **ModuleNotFoundError: No module named 'MySQLdb'**: 이 오류는 이제 발생하지 않습니다. 스크립트가 `mysql-connector-python`과 `sqlalchemy`를 사용하도록 수정되었습니다.
- **KeyError: 'XXX'**: CSV 파일의 컬럼명이 DB 구조와 다를 때 발생합니다. 현재 버전은 `to_sql`을 사용하여 CSV의 컬럼명과 DB 테이블의 컬럼명이 일치해야 합니다. (직접 추출한 영어 컬럼명 CSV에 최적화되어 있습니다.)
- **DB 연결 오류**: `docker-compose.yml`에 정의된 DB 정보와 `utils/db_manager.py`의 설정이 일치하는지 확인하세요.

## 5. 데이터 확인
마이그레이션 완료 후 Streamlit 앱을 실행하여 대시보드에 데이터가 정상적으로 표시되는지 확인합니다:
```bash
streamlit run app.py
```
