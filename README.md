# kr-emcare — 서울 5대병원 응급실 혼잡도

영문 프로젝트/저장소 이름: `kr-emcare` ("대한민국 응급의료 케어 정보"의 줄임). 서울 5대병원 실시간 혼잡도 외에 전국 응급의료기관 목록·공휴일 진료 병의원 조회까지 다루는 걸 염두에 두고 이름을 넓게 지었다.

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
- [x] GitHub Actions + GitHub Pages로 10분마다 자동 갱신 · 배포 완료 (https://trbb82349.github.io/kr-emcare/)
- [x] `emcare` 로고 헤더 + "응급실 혼잡도 현황"/"공휴일 진료 병원" 탭 UI (야간 진료는 데이터 규모 문제로 제외 — 아래 메모 참고)
- [x] 지역 선택 지도(실제 시도 경계선 SVG) + "서울 5대병원" 바로가기
  - 지도 출처: [southkorea/southkorea-maps](https://github.com/southkorea/southkorea-maps) (`popong/skorea-provinces-v3.1.svg`). 이 저장소는 별도 라이선스 명시가 없어 개인 비상업 프로젝트로 출처를 표기하고 사용 (`src/korea_map.py` 상단 주석 참고). 세종특별자치시는 이 지도 데이터에 없어 별도 점으로 표시.
- [x] 전국 응급의료기관 목록 (혼잡도 제외, 병원명·등급·주소·전화만) — 서울 5대병원 외 16개 지역도 실제 데이터 (`src/er_directory.py`, `getEgytListInfoInqire`)
- [x] 공휴일(QT=8) 진료 병의원 전국 조회 + "의원"으로만 표시되던 곳의 진료과목 표시 (`src/duty_data.py`, `src/collect_duty.py`)
- [x] 서울 전체(55곳) 실시간 응급실 혼잡도 — `STAGE1=서울특별시`만으로 한 번에 조회됨 (`src/er_congestion.py`). 목록은 접이식(기본: 상태·응급실 병상만, 누르면 입원실·중환자실·수술실·갱신시각 펼침)
- [ ] 서울 외 지역도 실시간 혼잡도로 확장 (지금은 서울만, 나머지는 병원 목록만)
- [ ] 여러 번 실행한 기록을 누적해서 시간대별 혼잡도 추이 보기 (다음 단계)

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

**배포 완료(2026-07-28).** 실제 사이트: **https://trbb82349.github.io/kr-emcare/**

이 URL만 즐겨찾기 해두면, 직접 스크립트를 실행하지 않아도 10분마다 자동으로 최신 상태가 보인다 (GitHub 사정에 따라 몇 분 정도 지연될 수 있음).

`src/dashboard.py`(화면 디자인)를 수정했으면, `python src/collect.py && python src/build_site.py`로 로컬에서 먼저 확인한 뒤 `git add -A && git commit -m "..." && git push`로 반영한다. push 시점에 GitHub Actions의 자동 커밋과 겹치면 `git pull --no-rebase`로 병합하고, `data/data.json`·`docs/index.html` 충돌은 손으로 합치지 말고 `collect.py`/`build_site.py`를 다시 실행해 새로 만든 뒤 커밋한다 (둘 다 자동 생성 파일이라 직접 병합할 필요가 없다).

## 진행 중인 API (활성화 대기)

| API | 용도 | 상태 |
|---|---|---|
| [건강보험심사평가원_병원정보서비스](https://www.data.go.kr/data/15001698/openapi.do) | 종별코드(`clCd`: 01=상급종합병원, 11=종합병원)로 병원 등급 확인 | 승인됨, 호출 시 계속 `500 Unexpected errors` |
| [국립중앙의료원_전국 병·의원 찾기 서비스](https://www.data.go.kr/data/15000736/openapi.do) | 공휴일(`QT=8`) 진료 병의원, 진료과목 조회 | ✅ 활성화됨, 정상 사용 중 |

HIRA 병원정보서비스는 여전히 `500` 에러라 상급종합/종합병원 집계는 아직 못 만들었다. `.env`의 키를 그대로 재사용하면 되고, 엔드포인트는 `https://apis.data.go.kr/B551182/hospInfoService/getHospBasisList`.

### data.go.kr 개발계정 트래픽 한도 (직접 겪은 것)

- 개발계정 하루 한도는 오퍼레이션 단위로 걸리는 것으로 보인다 — `getHsptlBassInfoInqire`(진료과목 개별조회)를 하루에 만 건 넘게 불렀더니 그 오퍼레이션만 `429 API token quota exceeded`가 났고, 같은 서비스의 목록 조회(`getHsptlMdcncListInfoInqire`)나 응급실 API(`ErmctInfoInqireService`)는 전혀 영향 없었다.
- 한도는 자정 기준으로 초기화되지만 "정확히 0시"가 아니라 시스템 처리 순서대로 순차 반영된다 (data.go.kr 공식 안내).
- `src/collect_duty.py`의 `DAILY_DEPT_CAP`(기본 2000)이 이 한도를 넘지 않게 하는 안전장치다. 급하게 다 채우고 싶어도 임시로 크게 올리지 말 것 — 실패만 쌓인다.

### 광주·전남 행정구역 통합

`Q0=광주광역시` / `Q0=전라남도`로 조회하면 0건이 나온다 — 두 지역이 **"전남광주통합특별시"**로 행정구역이 통합됐기 때문이다(직접 확인함). `er_directory.py`·`duty_data.py`의 `MERGED_SIDO`/`MERGED_REGION_IDS`가 이걸 처리해서, 통합 지역 데이터를 지도 위 광주·전남 두 자리에 똑같이 넣어준다 (지도 SVG 자체는 아직 두 지역이 분리된 옛날 데이터라 모양은 그대로 둠). 다른 시도 이름도 언젠가 바뀔 수 있으니, 지역이 갑자기 0건으로 나오면 이 케이스부터 의심해볼 것.

## Codex에게 다음에 요청할 말

- "여러 번 실행한 CSV를 하나로 합쳐서 시간대별 그래프로 보여줘" (추이 확인)
- "병원을 더 추가하고 싶어" (input/target_hospitals.json에 항목만 추가하면 됨)
- "HIRA API 다시 시도해줘" (활성화됐는지 재확인)
- "다른 지역(부산 등)도 실시간 혼잡도로 채워줘" (지금은 목록만 있는 지역을 서울처럼 실시간 병상 조회로 연결)

## 메모

- `lookup_hospital_ids.py`가 병원을 못 찾으면 `input/target_hospitals.json`의 `sigungu`(시군구)나 `name_keywords`를 API가 쓰는 실제 기관명에 맞게 조정해야 할 수 있다.
- 응급실 여유병상 수는 병원이 직접 입력하는 값이라 완전 실시간은 아니고, 병원마다 갱신 주기가 다르다. `정보갱신시각` 열을 함께 봐야 한다.
- 여유병상 수(`응급실_여유병상` 등)는 **음수가 나올 수 있다.** 음수는 "정원 초과"를 뜻한다 (예: -4면 정원보다 4명 더 받고 있다는 의미). 0이나 음수면 매우 혼잡한 상태로 봐야 한다.
- `getEmrrmRltmUsefulSckbdInfoInqire` 오퍼레이션은 병원 하나만 콕 집어 조회하는 기능이 없다. `STAGE1`(시도)·`STAGE2`(시군구)로 그 지역 병원 전체 목록을 받은 뒤, 응답 안에서 `hpid`가 일치하는 병원만 코드로 걸러내는 방식으로 동작한다 (`fetch_er_status.py`의 `fetch_one` 참고).
- `.env` 파일은 워크스페이스 루트 `.gitignore`에서 이미 제외 대상이라 Git에 올라가지 않는다.
