"""지역 전체 응급실 실시간 가용병상(혼잡도) 데이터를 모은다.

getEmrrmRltmUsefulSckbdInfoInqire는 STAGE1(시도)만 줘도 그 시도 안에서 실시간으로
병상을 보고하는 기관을 전부 돌려준다 (STAGE2 없이도 됨 — 서울은 55곳, 페이지 하나로 충분).
전국 응급의료기관 목록(534곳)보다 적은 건, 작은 기관 중 일부는 실시간 병상을 보고하지
않기 때문이다.

er_data.py의 5개 병원 CSV용 로직과는 별개다 — 이쪽은 "지역 전체", 저쪽은 "미리 고른 5곳".
같은 한글 필드 이름(FIELD_LABELS)을 써서, dashboard.py의 classify() 등을 그대로 재사용한다.
"""
from api_client import call_api

OPERATION = "getEmrrmRltmUsefulSckbdInfoInqire"

# 지금은 서울만 지원. 나중에 다른 지역을 추가하면 여기에 늘어난다.
SIDO_FOR_REGION = {
    "seoul": "서울특별시",
}

FIELD_LABELS = {
    "hvec": "응급실_여유병상",
    "hvgc": "입원실_여유병상",
    "hvicc": "일반중환자실_여유병상",
    "hvoc": "수술실_여유병상",
    "hvidate": "정보갱신시각",
}


def fetch_region_congestion(region_id: str) -> list[dict]:
    sido = SIDO_FOR_REGION.get(region_id)
    if not sido:
        return []
    items = call_api(OPERATION, {"STAGE1": sido, "numOfRows": 300, "pageNo": 1})
    rows = []
    for it in items:
        row = {"병원명": it.get("dutyName", ""), "hpid": it.get("hpid", "")}
        for code, label in FIELD_LABELS.items():
            row[label] = it.get(code, "")
        rows.append(row)
    rows.sort(key=lambda r: r["병원명"])
    return rows


def fetch_all_congestion() -> dict[str, list[dict]]:
    return {region_id: fetch_region_congestion(region_id) for region_id in SIDO_FOR_REGION}
