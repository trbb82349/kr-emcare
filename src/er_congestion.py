"""지역 전체 응급실 실시간 가용병상(혼잡도) 데이터를 모은다.

getEmrrmRltmUsefulSckbdInfoInqire는 STAGE1(시도)만 줘도 그 시도 안에서 실시간으로
병상을 보고하는 기관을 전부 돌려준다 (STAGE2 없이도 됨 — 서울은 55곳, 페이지 하나로 충분).
그래서 전국도 시도 17번(광주/전남 통합구역 포함)만 부르면 된다 (전국 합계 약 444곳,
2026-07-29 확인). 전국 응급의료기관 목록(534곳)보다 적은 건, 작은 기관 중 일부는
실시간 병상을 보고하지 않기 때문이다.

er_data.py의 5개 병원 CSV용 로직과는 별개다 — 이쪽은 "지역 전체", 저쪽은 "미리 고른 5곳".
같은 한글 필드 이름(FIELD_LABELS)을 써서, dashboard.py의 classify() 등을 그대로 재사용한다.
"""
from api_client import call_api

OPERATION = "getEmrrmRltmUsefulSckbdInfoInqire"

SIDO_FOR_REGION = {
    "seoul": "서울특별시",
    "busan": "부산광역시",
    "daegu": "대구광역시",
    "incheon": "인천광역시",
    "daejeon": "대전광역시",
    "ulsan": "울산광역시",
    "sejong": "세종특별자치시",
    "gyeonggi": "경기도",
    "gangwon": "강원특별자치도",
    "chungbuk": "충청북도",
    "chungnam": "충청남도",
    "jeonbuk": "전북특별자치도",
    "gyeongbuk": "경상북도",
    "gyeongnam": "경상남도",
    "jeju": "제주특별자치도",
}

# 광주광역시·전라남도는 "전남광주통합특별시"로 행정구역이 통합됐다 (er_directory.py 참고).
MERGED_SIDO = "전남광주통합특별시"
MERGED_REGION_IDS = ["gwangju", "jeonnam"]

FIELD_LABELS = {
    "hvec": "응급실_여유병상",
    "hvgc": "입원실_여유병상",
    "hvicc": "일반중환자실_여유병상",
    "hvoc": "수술실_여유병상",
    "hvidate": "정보갱신시각",
}


def _fetch_for_sido(sido: str) -> list[dict]:
    items = call_api(OPERATION, {"STAGE1": sido, "numOfRows": 300, "pageNo": 1})
    rows = []
    for it in items:
        row = {"병원명": it.get("dutyName", ""), "hpid": it.get("hpid", "")}
        for code, label in FIELD_LABELS.items():
            row[label] = it.get(code, "")
        rows.append(row)
    rows.sort(key=lambda r: r["병원명"])
    return rows


def fetch_region_congestion(region_id: str) -> list[dict]:
    if region_id in MERGED_REGION_IDS:
        return _fetch_for_sido(MERGED_SIDO)
    sido = SIDO_FOR_REGION.get(region_id)
    if not sido:
        return []
    return _fetch_for_sido(sido)


def fetch_all_congestion() -> dict[str, list[dict]]:
    result = {region_id: _fetch_for_sido(sido) for region_id, sido in SIDO_FOR_REGION.items()}
    merged_rows = _fetch_for_sido(MERGED_SIDO)
    for region_id in MERGED_REGION_IDS:
        result[region_id] = merged_rows
    return result
