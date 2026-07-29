"""공휴일 진료 데이터(data/duty_data.json)를 지역 패널 HTML로 그린다.

지역마다 수백~수천 건이라, 페이지에는 "총 개수 + 처음 30곳 미리보기"만 넣고
전체 목록은 data/duty_data.json 파일 자체에 남긴다.
"""
PREVIEW_LIMIT = 30


def _fmt_time(value) -> str:
    """900, "0900", 1800 같은 값을 "09:00" 형식으로 바꾼다."""
    if value in (None, ""):
        return "-"
    s = str(value).strip().zfill(4)
    if len(s) != 4 or not s.isdigit():
        return str(value)
    return f"{s[:2]}:{s[2:]}"


def _fmt_div(r: dict) -> str:
    """div가 "의원"이고 진료과목(dept)을 알면 "의원(안과)"처럼 붙여서 보여준다."""
    div = r.get("div", "")
    dept = r.get("dept")
    if div == "의원":
        return f"의원({dept})" if dept else "의원(과목 확인중)"
    return div


def _close_minutes(value) -> int:
    """마감시각을 분 단위로 바꾼다. "0000"은 자정(=24시간 운영으로 보고 가장 늦은 시각) 취급."""
    if value in (None, ""):
        return -1  # 정보 없음 -> 정렬에서 가장 뒤로
    s = str(value).strip().zfill(4)
    if len(s) != 4 or not s.isdigit():
        return -1
    h, m = int(s[:2]), int(s[2:])
    minutes = h * 60 + m
    return 24 * 60 if minutes == 0 else minutes


def _priority_sorted(rows: list[dict]) -> list[dict]:
    """종합병원을 먼저, 그 안에서는 공휴일 마감시각이 늦은(=야간까지 하는) 순으로 정렬한다."""
    return sorted(
        rows,
        key=lambda r: (0 if r.get("div") == "종합병원" else 1, -_close_minutes(r.get("holiday_close"))),
    )


def _holiday_table(rows: list[dict]) -> str:
    if not rows:
        return '<p class="duty-empty">이 지역은 공휴일 진료 등록 정보가 없습니다.</p>'
    rows = _priority_sorted(rows)
    trs = []
    for r in rows[:PREVIEW_LIMIT]:
        trs.append(
            "<tr>"
            f"<td>{r['name']}</td>"
            f"<td>{_fmt_div(r)}</td>"
            f"<td>{_fmt_time(r.get('holiday_open'))}~{_fmt_time(r.get('holiday_close'))}</td>"
            f"<td>{r.get('tel', '')}</td>"
            "</tr>"
        )
    return f"""
    <div class="duty-table-wrap">
      <table>
        <thead><tr><th>병원명</th><th>구분</th><th>공휴일 진료시간</th><th>전화</th></tr></thead>
        <tbody>{''.join(trs)}</tbody>
      </table>
    </div>"""


def region_duty_panel_html(region_id: str, label: str, duty_data: dict | None) -> str:
    """한 지역의 공휴일 진료 패널 내용을 만든다. duty_data가 없으면 전체 준비중."""
    if duty_data is None:
        return f"""
    <strong>{label} 정보를 준비하고 있어요</strong>
    데이터가 연결되면 이 자리에 표시됩니다."""

    holiday_rows = duty_data.get("holiday", {}).get(region_id, [])
    holiday_note = (
        f"총 {len(holiday_rows)}곳"
        + (f" · 처음 {PREVIEW_LIMIT}곳 미리보기" if len(holiday_rows) > PREVIEW_LIMIT else "")
        + " · 종합병원, 늦게까지 하는 곳 순으로 정렬"
    )
    merged_note = (
        '<p class="duty-note">광주·전남은 "전남광주통합특별시"로 행정구역이 통합되어, 같은 목록을 보여줍니다.</p>'
        if region_id in ("gwangju", "jeonnam") else ""
    )

    return f"""
    <h3 class="duty-heading">{label} · 공휴일 진료</h3>
    <p class="duty-note">{holiday_note}</p>
    {merged_note}
    {_holiday_table(holiday_rows)}"""
