"""fetch_er_status.py가 모은 데이터로 output/dashboard.html(정적 페이지)을 만든다.

색은 "상태(status)" 용도로만 쓴다 (good/warning/serious/critical) — 데이터 색이 아니므로
카테고리 팔레트와 섞이지 않도록 별도 4색만 사용하고, 색만으로 의미를 전달하지 않게
아이콘 + 글자 라벨을 항상 같이 붙인다.
"""
from pathlib import Path

from duty_view import region_duty_panel_html
from korea_map import (
    LABEL_POINTS,
    REGION_PATHS,
    SEJONG_POINT,
    SEJONG_RADIUS,
    SMALL_LABEL_REGIONS,
    VIEW_BOX,
)

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
      <h3 class="tile-name">{row['병원명']}</h3>
      <p class="tile-value">{value_text}<span class="tile-unit">병상</span></p>
      <p class="tile-badge"><span aria-hidden="true">{icon}</span> {label}</p>
      <p class="tile-sub">
        {sub('입원실_여유병상', '입원실')}
        {sub('일반중환자실_여유병상', '중환자실')}
        {sub('수술실_여유병상', '수술실')}
      </p>
      <p class="tile-time">{time_text}</p>
    </article>"""


# 전국 17개 시도 (id, 표시 이름). 지도 모양은 korea_map.REGION_PATHS에서 가져온다.
REGIONS = [
    ("seoul", "서울"),
    ("busan", "부산"),
    ("daegu", "대구"),
    ("incheon", "인천"),
    ("gwangju", "광주"),
    ("daejeon", "대전"),
    ("ulsan", "울산"),
    ("sejong", "세종"),
    ("gyeonggi", "경기"),
    ("gangwon", "강원"),
    ("chungbuk", "충북"),
    ("chungnam", "충남"),
    ("jeonbuk", "전북"),
    ("jeonnam", "전남"),
    ("gyeongbuk", "경북"),
    ("gyeongnam", "경남"),
    ("jeju", "제주"),
]


def _region_map_svg(default_region: str, has_data_ids: set[str]) -> str:
    """실제 국경선 모양의 SVG 지도를 만든다 (출처: korea_map.py 상단 주석 참고).

    각 지역은 path(모양) 바로 뒤에 그 지역의 이름표(text)를 붙여서 그린다.
    CSS에서 인접 형제 선택자(+)로 "선택된 지역이면 글자를 흰색으로" 처리하려면
    이 순서(모양 -> 이름표)가 유지되어야 한다.
    """
    shapes = []
    for region_id, label in REGIONS:
        if region_id == "sejong":
            continue  # 세종은 지도 경로가 없어서 아래에서 점으로 따로 그린다.
        d = REGION_PATHS[region_id]
        pressed = "true" if region_id == default_region else "false"
        data_class = " has-data" if region_id in has_data_ids else ""
        lx, ly = LABEL_POINTS[region_id]
        size_class = " small" if region_id in SMALL_LABEL_REGIONS else ""
        shapes.append(
            f'<path class="region-shape{data_class}" data-region="{region_id}" '
            f'tabindex="0" role="button" aria-pressed="{pressed}" aria-label="{label}" '
            f'd="{d}"><title>{label}</title></path>\n'
            f'<text class="region-label{size_class}" data-region="{region_id}" '
            f'x="{lx}" y="{ly}">{label}</text>'
        )

    sx, sy = SEJONG_POINT
    sejong_class = " has-data" if "sejong" in has_data_ids else ""
    sejong_pressed = "true" if default_region == "sejong" else "false"
    shapes.append(
        f'<circle class="region-point{sejong_class}" data-region="sejong" cx="{sx}" cy="{sy}" r="{SEJONG_RADIUS}" '
        f'tabindex="0" role="button" aria-pressed="{sejong_pressed}" aria-label="세종"><title>세종</title></circle>\n'
        f'<text class="region-label small" data-region="sejong" x="{sx}" y="{sy}">세종</text>'
    )
    shapes_html = "\n".join(shapes)

    return f"""
    <svg class="region-map" viewBox="{VIEW_BOX}" role="group" aria-label="대한민국 지역 선택 지도" xmlns="http://www.w3.org/2000/svg">
{shapes_html}
    </svg>"""


def _region_widget(
    scope: str,
    seoul_panel_html: str | None = None,
    region_content_fn=None,
    has_data_ids: set[str] | None = None,
) -> str:
    """지역 선택 지도 + 지역별 정보 패널을 만든다.

    scope: "er"(응급실) 또는 "duty"(공휴일/야간). DOM id가 겹치지 않게 접두어로 쓴다.
    seoul_panel_html: 서울 패널에 넣을 실제 데이터 HTML (ER 탭에서 사용). None이면 서울도 "준비중".
    region_content_fn: (region_id, label) -> HTML. 지정하면 모든 지역에 이 함수로 내용을 채운다
        (공휴일/야간 탭에서 사용 — 서울만이 아니라 지역마다 실제 데이터가 있을 수 있어서).
    has_data_ids: 지도에서 "실제 데이터 있음" 표시(초록 테두리)를 줄 지역 id 집합.
    """
    quick_tab_html = ""
    if seoul_panel_html is not None:
        quick_tab_html = f"""
    <div class="quick-tab-row">
      <button type="button" class="quick-tab" data-region="seoul" aria-pressed="true">서울 5대병원</button>
    </div>"""

    if has_data_ids is None:
        has_data_ids = {"seoul"} if seoul_panel_html is not None else set()

    map_html = _region_map_svg("seoul", has_data_ids)

    panels = []
    for region_id, label in REGIONS:
        if region_content_fn is not None:
            content = region_content_fn(region_id, label)
        elif region_id == "seoul" and seoul_panel_html is not None:
            content = seoul_panel_html
        else:
            content = f"""
      <strong>{label} 정보를 준비하고 있어요</strong>
      데이터가 연결되면 이 자리에 표시됩니다."""
        is_default_visible = region_id == "seoul"
        hidden_attr = "" if is_default_visible else " hidden"
        css_class = "region-panel" if (region_content_fn is not None or region_id == "seoul") else "region-panel placeholder"
        panels.append(
            f'<div class="{css_class}" data-region="{region_id}" id="panel-{scope}-{region_id}"{hidden_attr}>{content}</div>'
        )
    panels_html = "\n".join(panels)

    return f"""
  <div class="region-widget" data-scope="{scope}">{quick_tab_html}
    <div class="region-map-wrap">{map_html}</div>
    <div class="region-panels">
{panels_html}
    </div>
  </div>"""


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


def build_dashboard_html(rows: list[dict], generated_at_text: str, duty_data: dict | None = None) -> str:
    tiles_html = "\n".join(_tile(row) for row in rows)
    table_html = _table_rows(rows)

    # Datarize 디자인 토큰(2026-07-13 검증본) 그대로 사용.
    # 상태색(여유/혼잡/포화/초과)은 Datarize 문서에 없는 값이라, 접근성 검증을 마친
    # 기존 상태 팔레트를 그대로 쓰고 나머지(배경/글자/버튼/카드/간격)만 맞춘다.
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>emcare — 응급의료 케어 정보</title>
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

  .dz-logo {{ margin: 0 0 var(--sp-xxxl); }}
  .dz-logo .tagline {{
    font-size: 13px; font-weight: 500; color: var(--body-text);
    letter-spacing: 0.02em; margin: 0;
  }}
  .dz-logo .wordmark {{
    font-size: 30px; font-weight: 700; color: var(--ink);
    letter-spacing: -0.03em; margin: 2px 0 0; line-height: 1;
  }}

  .tabs {{
    display: inline-flex; gap: 4px;
    background: var(--surface); border: 1px solid rgba(25,25,25,0.1);
    border-radius: var(--r-full); padding: 5px;
    margin: 0 0 var(--sp-xxxl);
  }}
  .tab {{
    appearance: none; border: none; background: transparent; cursor: pointer;
    font-family: inherit; font-size: 14px; font-weight: 600; color: var(--body-text);
    padding: 10px 18px; border-radius: var(--r-full);
  }}
  .tab[aria-selected="true"] {{ background: var(--canvas); color: var(--ink); }}
  .tab:hover {{ color: var(--ink); }}

  .panel[hidden] {{ display: none; }}
  .panel-heading {{
    color: var(--ink); font-size: 20px; font-weight: 600;
    letter-spacing: -0.02em; margin: 0 0 var(--sp-xs);
  }}

  .placeholder {{
    border: 1px dashed var(--hairline); border-radius: var(--r-md);
    padding: 56px 24px; text-align: center; color: var(--body-text);
  }}
  .placeholder strong {{ display: block; color: var(--ink); font-size: 16px; margin-bottom: 6px; }}

  .region-widget {{ margin-top: var(--sp-xl); }}
  .quick-tab-row {{ margin-bottom: var(--sp-lg); }}
  .quick-tab {{
    appearance: none; cursor: pointer; font-family: inherit;
    background: var(--canvas); border: 1px solid var(--ink); color: var(--ink);
    font-size: 14px; font-weight: 600; border-radius: var(--r-full);
    padding: 10px 20px;
  }}
  .quick-tab[aria-pressed="true"] {{ background: var(--ink); color: #ffffff; }}

  .region-map-wrap {{ margin: 0 0 var(--sp-xxxl); }}
  .region-map {{ width: 100%; max-width: 300px; height: auto; }}
  .region-shape, .region-point {{
    fill: var(--surface); stroke: #aeb3ba; stroke-width: 0.9;
    cursor: pointer; outline: none;
    transition: fill .1s, stroke .1s;
  }}
  .region-shape.has-data, .region-point.has-data {{ stroke: var(--good); stroke-width: 1.2; }}
  .region-shape:hover, .region-point:hover {{ fill: var(--hairline); stroke: var(--link); stroke-width: 1.6; }}
  .region-shape[aria-pressed="true"], .region-point[aria-pressed="true"] {{ fill: var(--ink); stroke: var(--ink); }}
  .region-shape:focus-visible, .region-point:focus-visible {{ stroke: var(--link); stroke-width: 1.6; }}

  .region-label {{
    fill: var(--body-text); font-size: 5px; font-weight: 600;
    text-anchor: middle; dominant-baseline: middle;
    pointer-events: none; user-select: none;
  }}
  .region-label.small {{ font-size: 3.6px; }}
  .region-shape[aria-pressed="true"] + .region-label,
  .region-point[aria-pressed="true"] + .region-label {{ fill: #ffffff; }}

  .region-panel[hidden] {{ display: none; }}
  .region-panel.placeholder {{ padding: 40px 24px; }}

  .duty-heading {{ color: var(--ink); font-size: 15px; font-weight: 600; margin: var(--sp-xxl) 0 var(--sp-xs); }}
  .duty-heading:first-child {{ margin-top: 0; }}
  .duty-note {{ color: var(--body-text); font-size: 12px; margin: 0 0 var(--sp-sm); }}
  .duty-empty {{ color: var(--body-text); font-size: 13px; padding: var(--sp-lg) 0; }}
  .duty-table-wrap table {{ font-size: 12px; }}
  .duty-table-wrap th, .duty-table-wrap td {{ padding: var(--sp-sm) var(--sp-md); }}
</style>
</head>
<body>
<div class="dz-root">
  <div class="dz-logo">
    <p class="tagline">응급의료 케어 정보</p>
    <p class="wordmark">emcare</p>
  </div>

  <div class="tabs" role="tablist" aria-label="정보 종류">
    <button type="button" class="tab" role="tab" id="tab-er" aria-controls="panel-er" aria-selected="true">응급실 혼잡도 현황</button>
    <button type="button" class="tab" role="tab" id="tab-duty" aria-controls="panel-duty" aria-selected="false">공휴일 및 야간 진료 병원</button>
  </div>

  <section id="panel-er" class="panel" role="tabpanel" aria-labelledby="tab-er">
    <h2 class="panel-heading">응급실 혼잡도 현황</h2>
    <p class="subtitle">아래 "서울 5대병원"을 누르거나 지도에서 지역을 선택하면 그 지역 응급실 현황이 나옵니다.</p>
    {_region_widget("er", seoul_panel_html=f'''
    <p class="subtitle">{generated_at_text} 기준 · 여유병상 수가 음수면 정원을 초과해 받고 있다는 뜻입니다 · <span class="hint">국립중앙의료원 공공데이터 API</span></p>
    <div class="tiles" aria-label="병원별 응급실 여유병상 요약">
{tiles_html}
    </div>
    <table>
      <caption>전체 상세 표</caption>
      <thead>
        <tr><th>병원명</th><th>상태</th><th>응급실</th><th>입원실</th><th>중환자실</th><th>수술실</th><th>정보갱신시각</th></tr>
      </thead>
      <tbody>
{table_html}
      </tbody>
    </table>
    ''')}
  </section>

  <section id="panel-duty" class="panel" role="tabpanel" aria-labelledby="tab-duty" hidden>
    <h2 class="panel-heading">공휴일 및 야간 진료 병원</h2>
    <p class="subtitle">{f"{duty_data['meta']['last_updated']} 기준 · 하루 1번 갱신 · " if duty_data else ""}지도에서 지역을 선택하면 그 지역 정보가 나옵니다. 야간 진료는 아직 서울만 제공합니다.</p>
    {_region_widget(
        "duty",
        region_content_fn=lambda rid, lbl: region_duty_panel_html(rid, lbl, duty_data),
        has_data_ids=set(duty_data["holiday"].keys()) if duty_data else set(),
    )}
  </section>
</div>
<script>
(function () {{
  var tabs = document.querySelectorAll('.tab');
  tabs.forEach(function (tab) {{
    tab.addEventListener('click', function () {{
      tabs.forEach(function (t) {{ t.setAttribute('aria-selected', 'false'); }});
      tab.setAttribute('aria-selected', 'true');
      document.querySelectorAll('.panel').forEach(function (p) {{ p.hidden = true; }});
      document.getElementById(tab.getAttribute('aria-controls')).hidden = false;
    }});
  }});
}})();
(function () {{
  document.querySelectorAll('.region-widget').forEach(function (widget) {{
    var scope = widget.getAttribute('data-scope');
    var buttons = widget.querySelectorAll('.region-shape, .region-point, .quick-tab');
    function select(btn) {{
      var region = btn.getAttribute('data-region');
      buttons.forEach(function (b) {{
        b.setAttribute('aria-pressed', b.getAttribute('data-region') === region ? 'true' : 'false');
      }});
      widget.querySelectorAll('.region-panel').forEach(function (p) {{ p.hidden = true; }});
      var target = document.getElementById('panel-' + scope + '-' + region);
      if (target) target.hidden = false;
    }}
    buttons.forEach(function (btn) {{
      btn.addEventListener('click', function () {{ select(btn); }});
      btn.addEventListener('keydown', function (e) {{
        if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); select(btn); }}
      }});
    }});
  }});
}})();
</script>
</body>
</html>
"""


def write_dashboard(rows: list[dict], generated_at_text: str, out_path: Path, duty_data: dict | None = None) -> None:
    html = build_dashboard_html(rows, generated_at_text, duty_data=duty_data)
    out_path.write_text(html, encoding="utf-8")
