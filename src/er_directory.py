"""전국 응급의료기관 "목록"(혼잡도 없이 병원명·주소·등급만)을 지역별로 모은다.

국립중앙의료원_전국 응급의료기관 정보 조회 서비스(getEgytListInfoInqire)를 시도(Q0)별로
17번 호출한다. 전국 534곳 수준이라 가볍다 (실시간 가용병상 조회처럼 병원마다 따로
불러야 하는 무거운 작업이 아니다).
"""
from api_client import call_api

OPERATION = "getEgytListInfoInqire"

SIDO_TO_REGION = {
    "서울특별시": "seoul",
    "부산광역시": "busan",
    "대구광역시": "daegu",
    "인천광역시": "incheon",
    "대전광역시": "daejeon",
    "울산광역시": "ulsan",
    "세종특별자치시": "sejong",
    "경기도": "gyeonggi",
    "강원특별자치도": "gangwon",
    "충청북도": "chungbuk",
    "충청남도": "chungnam",
    "전북특별자치도": "jeonbuk",
    "경상북도": "gyeongbuk",
    "경상남도": "gyeongnam",
    "제주특별자치도": "jeju",
}

# 광주광역시·전라남도는 "전남광주통합특별시"로 행정구역이 통합됐다 (구 명칭으로 조회하면 0건 반환됨,
# 실제로 확인함). 지도에는 아직 광주/전남이 따로 그려져 있어서, 같은 통합 데이터를 두 지역 모두에 넣는다.
MERGED_SIDO = "전남광주통합특별시"
MERGED_REGION_IDS = ["gwangju", "jeonnam"]


def _simplify(item: dict) -> dict:
    return {
        "name": item.get("dutyName", ""),
        "addr": item.get("dutyAddr", ""),
        "tel": item.get("dutyTel1", ""),
        "level": item.get("dutyEmclsName", ""),
        "hpid": item.get("hpid", ""),
    }


def fetch_nationwide_directory() -> dict[str, list[dict]]:
    """시도별 응급의료기관 목록(이름/주소/전화/등급)을 반환한다."""
    result = {}
    for sido, region_id in SIDO_TO_REGION.items():
        items = call_api(OPERATION, {"Q0": sido, "numOfRows": 300, "pageNo": 1})
        rows = [_simplify(it) for it in items]
        rows.sort(key=lambda r: r["name"])
        result[region_id] = rows

    merged_items = call_api(OPERATION, {"Q0": MERGED_SIDO, "numOfRows": 300, "pageNo": 1})
    merged_rows = sorted((_simplify(it) for it in merged_items), key=lambda r: r["name"])
    for region_id in MERGED_REGION_IDS:
        result[region_id] = merged_rows

    return result
