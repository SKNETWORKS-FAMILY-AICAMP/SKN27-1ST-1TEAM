# Docker 및 DB 연결 가이드

## 1. Docker 컨테이너 실행하기
터미널(PowerShell 또는 Bash)에서 아래 명령어를 실행하여 컨테이너를 빌드하고 백그라운드에서 실행합니다.

```bash
docker-compose up -d --build
```

## 2. 실행 상태 확인
컨테이너가 정상적으로 실행 중인지 확인합니다.

```bash
docker ps
```
`mobility-mysql`과 `mobility-streamlit` 컨테이너가 `Up` 상태여야 합니다.

## 3. DBeaver에서 DB 연결하기 (MySQL)
DBeaver와 같은 DB 관리 도구에서 아래 정보를 입력하여 연결합니다.

- **Host**: `localhost`
- **Port**: `3306`
- **Database**: `mobility_db`
- **Username**: `user`
- **Password**: `password`

## 4. 코드 변경사항 실시간 반영 (Hot Reload)
`docker-compose.yml`에 볼륨 설정이 추가되어, 로컬에서 코드를 수정하면 컨테이너를 재시작할 필요 없이 즉시 반영됩니다.

## 5. Streamlit 접속
브라우저에서 아래 주소로 접속하면 실행된 앱을 볼 수 있습니다.
- `http://localhost:8501`
