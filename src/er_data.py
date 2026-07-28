"""5개 병원의 실시간 응급실 가용병상 데이터를 조회하는 공통 로직.

로컬용 fetch_er_status.py(CSV+HTML)와 CI용 collect.py(data/data.json)가 같이 쓴다.
"""
import json

from api_client import call_api
from common import INPUT_DIR

TARGET_FILE = INPUT_DIR / "target_hospitals.json"
OPERATION = "getEmrrmRltmUsefulSckbdInfoInqire"

# API 응답 필드 코드 -> 화면에 보여줄 한글 이름
# (data.go.kr 공식 응답메시지 명세 기준: hvec=응급실, hvgc=입원실, hvicc=일반중환자, hvoc=수술실)
FIELD_LABELS = {
    "hvec": "응급실_여유병상",
    "hvgc": "입원실_여유병상",
    "hvicc": "일반중환자실_여유병상",
    "hvoc": "수술실_여유병상",
    "hvidate": "정보갱신시각",
}


def load_target_hospitals() -> list[dict]:
    data = json.loads(TARGET_FILE.read_text(encoding="utf-8"))
    hospitals = data["hospitals"]
    missing = [h["name"] for h in hospitals if not h.get("hpid")]
    if missing:
        raise SystemExit(
            "다음 병원의 hpid가 아직 없습니다: " + ", ".join(missing) +
            "\n먼저 `python src/lookup_hospital_ids.py`를 실행하세요."
        )
    return hospitals


def fetch_one(sido: str, sigungu: str, hpid: str) -> dict:
    # 이 오퍼레이션은 HPID로 직접 조회하는 기능이 없고, 지역(시도/시군구) 목록을
    # 받아온 뒤 hpid가 일치하는 병원을 걸러내는 방식으로만 조회할 수 있다.
    items = call_api(OPERATION, {"STAGE1": sido, "STAGE2": sigungu, "numOfRows": 100})
    for item in items:
        if item.get("hpid") == hpid:
            return item
    return {}


def collect_rows(hospitals: list[dict], queried_at_text: str) -> list[dict]:
    rows = []
    for hospital in hospitals:
        info = fetch_one(hospital["sido"], hospital["sigungu"], hospital["hpid"])
        if not info:
            print(f"[경고] {hospital['name']}: 실시간 병상 정보를 찾지 못했습니다 (hpid={hospital['hpid']}).")
        row = {
            "조회시각": queried_at_text,
            "병원명": hospital["name"],
            "hpid": hospital["hpid"],
        }
        for code, label in FIELD_LABELS.items():
            row[label] = info.get(code, "")
        rows.append(row)
    return rows
