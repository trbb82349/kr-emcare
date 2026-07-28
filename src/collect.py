"""GitHub Actions가 스케줄에 맞춰 실행하는 데이터 수집 스크립트.

data/data.json을 최신 조회 결과로 덮어쓴다 (누적하지 않고 매번 스냅샷 교체).
로컬 fetch_er_status.py와 같은 조회 로직(er_data.py)을 공유한다.

필요한 환경변수: DATA_GO_KR_SERVICE_KEY (GitHub Secrets에서 주입됨)
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from er_data import collect_rows, load_target_hospitals

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "data.json"


def main():
    hospitals = load_target_hospitals()
    now = datetime.now(KST)
    now_text = now.strftime("%Y-%m-%d %H:%M")

    rows = collect_rows(hospitals, now_text)

    DATA_FILE.parent.mkdir(exist_ok=True)
    payload = {"meta": {"last_updated": now_text}, "hospitals": rows}
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[collect.py] {len(rows)}개 병원 데이터를 저장했습니다: {DATA_FILE}")


if __name__ == "__main__":
    main()
