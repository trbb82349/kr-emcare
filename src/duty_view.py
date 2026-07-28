"""공휴일·야간 진료 데이터(data/duty_data.json)를 지역 패널 HTML로 그린다.

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


def _holiday_table(rows: list[dict]) -> str:
    if not rows:
        return '<p class="duty-empty">이 지역은 공휴일 진료 등록 정보가 없습니다.</p>'
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


def _night_table(rows: list[dict]) -> str:
    if not rows:
        return '<p class="duty-empty">이 지역은 야간 진료 데이터가 아직 없습니다.</p>'
    trs = []
    for r in rows[:PREVIEW_LIMIT]:
        trs.append(
            "<tr>"
            f"<td>{r['name']}</td>"
            f"<td>{_fmt_div(r)}</td>"
            f"<td>{_fmt_time(r.get('latest_close'))}까지</td>"
            f"<td>{r.get('tel', '')}</td>"
            "</tr>"
        )
    return f"""
    <div class="duty-table-wrap">
      <table>
        <thead><tr><th>병원명</th><th>구분</th><th>평일 마감</th><th>전화</th></tr></thead>
        <tbody>{''.join(trs)}</tbody>
      </table>
    </div>"""


def region_duty_panel_html(region_id: str, label: str, duty_data: dict | None) -> str:
    """한 지역의 공휴일/야간 진료 패널 내용을 만든다. duty_data가 없으면 전체 준비중."""
    if duty_data is None:
        return f"""
    <strong>{label} 정보를 준비하고 있어요</strong>
    데이터가 연결되면 이 자리에 표시됩니다."""

    holiday_rows = duty_data.get("holiday", {}).get(region_id, [])
    night_rows = duty_data.get("night", {}).get(region_id, [])
    has_night = region_id in duty_data.get("meta", {}).get("night_scope", [])

    holiday_note = f"총 {len(holiday_rows)}곳" + (f" · 처음 {PREVIEW_LIMIT}곳 미리보기" if len(holiday_rows) > PREVIEW_LIMIT else "")

    if has_night:
        night_note = f"총 {len(night_rows)}곳 (평일 마감 20:00 이후)" + (f" · 처음 {PREVIEW_LIMIT}곳 미리보기" if len(night_rows) > PREVIEW_LIMIT else "")
        night_html = _night_table(night_rows)
    else:
        night_note = "아직 서울만 제공합니다."
        night_html = '<p class="duty-empty">이 지역의 야간 진료 정보는 준비 중입니다.</p>'

    return f"""
    <h3 class="duty-heading">{label} · 공휴일 진료</h3>
    <p class="duty-note">{holiday_note}</p>
    {_holiday_table(holiday_rows)}

    <h3 class="duty-heading">{label} · 야간 진료</h3>
    <p class="duty-note">{night_note}</p>
    {night_html}"""
