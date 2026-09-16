"""
config_loader.py
================
설정 파일 로드 + Anthropic API 키를 Google Drive MCP 또는 환경변수에서 읽어온다.
Claude Cowork 스케줄 세션에서 실행될 때 Google Drive MCP 가 이미 연결되어 있으므로
해당 MCP 를 subprocess 로 직접 호출하지 않고, 스케줄 프롬프트에서
미리 환경변수 ANTHROPIC_API_KEY 를 주입한 뒤 pipeline.py 를 실행한다.
(Google Drive 에서 키를 읽는 로직은 scheduled_runner.py 에 있다.)
"""

import json
import os
import sys
from pathlib import Path


def load_config(config_path: str) -> dict:
    """JSON 설정 파일을 읽어 dict 로 반환한다."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    _validate_config(cfg)
    return cfg


def _validate_config(cfg: dict) -> None:
    """필수 키 존재 여부 확인."""
    required = ["job_id", "topic", "content", "publish"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"설정 파일에 필수 항목이 없습니다: {missing}")


def get_anthropic_key(cfg: dict) -> str:
    """
    Anthropic API 키를 다음 순서로 탐색한다.
    1. 환경변수 ANTHROPIC_API_KEY
    2. 설정 파일 내 credentials.anthropic_key_value (직접 입력)
    3. 설정 파일과 같은 폴더의 .env 파일
    """
    # 1. 환경변수
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key

    # 2. 설정 파일 직접 값 (배포 테스트용, 운영에서는 사용 금지)
    creds = cfg.get("credentials", {})
    key = creds.get("anthropic_key_value", "").strip()
    if key:
        return key

    # 3. .env 파일
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text("utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key

    raise EnvironmentError(
        "Anthropic API 키를 찾을 수 없습니다.\n"
        "다음 중 하나를 설정하세요:\n"
        "  1. 환경변수: export ANTHROPIC_API_KEY='sk-ant-...'\n"
        "  2. 프로젝트 루트 .env 파일: ANTHROPIC_API_KEY=sk-ant-..."
    )
