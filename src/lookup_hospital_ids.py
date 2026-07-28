"""1단계: input/target_hospitals.json에 적힌 5개 병원의 기관코드(hpid)를 찾아서 채워 넣는다.

실행:
    python src/lookup_hospital_ids.py

사전 준비:
    프로젝트 폴더에 .env 파일을 만들고 아래 한 줄을 넣어야 한다.
    DATA_GO_KR_SERVICE_KEY=공공데이터포털에서 발급받은 인증키(Decoding)
"""
import json

from api_client import call_api
from common import INPUT_DIR

TARGET_FILE = INPUT_DIR / "target_hospitals.json"
OPERATION = "getEgytListInfoInqire"


def find_hpid(sido: str, sigungu: str, keywords: list[str]) -> tuple[str, str] | None:
    items = call_api(OPERATION, {"Q0": sido, "Q1": sigungu, "numOfRows": 100, "pageNo": 1})
    for item in items:
        duty_name = item.get("dutyName", "")
        if any(keyword in duty_name for keyword in keywords):
            return item.get("hpid"), duty_name
    return None


def main():
    data = json.loads(TARGET_FILE.read_text(encoding="utf-8"))

    for hospital in data["hospitals"]:
        result = find_hpid(hospital["sido"], hospital["sigungu"], hospital["name_keywords"])
        if result is None:
            print(f"[못 찾음] {hospital['name']} — {hospital['sido']} {hospital['sigungu']}에서 이름이 일치하는 기관이 없습니다. "
                  f"target_hospitals.json의 name_keywords나 sigungu를 확인해 주세요.")
            continue
        hpid, matched_name = result
        hospital["hpid"] = hpid
        print(f"[찾음] {hospital['name']} -> hpid={hpid} (API상 기관명: {matched_name})")

    TARGET_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과를 저장했습니다: {TARGET_FILE}")


if __name__ == "__main__":
    main()
