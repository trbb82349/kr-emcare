"""2단계: 5개 병원의 실시간 응급실 가용병상 정보를 가져와 CSV로 저장하고 화면에 출력한다.

실행:
    python src/fetch_er_status.py

사전 준비:
    1. .env에 DATA_GO_KR_SERVICE_KEY가 설정되어 있어야 한다.
    2. 먼저 lookup_hospital_ids.py를 실행해서 input/target_hospitals.json의
       hpid 값이 모두 채워져 있어야 한다.
"""
import csv
from datetime import datetime

from common import OUTPUT_DIR
from dashboard import write_dashboard
from er_data import collect_rows, load_target_hospitals


def main():
    hospitals = load_target_hospitals()

    now = datetime.now()
    rows = collect_rows(hospitals, now.strftime("%Y-%m-%d %H:%M"))

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"er_status_{now.strftime('%Y%m%d_%H%M')}.csv"
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dashboard_path = OUTPUT_DIR / "dashboard.html"
    write_dashboard(rows, now.strftime("%Y-%m-%d %H:%M"), dashboard_path)

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
