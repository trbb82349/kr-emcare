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
        result[region_id] = rows
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
    return rows
