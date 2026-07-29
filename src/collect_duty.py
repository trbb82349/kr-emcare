"""공휴일 진료 병의원 데이터를 하루 1번 수집해서 data/duty_data.json에 저장한다.

GitHub Actions의 별도 스케줄(.github/workflows/update_duty.yml)에서 실행된다.
응급실 데이터(data/data.json)와는 별도 파일 + 별도 주기로 관리한다 — 진료시간표는
실시간으로 바뀌는 정보가 아니라서 10분마다 갱신할 필요가 없다.

(야간 진료 기능은 지역별로 수만~수십만 건을 다 받아야 해서 규모가 너무 커 제외했다.
공휴일 진료는 QT=8로 서버에서 이미 걸러줘서 전국이 약 8천 건 수준이라 감당 가능하다.)

"의원"으로만 표시되는 곳은 병원 하나하나 API를 따로 불러야 진료과목을 알 수 있어서,
data/dept_cache.json에 hpid -> 진료과목을 계속 누적해서 캐시해두고, 하루에 DAILY_DEPT_CAP개까지만
새로 조회한다 (전체를 하루에 다 채우면 API 호출량이 너무 커짐).
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from duty_data import fetch_holiday_nationwide, fill_departments

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "duty_data.json"
DEPT_CACHE_FILE = ROOT / "data" / "dept_cache.json"
DAILY_DEPT_CAP = 900  # getHsptlBassInfoInqire의 실제 하루 한도가 1000건 안팎으로 보여서 여유 있게 낮춤


def _apply_departments(holiday: dict[str, list[dict]], cache: dict[str, str]) -> None:
    for rows in holiday.values():
        for row in rows:
            if row.get("div") != "의원":
                continue
            dept = cache.get(row.get("hpid", ""))
            if dept:
                row["dept"] = dept


def main():
    now_text = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    print("[collect_duty.py] 공휴일 진료 병의원 수집 중 (전국 17개 시도)...")
    holiday = fetch_holiday_nationwide()
    for region_id, rows in holiday.items():
        print(f"  {region_id}: {len(rows)}곳")

    print("[collect_duty.py] '의원' 진료과목 조회 중 (캐시 활용, 하루 최대 "
          f"{DAILY_DEPT_CAP}건)...")
    cache = json.loads(DEPT_CACHE_FILE.read_text(encoding="utf-8")) if DEPT_CACHE_FILE.exists() else {}

    rows_by_hpid = {}
    for rows in holiday.values():
        for row in rows:
            if row.get("hpid"):
                rows_by_hpid[row["hpid"]] = row

    cache, fetched, remaining, failed = fill_departments(rows_by_hpid, cache, DAILY_DEPT_CAP)
    print(f"  이번에 새로 성공: {fetched}건 / 실패(재시도 예정): {failed}건 / 아직 순번 못 옴: {remaining}건 / 캐시 총 {len(cache)}건")
    DEPT_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    _apply_departments(holiday, cache)

    payload = {
        "meta": {"last_updated": now_text},
        "holiday": holiday,
    }
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[collect_duty.py] 저장 완료: {DATA_FILE}")


if __name__ == "__main__":
    main()
