"""공통 유틸리티: .env 파일 읽기, 프로젝트 경로 계산."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

API_BASE = "https://apis.data.go.kr/B552657/ErmctInfoInqireService"


def load_env():
    """python-dotenv 없이 .env 파일을 읽어 os.environ에 채워 넣는다."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_service_key() -> str:
    load_env()
    key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "").strip()
    if not key:
        raise SystemExit(
            "DATA_GO_KR_SERVICE_KEY가 설정되어 있지 않습니다.\n"
            f"{ENV_PATH} 파일을 만들고 아래처럼 한 줄을 추가하세요:\n"
            "DATA_GO_KR_SERVICE_KEY=발급받은_인증키(Decoding 키)"
        )
    return key
