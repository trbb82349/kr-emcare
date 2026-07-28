"""공휴일·야간 진료 병의원 데이터를 하루 1번 수집해서 data/duty_data.json에 저장한다.

GitHub Actions의 별도 스케줄(.github/workflows/update_duty.yml)에서 실행된다.
응급실 데이터(data/data.json)와는 별도 파일 + 별도 주기로 관리한다 — 진료시간표는
실시간으로 바뀌는 정보가 아니라서 10분마다 갱신할 필요가 없다.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from duty_data import fetch_holiday_nationwide, fetch_night_seoul

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "duty_data.json"


def main():
    now_text = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

    print("[collect_duty.py] 공휴일 진료 병의원 수집 중 (전국 17개 시도)...")
    holiday = fetch_holiday_nationwide()
    for region_id, rows in holiday.items():
        print(f"  {region_id}: {len(rows)}곳")

    print("[collect_duty.py] 야간 진료 병의원 수집 중 (서울)...")
    night_seoul = fetch_night_seoul()
    print(f"  서울 야간(마감 20시 이후): {len(night_seoul)}곳")

    payload = {
        "meta": {"last_updated": now_text, "night_scope": ["seoul"]},
        "holiday": holiday,
        "night": {"seoul": night_seoul},
    }
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[collect_duty.py] 저장 완료: {DATA_FILE}")


if __name__ == "__main__":
    main()
