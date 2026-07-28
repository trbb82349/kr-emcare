"""국립중앙의료원 응급의료기관 정보 조회 API(ErmctInfoInqireService) 호출 공통 함수.

공공데이터포털 상세: https://www.data.go.kr/data/15000563/openapi.do
"""
import xml.etree.ElementTree as ET

import requests

from common import API_BASE, get_service_key


def call_api(operation: str, params: dict) -> list[dict]:
    """오퍼레이션 이름과 파라미터로 API를 호출하고 item 목록을 dict 리스트로 반환한다."""
    url = f"{API_BASE}/{operation}"
    query = {"serviceKey": get_service_key(), "_type": "json"}
    query.update(params)

    resp = requests.get(url, params=query, timeout=10)
    resp.raise_for_status()

    # 정상 상황이면 JSON, 인증키 오류 등 일부 상황에서는 XML 에러 메시지가 온다.
    content_type = resp.headers.get("Content-Type", "")
    if "json" in content_type:
        data = resp.json()
        header = data.get("response", {}).get("header", {})
        result_code = header.get("resultCode")
        if result_code not in ("00", None):
            raise SystemExit(f"API 오류({result_code}): {header.get('resultMsg')}")
        body = data.get("response", {}).get("body", {})
        items = body.get("items")
        if not items:
            return []
        item = items.get("item", [])
        if isinstance(item, dict):
            return [item]
        return item

    # XML 에러 응답 처리 (예: 서비스키 미등록, 트래픽 초과 등)
    root = ET.fromstring(resp.text)
    err_msg = root.findtext(".//returnAuthMsg") or root.findtext(".//errMsg") or resp.text[:300]
    raise SystemExit(f"API가 JSON이 아닌 응답을 반환했습니다 (인증키 확인 필요): {err_msg}")
