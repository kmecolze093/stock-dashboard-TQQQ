# 아기티큐 투자 웹 대시보드

Scriptable 위젯을 PC·모바일에서 볼 수 있는 정적 웹 대시보드로 변환한 프로젝트입니다.

## 구조
- `index.html`, `styles.css`, `app.js`: 반응형 웹 화면
- `scripts/update_data.py`: QQQ, TQQQ, CNN FGI 데이터를 받아 계산
- `data/latest.json`: 웹에서 읽는 최종 데이터
- `.github/workflows/update-data.yml`: 미국 장 마감 후 평일 하루 1회 자동 갱신

## GitHub에서 실행
1. 새 GitHub 저장소를 만듭니다.
2. 이 폴더 안의 파일과 숨김 폴더 `.github`를 모두 업로드합니다.
3. 저장소의 `Actions` 탭에서 `Update market dashboard`를 선택하고 `Run workflow`를 한 번 실행합니다.
4. 저장소 `Settings > Pages`로 이동합니다.
5. `Build and deployment > Source`를 `Deploy from a branch`로 선택합니다.
6. Branch를 `main`, 폴더를 `/(root)`로 정한 뒤 저장합니다.
7. 잠시 후 표시되는 Pages 주소로 접속합니다.

## 자동 갱신 시간
워크플로는 평일 `22:30 UTC`에 실행됩니다. 한국시간으로는 다음 날 오전 7시 30분입니다. 미국 동부시간의 서머타임과 표준시간 모두 주식시장 마감 이후가 되도록 여유를 둔 시간입니다.

## 수동 갱신
GitHub 저장소의 `Actions > Update market dashboard > Run workflow`를 누르면 즉시 갱신할 수 있습니다.

## 로컬 확인
Python이 설치된 PC에서:
```bash
pip install -r requirements.txt
python scripts/update_data.py
python -m http.server 8000
```
브라우저에서 `http://localhost:8000`을 엽니다.

Dashboard deployment reset.
