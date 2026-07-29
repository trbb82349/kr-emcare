"""2단계: 5개 병원의 실시간 응급실 가용병상 정보를 가져와 CSV로 저장하고 화면에 출력한다.

실행:
    python src/fetch_er_status.py

사전 준비:
    1. .env에 DATA_GO_KR_SERVICE_KEY가 설정되어 있어야 한다.
    2. 먼저 lookup_hospital_ids.py를 실행해서 input/target_hospitals.json의
       hpid 값이 모두 채워져 있어야 한다.
"""
import csv
import json
from datetime import datetime

from common import OUTPUT_DIR, PROJECT_ROOT
from dashboard import write_dashboard
from er_data import collect_rows, load_target_hospitals

DUTY_DATA_FILE = PROJECT_ROOT / "data" / "duty_data.json"
DATA_FILE = PROJECT_ROOT / "data" / "data.json"


def _load_json(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def main():
    hospitals = load_target_hospitals()

    now = datetime.now()
    rows = collect_rows(hospitals, now.strftime("%Y-%m-%d %H:%M"))
    duty_data = _load_json(DUTY_DATA_FILE)
    # 전국 병원 목록(directory)·지역별 혼잡도(congestion)는 매번 새로 안 받고, data.json에
    # 이미 있으면 그걸 재사용한다 (collect.py가 GitHub Actions에서 이미 채워둔 값 —
    # 로컬 확인용으로는 그걸로 충분하고, 매번 새로 받으면 이 빠른 로컬 체크가 느려진다).
    existing_data = _load_json(DATA_FILE)
    directory = existing_data.get("directory") if existing_data else None
    congestion = existing_data.get("congestion") if existing_data else None

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"er_status_{now.strftime('%Y%m%d_%H%M')}.csv"
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dashboard_path = OUTPUT_DIR / "dashboard.html"
    write_dashboard(
        rows, now.strftime("%Y-%m-%d %H:%M"), dashboard_path,
        duty_data=duty_data, directory=directory, congestion=congestion,
    )

    print(f"{len(rows)}개 병원 정보를 저장했습니다: {out_path}")
    print(f"웹 화면도 새로 만들었습니다: {dashboard_path} (브라우저로 열어서 확인)\n")
    header = f"{'병원명':<12}{'응급실 여유병상':<16}{'중환자실 여유병상':<18}{'정보갱신시각'}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['병원명']:<12}"
            f"{str(row['응급실_여유병상']):<16}"
            f"{str(row['일반중환자실_여유병상']):<18}"
            f"{row['정보갱신시각']}"
        )


if __name__ == "__main__":
    main()
