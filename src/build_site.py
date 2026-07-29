"""data/data.json -> docs/index.html 변환. GitHub Pages가 docs/를 서빙한다.

dashboard.py의 build_dashboard_html()을 그대로 재사용해서, 로컬에서 보는
output/dashboard.html과 배포되는 docs/index.html이 항상 같은 디자인을 쓴다.
"""
import json
from pathlib import Path

from dashboard import build_dashboard_html

ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "data.json"
DUTY_DATA_FILE = ROOT / "data" / "duty_data.json"
OUT_FILE = ROOT / "docs" / "index.html"


def build():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    rows = data["hospitals"]
    generated_at_text = data["meta"]["last_updated"]

    duty_data = json.loads(DUTY_DATA_FILE.read_text(encoding="utf-8")) if DUTY_DATA_FILE.exists() else None
    directory = data.get("directory")
    congestion = data.get("congestion")

    html = build_dashboard_html(
        rows, generated_at_text, duty_data=duty_data, directory=directory, congestion=congestion,
    )

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"[build_site.py] 저장 완료: {OUT_FILE}")


if __name__ == "__main__":
    build()
