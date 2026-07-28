# kr-emcare — 서울 5대병원 응급실 혼잡도

영문 프로젝트/저장소 이름: `kr-emcare` ("대한민국 응급의료 케어 정보"의 줄임). 지금은 서울 5대병원 응급실만 다루지만, 나중에 전국 확장·당직의료기관(공휴일/야간 진료) 추가를 염두에 두고 이름을 넓게 지었다.

## 한 줄 목표

서울대학교병원·세브란스병원·서울아산병원·삼성서울병원·서울성모병원 5곳의 응급실 실시간 가용병상 정보를 공공데이터 API로 가져와 눈으로 보기 쉬운 표(CSV)와 웹 화면으로 만든다.

## 작업 카드

```text
목표: 서울 5대병원 응급실 혼잡도(여유병상 수)를 실시간으로 확인할 수 있게 만들기
입력: 공공데이터포털 국립중앙의료원 응급의료기관 API 인증키(.env), input/target_hospitals.json
출력: output/er_status_YYYYMMDD_HHMM.csv (5개 병원의 여유병상 현황 스냅샷)
성공 기준: 스크립트 실행 시 5개 병원의 응급실/중환자실 여유병상 수가 콘솔과 CSV에 나온다
오늘 만들 최소 버전: 병원 기관코드(hpid) 자동 조회 + 1회 실행으로 CSV 스냅샷 생성
```

## 데이터 출처

- [국립중앙의료원_전국 응급의료기관 정보 조회 서비스](https://www.data.go.kr/data/15000563/openapi.do) (공공데이터포털)
- 실제 사용 오퍼레이션
  - `getEgytListInfoInqire`: 병원 기관코드(hpid) 조회용
  - `getEmrrmRltmUsefulSckbdInfoInqire`: 응급실 실시간 가용병상정보 조회용
- 심의유형 "자동승인"이라 활용신청 후 바로 인증키를 쓸 수 있다 (개발계정 기준).

## 만들 기능

- [x] 병원 5곳의 기관코드(hpid)를 API로 자동 조회하는 코드 작성 (`src/lookup_hospital_ids.py`)
- [x] 기관코드로 실시간 응급실 가용병상 조회 후 CSV 저장하는 코드 작성 (`src/fetch_er_status.py`)
- [x] 실제 API 키로 두 스크립트 모두 실행해서 정상 동작 확인 (2026-07-27 완료)
- [x] 웹 화면(HTML 대시보드)으로 보여주기 (`src/dashboard.py`, `fetch_er_status.py` 실행할 때마다 같이 생성)
- [x] Datarize 디자인 토큰 기준으로 대시보드 스타일 적용
- [ ] GitHub Actions + GitHub Pages로 10분마다 자동 갱신 (코드는 준비됨, GitHub 쪽 연결 작업 진행 중 — 아래 "자동 배포" 참고)
- [ ] 여러 번 실행한 기록을 누적해서 시간대별 혼잡도 추이 보기 (다음 단계)
- [ ] 전국 응급의료기관으로 확장 (다음 단계, 지금은 서울 5곳만)
- [ ] 공휴일·야간 진료 당직의료기관 정보 추가 (다음 단계)

## 준비물: 공공데이터포털 API 키 발급

1. [data.go.kr](https://www.data.go.kr) 회원가입 후 로그인
2. "국립중앙의료원_전국 응급의료기관 정보 조회 서비스" 검색 (또는 위 링크로 바로 이동)
3. "활용신청" 버튼 클릭 → 활용 목적 등 간단히 작성 → 신청
4. 자동승인이므로 마이페이지 > 데이터 활용 > Open API 이용현황에서 바로 인증키 확인 가능
5. **일반 인증키(Decoding)** 값을 복사

## 실행 방법

```bash
cd "10-projects/kr-emcare"

# 1) 최초 1회: 패키지 설치 (requests가 이미 있다면 생략 가능)
pip install -r requirements.txt

# 2) 최초 1회: .env 파일 만들기
copy .env.example .env
# .env를 열어서 DATA_GO_KR_SERVICE_KEY= 뒤에 발급받은 인증키를 붙여넣기

# 3) 최초 1회: 5개 병원의 기관코드(hpid) 조회
python src/lookup_hospital_ids.py

# 4) 실시간 응급실 현황 조회 + 웹 화면 생성 (이후 원할 때마다 반복 실행)
python src/fetch_er_status.py

# 5) 웹 화면 열기 (매번 실행할 필요 없음, 파일 위치만 기억하면 됨)
start output/dashboard.html
```

## 확인 방법

- `python src/lookup_hospital_ids.py` 실행 후 콘솔에 5개 병원 모두 `[찾음] ... -> hpid=...`가 뜨고, `input/target_hospitals.json`의 `hpid` 값이 채워져 있으면 성공.
- `python src/fetch_er_status.py` 실행 후 콘솔에 5개 병원의 응급실/중환자실 여유병상 수가 표로 뜨고, `output/` 폴더에 `er_status_시각.csv`와 `dashboard.html`이 생기면 성공.
- `output/dashboard.html`을 더블클릭해서 브라우저로 열면, 병원별 카드에 여유병상 수와 상태(🟢 여유 / 🟡 혼잡 / 🟠 포화 / 🔴 초과)가 색과 아이콘+글자로 함께 표시된다. **다시 조회하려면 `fetch_er_status.py`를 다시 실행한 뒤 브라우저에서 새로고침(F5)** 하면 된다 (파일을 덮어쓰는 방식이라 주소는 그대로).
- CSV를 엑셀로 열어서 병원명, 응급실_여유병상, 정보갱신시각 열이 채워져 있는지 확인.

## 자동 배포 (GitHub Actions + GitHub Pages)

로컬에서 매번 실행하지 않아도, GitHub에 올려두면 10분마다 자동으로 데이터를 갱신하고 웹사이트를 다시 배포하도록 구성해뒀다.

```
data/data.json        ← collect.py가 매번 덮어쓰는 최신 스냅샷
docs/index.html       ← build_site.py가 data.json으로 다시 그리는 웹페이지 (GitHub Pages가 이 폴더를 서빙)
.github/workflows/update.yml  ← 10분마다 collect.py → build_site.py → 커밋/푸시를 자동 실행
```

**진행 상태(2026-07-28 기준): 코드는 준비됐고, GitHub 저장소 연결은 진행 중.** 남은 절차:

1. GitHub에 새 **공개(Public)** 저장소 생성 (이름은 `kr-emcare` 그대로)
2. 이 폴더를 그 저장소로 push (`git init` → `git add` → `git commit` → `git remote add origin ...` → `git push`)
3. 저장소 Settings → Secrets and variables → Actions → `DATA_GO_KR_SERVICE_KEY` 등록 (로컬 `.env`에 있는 값과 동일)
4. 저장소 Settings → Pages → Source: `Deploy from a branch` → Branch `main` / `/docs` → Save
5. Actions 탭에서 "자동 업데이트" 워크플로 → Run workflow로 첫 실행 확인
6. `https://[깃허브아이디].github.io/kr-emcare` 에서 실제 배포된 화면 확인

배포된 뒤에는 이 URL만 즐겨찾기 해두면, 직접 스크립트를 실행하지 않아도 10분마다 자동으로 최신 상태가 보인다 (GitHub 사정에 따라 몇 분 정도 지연될 수 있음).

## Codex에게 다음에 요청할 말

- "여러 번 실행한 CSV를 하나로 합쳐서 시간대별 그래프로 보여줘" (추이 확인)
- "병원을 더 추가하고 싶어" (input/target_hospitals.json에 항목만 추가하면 됨)
- "전국 응급실로 확장해줘" (서울 5곳 → 전국, target_hospitals.json 구조를 지역별로 확장)
- "공휴일·야간 당직의료기관도 보여줘" (같은 API 안에 관련 정보가 있는지 먼저 확인 필요)

## 메모

- `lookup_hospital_ids.py`가 병원을 못 찾으면 `input/target_hospitals.json`의 `sigungu`(시군구)나 `name_keywords`를 API가 쓰는 실제 기관명에 맞게 조정해야 할 수 있다.
- 응급실 여유병상 수는 병원이 직접 입력하는 값이라 완전 실시간은 아니고, 병원마다 갱신 주기가 다르다. `정보갱신시각` 열을 함께 봐야 한다.
- 여유병상 수(`응급실_여유병상` 등)는 **음수가 나올 수 있다.** 음수는 "정원 초과"를 뜻한다 (예: -4면 정원보다 4명 더 받고 있다는 의미). 0이나 음수면 매우 혼잡한 상태로 봐야 한다.
- `getEmrrmRltmUsefulSckbdInfoInqire` 오퍼레이션은 병원 하나만 콕 집어 조회하는 기능이 없다. `STAGE1`(시도)·`STAGE2`(시군구)로 그 지역 병원 전체 목록을 받은 뒤, 응답 안에서 `hpid`가 일치하는 병원만 코드로 걸러내는 방식으로 동작한다 (`fetch_er_status.py`의 `fetch_one` 참고).
- `.env` 파일은 워크스페이스 루트 `.gitignore`에서 이미 제외 대상이라 Git에 올라가지 않는다.
