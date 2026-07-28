"""공휴일·야간 진료 병의원 데이터 수집 로직.

국립중앙의료원_전국 병·의원 찾기 서비스(B552657/HsptlAsembySearchService,
getHsptlMdcncListInfoInqire)를 쓴다.

- 공휴일 진료: QT=8 파라미터로 서버에서 이미 걸러진 목록을 받는다 (전국 약 8천 건 수준,
  10분마다 자동 갱신하기엔 크지만 하루 1번이면 충분히 감당 가능).
- 야간 진료: 이 API에는 "야간" 전용 필터가 없다. 서울만 먼저(전체 약 1만9천 건) 받아서,
  평일(월~토, dutyTime1~6) 중 하나라도 마감시각(dutyTime*c)이 20:00 이후인 곳을 걸러낸다.
  전국으로 넓히면 수십만 건이라 지금은 서울만 지원한다.
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
    "광주광역시": "gwangju",
    "대전광역시": "daejeon",
    "울산광역시": "ulsan",
    "세종특별자치시": "sejong",
    "경기도": "gyeonggi",
    "강원특별자치도": "gangwon",
    "충청북도": "chungbuk",
    "충청남도": "chungnam",
    "전북특별자치도": "jeonbuk",
    "전라남도": "jeonnam",
    "경상북도": "gyeongbuk",
    "경상남도": "gyeongnam",
    "제주특별자치도": "jeju",
}

NIGHT_CLOSE_THRESHOLD = 2000  # 20:00. 이 시각(또는 그 이후)까지 하면 "야간 진료"로 본다.
WEEKDAY_CLOSE_FIELDS = ["dutyTime1c", "dutyTime2c", "dutyTime3c", "dutyTime4c", "dutyTime5c", "dutyTime6c"]

# 목록에서 제외할 기관 구분(dutyDivNam). "기타"로 시작하는 값(기타, 기타(구급차) 등)도 전부 제외한다.
EXCLUDED_DIVS = {"한의원", "한방병원", "요양병원"}


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


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def fetch_holiday_nationwide() -> dict[str, list[dict]]:
    """QT=8(공휴일)로 17개 시도를 전부 조회해서 지역별 목록을 반환한다."""
    result = {region_id: [] for region_id in SIDO_TO_REGION.values()}
    for sido, region_id in SIDO_TO_REGION.items():
        items = _fetch_all({"Q0": sido, "QT": "8"})
        rows = []
        for it in items:
            if _is_excluded(it.get("dutyDivNam", "")):
                continue
            row = _simplify(it)
            row["holiday_open"] = it.get("dutyTime8s", "")
            row["holiday_close"] = it.get("dutyTime8c", "")
            rows.append(row)
        result[region_id] = _dedupe_by_name(rows)
    return result


def fetch_night_seoul() -> list[dict]:
    """서울 전체를 받아서 평일 마감시각이 20시 이후인 곳만 걸러낸다."""
    items = _fetch_all({"Q0": "서울특별시"}, page_size=500)
    rows = []
    for it in items:
        if _is_excluded(it.get("dutyDivNam", "")):
            continue
        close_times = [_to_int(it.get(f)) for f in WEEKDAY_CLOSE_FIELDS]
        close_times = [c for c in close_times if c is not None]
        if not close_times:
            continue
        latest_close = max(close_times)
        if latest_close >= NIGHT_CLOSE_THRESHOLD:
            row = _simplify(it)
            row["latest_close"] = latest_close
            rows.append(row)
    rows.sort(key=lambda r: r["latest_close"], reverse=True)
    return _dedupe_by_name(rows)  # 정렬 후 걸러서, 같은 이름이면 마감이 더 늦은 지점이 남는다


def fetch_department(hpid: str) -> str | None:
    """getHsptlBassInfoInqire로 병원 하나의 진료과목(dgidIdName)을 조회한다."""
    query = {"serviceKey": get_service_key(), "_type": "json", "HPID": hpid}
    try:
        resp = requests.get(DEPT_URL, params=query, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    body = data.get("response", {}).get("body", {})
    items = body.get("items")
    if not items:
        return None
    item = items.get("item", {})
    if isinstance(item, list):
        item = item[0] if item else {}
    return item.get("dgidIdName") or None


def fill_departments(rows_by_hpid: dict[str, dict], cache: dict[str, str], daily_cap: int, sleep_sec: float = 0.05) -> tuple[dict[str, str], int, int]:
    """div가 "의원"인 항목 중 캐시에 없는 hpid를 daily_cap개까지 새로 조회해서 캐시에 채운다.

    반환: (갱신된 캐시, 새로 조회한 개수, 남은 미조회 개수)
    """
    pending = [hpid for hpid, row in rows_by_hpid.items() if row.get("div") == "의원" and hpid not in cache]
    to_fetch = pending[:daily_cap]
    fetched = 0
    for hpid in to_fetch:
        dept = fetch_department(hpid)
        if dept:
            cache[hpid] = dept
        else:
            cache[hpid] = ""  # 조회했지만 과목 정보가 없는 경우도 "확인함"으로 표시해 재조회 방지
        fetched += 1
        time.sleep(sleep_sec)
    remaining = len(pending) - fetched
    return cache, fetched, remaining
