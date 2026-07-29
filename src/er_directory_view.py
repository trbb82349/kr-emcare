"""전국 응급의료기관 목록(data.json의 "directory")을 지역 패널 HTML로 그린다.

dashboard.py의 er_region_content가 그 지역 실시간 혼잡도(congestion)를 먼저 찾고,
없을 때만 이 병원 정보 전용 목록으로 대신한다 (지금은 실시간 혼잡도가 전국을 다 덮어서,
이 함수는 사실상 안전망 역할이다).
"""


def region_directory_panel_html(region_id: str, label: str, directory: dict | None) -> str:
    if directory is None:
        return f"""
      <strong>{label} 정보를 준비하고 있어요</strong>
      데이터가 연결되면 이 자리에 표시됩니다."""

    rows = directory.get(region_id, [])
    if not rows:
        return f"""
    <h3 class="duty-heading">{label} 응급의료기관</h3>
    <p class="duty-empty">등록된 응급의료기관이 없습니다.</p>"""

    merged_note = (
        '<p class="duty-note">광주·전남은 "전남광주통합특별시"로 행정구역이 통합되어, 같은 목록을 보여줍니다.</p>'
        if region_id in ("gwangju", "jeonnam") else ""
    )

    trs = "".join(
        "<tr>"
        f"<td>{r['name']}</td>"
        f"<td>{r.get('level', '')}</td>"
        f"<td>{r.get('addr', '')}</td>"
        f"<td>{r.get('tel', '')}</td>"
        "</tr>"
        for r in rows
    )
    return f"""
    <h3 class="duty-heading">{label} 응급의료기관 ({len(rows)}곳)</h3>
    <p class="duty-note">이 지역은 실시간 여유병상(혼잡도) 데이터가 아직 없어서, 병원 정보만 보여줍니다.</p>
    {merged_note}
    <div class="duty-table-wrap">
      <table>
        <thead><tr><th>병원명</th><th>등급</th><th>주소</th><th>전화</th></tr></thead>
        <tbody>{trs}</tbody>
      </table>
    </div>"""
