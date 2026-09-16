"""
scheduled_runner.py — Claude Cowork 예약 실행 오케스트레이터
=============================================================
Claude Cowork 예약 작업에서 호출하는 진입점.
실행 순서:
  1. Google Drive MCP 로 anthropic_key.txt 읽기
  2. ANTHROPIC_API_KEY 환경변수 설정
  3. GitHub repo 클론 또는 pull (최신 코드 동기화)
  4. python src/pipeline.py --config config/my_job.json 실행

사용법 (Claude Cowork 예약 작업 프롬프트에 포함):
  python /home/claude/cardnews-auto/scheduled_runner.py

환경 요구사항:
  - Google Drive MCP 연결 (claude.ai Cowork)
  - GITHUB_REPO_URL 환경변수 또는 스크립트 상수로 지정
  - config/my_job.json 에 credentials 섹션 완성
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ── 상수 ──────────────────────────────────────────────────────────────
GITHUB_REPO_URL = "https://github.com/honey33doo/cardnews-auto.git"
LOCAL_REPO_DIR  = Path("/home/claude/cardnews-auto")
CONFIG_FILE     = LOCAL_REPO_DIR / "config" / "my_job.json"
PIPELINE_SCRIPT = LOCAL_REPO_DIR / "src" / "pipeline.py"
DRIVE_KEY_FILE  = "anthropic_key.txt"   # Google Drive 루트의 파일명

# ── 로깅 ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [runner] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cardnews.runner")


# ── 헬퍼 ──────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path = None, env: dict = None) -> subprocess.CompletedProcess:
    """서브프로세스 실행 + 실패 시 예외."""
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"명령 실패 (exit {result.returncode}): {' '.join(cmd)}\n"
            f"STDERR: {result.stderr.strip()}"
        )
    return result


def _install_deps() -> None:
    """requirements.txt 의존성 설치."""
    req = LOCAL_REPO_DIR / "requirements.txt"
    if not req.exists():
        logger.warning("requirements.txt 없음 — 의존성 설치 스킵")
        return
    logger.info("pip 의존성 설치 중...")
    _run(
        [sys.executable, "-m", "pip", "install", "-r", str(req),
         "--break-system-packages", "-q"],
        cwd=LOCAL_REPO_DIR,
    )
    logger.info("의존성 설치 완료")


def _install_system_fonts() -> None:
    """나눔폰트 시스템 패키지 설치 (없으면 시도)."""
    try:
        import subprocess as sp
        result = sp.run(
            ["fc-list", ":lang=ko"],
            capture_output=True, text=True, timeout=5
        )
        if "Nanum" in result.stdout:
            return  # 이미 설치됨
    except Exception:
        pass
    logger.info("나눔 폰트 설치 중...")
    try:
        _run(["apt-get", "install", "-y", "-q", "fonts-nanum", "fonts-nanum-extra"])
        logger.info("나눔 폰트 설치 완료")
    except Exception as e:
        logger.warning(f"폰트 설치 실패 (계속 진행): {e}")


# ── Google Drive 키 읽기 ────────────────────────────────────────────────

def _read_key_from_env() -> str | None:
    """환경변수에 API 키가 이미 있으면 반환."""
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def _read_key_from_config() -> str | None:
    """config/my_job.json 의 credentials.anthropic_key_value 에서 읽기."""
    if not CONFIG_FILE.exists():
        return None
    try:
        cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
        return cfg.get("credentials", {}).get("anthropic_key_value", "").strip() or None
    except Exception:
        return None


def _read_key_from_drive_mcp() -> str | None:
    """
    Google Drive MCP 를 통해 anthropic_key.txt 파일을 읽는다.
    이 함수는 Claude Cowork 세션에서 직접 실행되는 경우에만 동작한다.
    (MCP 툴은 Python subprocess 에서 호출 불가 — Claude 세션 내부에서만 가능)

    → 실제로는 scheduled_runner 가 Claude 세션의 일부로 실행되므로,
      Claude 가 MCP 를 통해 키를 읽어 환경변수로 먼저 주입한 뒤
      이 스크립트를 호출해야 한다.

    Returns:
        None (이 함수에서는 직접 MCP 호출 불가)
    """
    logger.info(
        "Google Drive MCP 키 읽기는 Claude 세션에서 처리됩니다.\n"
        "  → ANTHROPIC_API_KEY 환경변수가 설정되어 있어야 합니다.\n"
        "  → 설정 방법: Claude 세션에서 mcp__Google_Drive__read_file_content 로 읽어\n"
        "    os.environ['ANTHROPIC_API_KEY'] = <key> 로 전달하세요."
    )
    return None


def get_api_key() -> str:
    """
    우선순위: 환경변수 → config 파일 → (Drive MCP: 외부에서 주입 필요)
    """
    key = _read_key_from_env()
    if key:
        logger.info("✓ API 키: 환경변수에서 로드")
        return key

    key = _read_key_from_config()
    if key:
        logger.info("✓ API 키: config/my_job.json 에서 로드")
        os.environ["ANTHROPIC_API_KEY"] = key
        return key

    raise EnvironmentError(
        "ANTHROPIC_API_KEY 를 찾을 수 없습니다.\n"
        "다음 중 하나를 선택하세요:\n"
        "  1) 환경변수 ANTHROPIC_API_KEY 설정\n"
        "  2) config/my_job.json 의 credentials.anthropic_key_value 입력\n"
        "  3) Claude 세션에서 Google Drive MCP 로 읽어 환경변수에 주입"
    )


# ── GitHub 동기화 ────────────────────────────────────────────────────────

def sync_repo() -> None:
    """GitHub 에서 최신 코드를 가져온다 (클론 or pull)."""
    git_dir = LOCAL_REPO_DIR / ".git"
    if git_dir.exists():
        logger.info("git pull — 최신 코드 동기화 중...")
        _run(["git", "pull", "--ff-only"], cwd=LOCAL_REPO_DIR)
        logger.info("git pull 완료")
    else:
        parent = LOCAL_REPO_DIR.parent
        parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"git clone {GITHUB_REPO_URL} → {LOCAL_REPO_DIR}")
        _run(
            ["git", "clone", GITHUB_REPO_URL, str(LOCAL_REPO_DIR)],
            cwd=parent,
        )
        logger.info("git clone 완료")


# ── 파이프라인 실행 ──────────────────────────────────────────────────────

def run_pipeline(step: str = "all", no_publish: bool = False) -> None:
    """pipeline.py 를 지정된 스텝으로 실행한다."""
    cmd = [
        sys.executable, str(PIPELINE_SCRIPT),
        "--config", str(CONFIG_FILE),
        "--step", step,
    ]
    if no_publish:
        cmd.append("--no-publish")

    logger.info(f"파이프라인 실행: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(LOCAL_REPO_DIR))
    if result.returncode != 0:
        raise RuntimeError(f"파이프라인 실패 (exit {result.returncode})")


# ── 메인 ──────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="카드뉴스 자동화 스케줄 실행기")
    parser.add_argument("--step", default="all",
                        choices=["all", "research", "script", "cards", "publish"],
                        help="실행할 파이프라인 스텝")
    parser.add_argument("--no-sync", action="store_true",
                        help="GitHub 동기화 스킵 (로컬 코드 사용)")
    parser.add_argument("--no-publish", action="store_true",
                        help="발행 단계 스킵 (콘텐츠만 생성)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("카드뉴스 자동화 — 스케줄 실행 시작")
    logger.info("=" * 60)

    # 1. API 키 확인
    get_api_key()

    # 2. GitHub 동기화
    if not args.no_sync:
        try:
            sync_repo()
        except Exception as e:
            logger.warning(f"GitHub 동기화 실패 (로컬 코드로 계속): {e}")

    # 3. 시스템 폰트 + 의존성
    _install_system_fonts()
    _install_deps()

    # 4. config 파일 확인
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"설정 파일 없음: {CONFIG_FILE}\n"
            "config/my_job.json 을 생성하세요. (config/sample_job.json 참고)"
        )

    # 5. 파이프라인 실행
    run_pipeline(step=args.step, no_publish=args.no_publish)

    logger.info("=" * 60)
    logger.info("✅ 스케줄 실행 완료")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
