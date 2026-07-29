"""공휴일 진료 병의원 데이터 수집 로직.

국립중앙의료원_전국 병·의원 찾기 서비스(B552657/HsptlAsembySearchService,
getHsptlMdcncListInfoInqire)를 쓴다.

공휴일 진료는 QT=8 파라미터로 서버에서 이미 걸러진 목록을 받는다 (전국 약 8천 건 수준,
10분마다 자동 갱신하기엔 크지만 하루 1번이면 충분히 감당 가능).

(야간 진료는 이 API에 전용 필터가 없어 지역 전체를 다 받아야 하는데, 서울만 해도
약 1만9천 건, 전국이면 수십만 건이라 규모상 제외했다.)
"""
import time

import requests

from common import get_service_key

BASE_URL = "https://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlMdcncListInfoInqire"
DEPT_URL = "https://apis.data.go.kr/B552657/HsptlAsembySearchService/getHsptlBassInfoInqire"

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

# 광주광역시·전라남도는 "전남광주통합특별시"로 행정구역이 통합됐다 (구 명칭으로 조회하면 0건).
# 지도에는 아직 광주/전남이 따로 그려져 있어서, 같은 통합 데이터를 두 지역 모두에 넣는다.
MERGED_SIDO = "전남광주통합특별시"
MERGED_REGION_IDS = ["gwangju", "jeonnam"]

# 목록에서 제외할 기관 구분(dutyDivNam). "기타"로 시작하는 값(기타, 기타(구급차) 등)도 전부 제외한다.
EXCLUDED_DIVS = {"한의원", "한방병원", "요양병원", "조산원"}


def _is_excluded(div: str) -> bool:
    return div in EXCLUDED_DIVS or div.startswith("기타")


def _dedupe_by_name(rows: list[dict]) -> list[dict]:
    """같은 이름(다른 지점/전화번호로 여러 번 등록된 곳)은 처음 나온 것 하나만 남긴다."""
    seen = set()
    out = []
    for row in rows:
        name = row.get("name", "")
        if name in seen:
            continue
        seen.add(name)
        out.append(row)
    return out


def _fetch_page(params: dict) -> tuple[list[dict], int]:
    query = {"serviceKey": get_service_key(), "_type": "json"}
    query.update(params)
    resp = requests.get(BASE_URL, params=query, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") not in ("00", None):
        raise SystemExit(f"API 오류({header.get('resultCode')}): {header.get('resultMsg')}")
    body = data.get("response", {}).get("body", {})
    total = body.get("totalCount", 0)
    items = body.get("items")
    if not items:
        return [], total
    item = items.get("item", [])
    if isinstance(item, dict):
        item = [item]
    return item, total


def _fetch_all(params: dict, page_size: int = 200, sleep_sec: float = 0.05) -> list[dict]:
    all_items = []
    page = 1
    while True:
        items, total = _fetch_page({**params, "numOfRows": page_size, "pageNo": page})
        all_items.extend(items)
        if len(all_items) >= total or not items:
            break
        page += 1
        time.sleep(sleep_sec)
    return all_items


def _simplify(item: dict) -> dict:
    return {
        "name": item.get("dutyName", ""),
        "addr": item.get("dutyAddr", ""),
        "tel": item.get("dutyTel1", ""),
        "div": item.get("dutyDivNam", ""),
        "hpid": item.get("hpid", ""),
    }


def _fetch_holiday_for_sido(sido: str) -> list[dict]:
    items = _fetch_all({"Q0": sido, "QT": "8"})
    rows = []
    for it in items:
        if _is_excluded(it.get("dutyDivNam", "")):
            continue
        row = _simplify(it)
        row["holiday_open"] = it.get("dutyTime8s", "")
        row["holiday_close"] = it.get("dutyTime8c", "")
        rows.append(row)
    return _dedupe_by_name(rows)


def fetch_holiday_nationwide() -> dict[str, list[dict]]:
    """QT=8(공휴일)로 17개 시도를 전부 조회해서 지역별 목록을 반환한다."""
    result = {}
    for sido, region_id in SIDO_TO_REGION.items():
        result[region_id] = _fetch_holiday_for_sido(sido)

    merged_rows = _fetch_holiday_for_sido(MERGED_SIDO)
    for region_id in MERGED_REGION_IDS:
        result[region_id] = merged_rows

    return result


class DeptLookupFailed(Exception):
    """조회 자체가 실패한 경우 (서버 오류·타임아웃·빈 응답 등). "과목 없음"과는 구분해서 나중에 재시도한다."""


def fetch_department(hpid: str) -> str:
    """getHsptlBassInfoInqire로 병원 하나의 진료과목(dgidIdName)을 조회한다.

    반환값은 실제 과목명, 또는 정말로 등록된 과목이 없으면 빈 문자열("").
    조회 자체가 실패하면(타임아웃, 서버 오류, 빈 응답 등) DeptLookupFailed를 던진다 —
    이 경우 캐시에 쓰지 않고 다음 실행에서 다시 시도한다.
    """
    query = {"serviceKey": get_service_key(), "_type": "json", "HPID": hpid}
    try:
        resp = requests.get(DEPT_URL, params=query, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise DeptLookupFailed(str(e)) from e
    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") not in ("00", None):
        raise DeptLookupFailed(header.get("resultMsg"))
    body = data.get("response", {}).get("body", {})
    items = body.get("items")
    if not items:
        # 방금 목록 API에서 받아온 유효한 hpid인데 기본정보가 비어 있으면, 대부분 서버 과부하로
        # 인한 일시적 빈 응답이다. "과목 없음"으로 단정하지 않고 재시도 대상으로 남긴다.
        raise DeptLookupFailed("empty items")
    item = items.get("item", {})
    if isinstance(item, list):
        item = item[0] if item else {}
    if not item:
        raise DeptLookupFailed("empty item")
    return item.get("dgidIdName") or ""


def fill_departments(rows_by_hpid: dict[str, dict], cache: dict[str, str], daily_cap: int, sleep_sec: float = 0.08) -> tuple[dict[str, str], int, int, int]:
    """div가 "의원"인 항목 중 캐시에 없는 hpid를 daily_cap개까지 새로 조회해서 캐시에 채운다.

    반환: (갱신된 캐시, 새로 성공한 개수, 남은 미조회 개수, 실패해서 다음에 재시도할 개수)
    """
    pending = [hpid for hpid, row in rows_by_hpid.items() if row.get("div") == "의원" and hpid not in cache]
    to_fetch = pending[:daily_cap]
    fetched = 0
    failed = 0
    for hpid in to_fetch:
        try:
            cache[hpid] = fetch_department(hpid)
            fetched += 1
        except DeptLookupFailed:
            failed += 1  # 캐시에 안 남기고 다음 실행에서 재시도
        time.sleep(sleep_sec)
    remaining = len(pending) - fetched - failed
    return cache, fetched, remaining, failed
