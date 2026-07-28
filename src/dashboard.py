"""fetch_er_status.py가 모은 데이터로 output/dashboard.html(정적 페이지)을 만든다.

색은 "상태(status)" 용도로만 쓴다 (good/warning/serious/critical) — 데이터 색이 아니므로
카테고리 팔레트와 섞이지 않도록 별도 4색만 사용하고, 색만으로 의미를 전달하지 않게
아이콘 + 글자 라벨을 항상 같이 붙인다.
"""
from pathlib import Path

STATUS_STEPS = [
    # (임계값 초과 여부 판단 함수, 상태 키, 아이콘, 라벨)
    (lambda v: v < 0, "critical", "\U0001F534", "초과"),
    (lambda v: v == 0, "serious", "\U0001F7E0", "포화"),
    (lambda v: v <= 2, "warning", "\U0001F7E1", "혼잡"),
]

STATUS_COLORS = {
    # references/palette.md 의 고정 상태 팔레트 (light, dark)
    "good": ("#0ca30c", "#0ca30c"),
    "warning": ("#fab219", "#fab219"),
    "serious": ("#ec835a", "#ec835a"),
    "critical": ("#d03b3b", "#e66767"),
    "muted": ("#898781", "#898781"),
}


def classify(value) -> tuple[str, str, str]:
    """여유병상 수 -> (상태키, 아이콘, 라벨). 값이 없으면 muted/정보없음."""
    if value in ("", None):
        return "muted", "⚪", "정보없음"
    v = int(value)
    for is_match, key, icon, label in STATUS_STEPS:
        if is_match(v):
            return key, icon, label
    return "good", "\U0001F7E2", "여유"


def _tile(row: dict) -> str:
    status_key, icon, label = classify(row["응급실_여유병상"])
    value_text = row["응급실_여유병상"] if row["응급실_여유병상"] != "" else "정보없음"
    hvidate = str(row.get("정보갱신시각", ""))
    time_text = f"{hvidate[8:10]}:{hvidate[10:12]} 갱신" if len(hvidate) == 14 else "갱신시각 정보없음"

    def sub(field, label_text):
        v = row.get(field, "")
        return f'<span class="sub-item">{label_text} {v if v != "" else "-"}</span>'

    return f"""
    <article class="tile status-{status_key}">
      <h2 class="tile-name">{row['병원명']}</h2>
      <p class="tile-value">{value_text}<span class="tile-unit">병상</span></p>
      <p class="tile-badge"><span aria-hidden="true">{icon}</span> {label}</p>
      <p class="tile-sub">
        {sub('입원실_여유병상', '입원실')}
        {sub('일반중환자실_여유병상', '중환자실')}
        {sub('수술실_여유병상', '수술실')}
      </p>
      <p class="tile-time">{time_text}</p>
    </article>"""


def _table_rows(rows: list[dict]) -> str:
    out = []
    for row in rows:
        status_key, icon, label = classify(row["응급실_여유병상"])
        out.append(
            "<tr>"
            f"<td>{row['병원명']}</td>"
            f"<td>{icon} {label}</td>"
            f"<td class='num'>{row['응급실_여유병상']}</td>"
            f"<td class='num'>{row.get('입원실_여유병상', '')}</td>"
            f"<td class='num'>{row.get('일반중환자실_여유병상', '')}</td>"
            f"<td class='num'>{row.get('수술실_여유병상', '')}</td>"
            f"<td>{row.get('정보갱신시각', '')}</td>"
            "</tr>"
        )
    return "\n".join(out)


def build_dashboard_html(rows: list[dict], generated_at_text: str) -> str:
    tiles_html = "\n".join(_tile(row) for row in rows)
    table_html = _table_rows(rows)

    # Datarize 디자인 토큰(2026-07-13 검증본) 그대로 사용.
    # 상태색(여유/혼잡/포화/초과)은 Datarize 문서에 없는 값이라, 접근성 검증을 마친
    # 기존 상태 팔레트를 그대로 쓰고 나머지(배경/글자/버튼/카드/간격)만 맞춘다.
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>서울 5대병원 응급실 혼잡도</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" as="style" crossorigin
      href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
<style>
  .dz-root {{
    /* Datarize tokens.colors */
    --canvas: #ffffff;
    --ink: #191919;
    --action: #111111;
    --body-text: #5d6875;
    --link: #007aff;
    --surface: #f2f5fa;
    --hairline: #e5e7eb;
    /* Datarize tokens.rounded */
    --r-sm: 8px;
    --r-md: 10px;
    --r-pill: 50px;
    --r-full: 999px;
    /* Datarize tokens.spacing */
    --sp-xs: 6px; --sp-sm: 8px; --sp-md: 10px; --sp-lg: 14px;
    --sp-xl: 16px; --sp-xxl: 20px; --sp-xxxl: 24px; --sp-section: 32px;
    /* status palette — Datarize 문서에 정의가 없어 별도 유지 */
    --good: {STATUS_COLORS['good'][0]};
    --warning: {STATUS_COLORS['warning'][0]};
    --serious: {STATUS_COLORS['serious'][0]};
    --critical: {STATUS_COLORS['critical'][0]};
    --muted-status: {STATUS_COLORS['muted'][0]};
  }}

  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--canvas);
    font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  .dz-root {{ max-width: 1040px; margin: 0 auto; padding: var(--sp-section) var(--sp-xxl) 48px; }}

  h1 {{
    color: var(--ink);
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1.3;
    margin: 0 0 var(--sp-xs);
  }}
  .subtitle {{ color: var(--body-text); font-size: 15px; line-height: 1.5; margin: 0 0 var(--sp-xxxl); }}
  .subtitle .hint {{ color: var(--body-text); }}

  .tiles {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--sp-lg);
    margin-bottom: var(--sp-section);
  }}
  .tile {{
    background: var(--canvas);
    border: 1px solid var(--hairline);
    border-left: 4px solid var(--status-color, var(--muted-status));
    border-radius: var(--r-md);
    padding: var(--sp-xl);
    box-shadow: none;
  }}
  .tile.status-good {{ --status-color: var(--good); }}
  .tile.status-warning {{ --status-color: var(--warning); }}
  .tile.status-serious {{ --status-color: var(--serious); }}
  .tile.status-critical {{ --status-color: var(--critical); }}
  .tile.status-muted {{ --status-color: var(--muted-status); }}

  .tile-name {{ font-size: 14px; font-weight: 500; color: var(--body-text); margin: 0 0 var(--sp-sm); }}
  .tile-value {{ font-size: 34px; font-weight: 600; color: var(--ink); margin: 0; line-height: 1.1; }}
  .tile-unit {{ font-size: 13px; font-weight: 400; color: var(--body-text); margin-left: 4px; }}
  .tile-badge {{ font-size: 13px; font-weight: 500; color: var(--body-text); margin: var(--sp-sm) 0 0; }}
  .tile-sub {{
    display: flex; flex-wrap: wrap; gap: var(--sp-sm);
    font-size: 12px; color: var(--body-text);
    margin: var(--sp-md) 0 0; padding-top: var(--sp-md);
    border-top: 1px solid var(--hairline);
  }}
  .tile-time {{ font-size: 11px; color: var(--body-text); opacity: 0.8; margin: var(--sp-sm) 0 0; }}

  table {{
    width: 100%; border-collapse: collapse;
    background: var(--canvas); border: 1px solid var(--hairline);
    border-radius: var(--r-md); overflow: hidden; font-size: 13px;
  }}
  caption {{ text-align: left; color: var(--body-text); font-size: 13px; margin-bottom: var(--sp-sm); }}
  th, td {{ padding: var(--sp-md) var(--sp-lg); text-align: left; border-bottom: 1px solid var(--hairline); color: var(--ink); }}
  th {{ background: var(--surface); color: var(--body-text); font-weight: 600; font-size: 12px; }}
  td.num {{ font-variant-numeric: tabular-nums; }}
  tr:last-child td {{ border-bottom: none; }}

  a {{ color: var(--link); }}
</style>
</head>
<body>
<div class="dz-root">
  <h1>서울 5대병원 응급실 혼잡도</h1>
  <p class="subtitle">{generated_at_text} 기준 · 여유병상 수가 음수면 정원을 초과해 받고 있다는 뜻입니다 · <span class="hint">국립중앙의료원 공공데이터 API</span></p>

  <section class="tiles" aria-label="병원별 응급실 여유병상 요약">
{tiles_html}
  </section>

  <table>
    <caption>전체 상세 표</caption>
    <thead>
      <tr><th>병원명</th><th>상태</th><th>응급실</th><th>입원실</th><th>중환자실</th><th>수술실</th><th>정보갱신시각</th></tr>
    </thead>
    <tbody>
{table_html}
    </tbody>
  </table>
</div>
</body>
</html>
"""


def write_dashboard(rows: list[dict], generated_at_text: str, out_path: Path) -> None:
    html = build_dashboard_html(rows, generated_at_text)
    out_path.write_text(html, encoding="utf-8")
