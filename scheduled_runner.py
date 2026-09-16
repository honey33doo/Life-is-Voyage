"""
scheduled_runner.py ??Claude Cowork ?ˆì•½ ?¤í–‰ ?¤ì??¤íŠ¸?ˆì´??=============================================================
Claude Cowork ?ˆì•½ ?‘ì—…?ì„œ ?¸ì¶œ?˜ëŠ” ì§„ì…??
?¤í–‰ ?œì„œ:
  1. Google Drive MCP ë¡?anthropic_key.txt ?½ê¸°
  2. ANTHROPIC_API_KEY ?˜ê²½ë³€???¤ì •
  3. GitHub repo ?´ë¡  ?ëŠ” pull (ìµœì‹  ì½”ë“œ ?™ê¸°??
  4. python src/pipeline.py --config config/my_job.json ?¤í–‰

?¬ìš©ë²?(Claude Cowork ?ˆì•½ ?‘ì—… ?„ë¡¬?„íŠ¸???¬í•¨):
  python /home/claude/cardnews-auto/scheduled_runner.py

?˜ê²½ ?”êµ¬?¬í•­:
  - Google Drive MCP ?°ê²° (claude.ai Cowork)
  - GITHUB_REPO_URL ?˜ê²½ë³€???ëŠ” ?¤í¬ë¦½íŠ¸ ?ìˆ˜ë¡?ì§€??  - config/my_job.json ??credentials ?¹ì…˜ ?„ì„±
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ?€?€ ?ìˆ˜ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
GITHUB_REPO_URL = "https://github.com/honey33doo/Life-is-Voyage.git"
LOCAL_REPO_DIR  = Path("/home/claude/cardnews-auto")
CONFIG_FILE     = LOCAL_REPO_DIR / "config" / "my_job.json"
PIPELINE_SCRIPT = LOCAL_REPO_DIR / "src" / "pipeline.py"
DRIVE_KEY_FILE  = "anthropic_key.txt"   # Google Drive ë£¨íŠ¸???Œì¼ëª?
# ?€?€ ë¡œê¹… ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [runner] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cardnews.runner")


# ?€?€ ?¬í¼ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€

def _run(cmd: list[str], cwd: Path = None, env: dict = None) -> subprocess.CompletedProcess:
    """?œë¸Œ?„ë¡œ?¸ìŠ¤ ?¤í–‰ + ?¤íŒ¨ ???ˆì™¸."""
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
            f"ëª…ë ¹ ?¤íŒ¨ (exit {result.returncode}): {' '.join(cmd)}\n"
            f"STDERR: {result.stderr.strip()}"
        )
    return result


def _install_deps() -> None:
    """requirements.txt ?˜ì¡´???¤ì¹˜."""
    req = LOCAL_REPO_DIR / "requirements.txt"
    if not req.exists():
        logger.warning("requirements.txt ?†ìŒ ???˜ì¡´???¤ì¹˜ ?¤í‚µ")
        return
    logger.info("pip ?˜ì¡´???¤ì¹˜ ì¤?..")
    _run(
        [sys.executable, "-m", "pip", "install", "-r", str(req),
         "--break-system-packages", "-q"],
        cwd=LOCAL_REPO_DIR,
    )
    logger.info("?˜ì¡´???¤ì¹˜ ?„ë£Œ")


def _install_system_fonts() -> None:
    """?˜ëˆ”?°íŠ¸ ?œìŠ¤???¨í‚¤ì§€ ?¤ì¹˜ (?†ìœ¼ë©??œë„)."""
    try:
        import subprocess as sp
        result = sp.run(
            ["fc-list", ":lang=ko"],
            capture_output=True, text=True, timeout=5
        )
        if "Nanum" in result.stdout:
            return  # ?´ë? ?¤ì¹˜??    except Exception:
        pass
    logger.info("?˜ëˆ” ?°íŠ¸ ?¤ì¹˜ ì¤?..")
    try:
        _run(["apt-get", "install", "-y", "-q", "fonts-nanum", "fonts-nanum-extra"])
        logger.info("?˜ëˆ” ?°íŠ¸ ?¤ì¹˜ ?„ë£Œ")
    except Exception as e:
        logger.warning(f"?°íŠ¸ ?¤ì¹˜ ?¤íŒ¨ (ê³„ì† ì§„í–‰): {e}")


# ?€?€ Google Drive ???½ê¸° ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€

def _read_key_from_env() -> str | None:
    """?˜ê²½ë³€?˜ì— API ?¤ê? ?´ë? ?ˆìœ¼ë©?ë°˜í™˜."""
    return os.environ.get("ANTHROPIC_API_KEY", "").strip() or None


def _read_key_from_config() -> str | None:
    """config/my_job.json ??credentials.anthropic_key_value ?ì„œ ?½ê¸°."""
    if not CONFIG_FILE.exists():
        return None
    try:
        cfg = json.loads(CONFIG_FILE.read_text("utf-8"))
        return cfg.get("credentials", {}).get("anthropic_key_value", "").strip() or None
    except Exception:
        return None


def _read_key_from_drive_mcp() -> str | None:
    """
    Google Drive MCP ë¥??µí•´ anthropic_key.txt ?Œì¼???½ëŠ”??
    ???¨ìˆ˜??Claude Cowork ?¸ì…˜?ì„œ ì§ì ‘ ?¤í–‰?˜ëŠ” ê²½ìš°?ë§Œ ?™ì‘?œë‹¤.
    (MCP ?´ì? Python subprocess ?ì„œ ?¸ì¶œ ë¶ˆê? ??Claude ?¸ì…˜ ?´ë??ì„œë§?ê°€??

    ???¤ì œë¡œëŠ” scheduled_runner ê°€ Claude ?¸ì…˜???¼ë?ë¡??¤í–‰?˜ë?ë¡?
      Claude ê°€ MCP ë¥??µí•´ ?¤ë? ?½ì–´ ?˜ê²½ë³€?˜ë¡œ ë¨¼ì? ì£¼ì…????      ???¤í¬ë¦½íŠ¸ë¥??¸ì¶œ?´ì•¼ ?œë‹¤.

    Returns:
        None (???¨ìˆ˜?ì„œ??ì§ì ‘ MCP ?¸ì¶œ ë¶ˆê?)
    """
    logger.info(
        "Google Drive MCP ???½ê¸°??Claude ?¸ì…˜?ì„œ ì²˜ë¦¬?©ë‹ˆ??\n"
        "  ??ANTHROPIC_API_KEY ?˜ê²½ë³€?˜ê? ?¤ì •?˜ì–´ ?ˆì–´???©ë‹ˆ??\n"
        "  ???¤ì • ë°©ë²•: Claude ?¸ì…˜?ì„œ mcp__Google_Drive__read_file_content ë¡??½ì–´\n"
        "    os.environ['ANTHROPIC_API_KEY'] = <key> ë¡??„ë‹¬?˜ì„¸??"
    )
    return None


def get_api_key() -> str:
    """
    ?°ì„ ?œìœ„: ?˜ê²½ë³€????config ?Œì¼ ??(Drive MCP: ?¸ë??ì„œ ì£¼ì… ?„ìš”)
    """
    key = _read_key_from_env()
    if key:
        logger.info("??API ?? ?˜ê²½ë³€?˜ì—??ë¡œë“œ")
        return key

    key = _read_key_from_config()
    if key:
        logger.info("??API ?? config/my_job.json ?ì„œ ë¡œë“œ")
        os.environ["ANTHROPIC_API_KEY"] = key
        return key

    raise EnvironmentError(
        "ANTHROPIC_API_KEY ë¥?ì°¾ì„ ???†ìŠµ?ˆë‹¤.\n"
        "?¤ìŒ ì¤??˜ë‚˜ë¥?? íƒ?˜ì„¸??\n"
        "  1) ?˜ê²½ë³€??ANTHROPIC_API_KEY ?¤ì •\n"
        "  2) config/my_job.json ??credentials.anthropic_key_value ?…ë ¥\n"
        "  3) Claude ?¸ì…˜?ì„œ Google Drive MCP ë¡??½ì–´ ?˜ê²½ë³€?˜ì— ì£¼ì…"
    )


# ?€?€ GitHub ?™ê¸°???€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€

def sync_repo() -> None:
    """GitHub ?ì„œ ìµœì‹  ì½”ë“œë¥?ê°€?¸ì˜¨??(?´ë¡  or pull)."""
    git_dir = LOCAL_REPO_DIR / ".git"
    if git_dir.exists():
        logger.info("git pull ??ìµœì‹  ì½”ë“œ ?™ê¸°??ì¤?..")
        _run(["git", "pull", "--ff-only"], cwd=LOCAL_REPO_DIR)
        logger.info("git pull ?„ë£Œ")
    else:
        parent = LOCAL_REPO_DIR.parent
        parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"git clone {GITHUB_REPO_URL} ??{LOCAL_REPO_DIR}")
        _run(
            ["git", "clone", GITHUB_REPO_URL, str(LOCAL_REPO_DIR)],
            cwd=parent,
        )
        logger.info("git clone ?„ë£Œ")


# ?€?€ ?Œì´?„ë¼???¤í–‰ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€

def run_pipeline(step: str = "all", no_publish: bool = False) -> None:
    """pipeline.py ë¥?ì§€?•ëœ ?¤í…?¼ë¡œ ?¤í–‰?œë‹¤."""
    cmd = [
        sys.executable, str(PIPELINE_SCRIPT),
        "--config", str(CONFIG_FILE),
        "--step", step,
    ]
    if no_publish:
        cmd.append("--no-publish")

    logger.info(f"?Œì´?„ë¼???¤í–‰: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(LOCAL_REPO_DIR))
    if result.returncode != 0:
        raise RuntimeError(f"?Œì´?„ë¼???¤íŒ¨ (exit {result.returncode})")


# ?€?€ ë©”ì¸ ?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€?€

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ì¹´ë“œ?´ìŠ¤ ?ë™???¤ì?ì¤??¤í–‰ê¸?)
    parser.add_argument("--step", default="all",
                        choices=["all", "research", "script", "cards", "publish"],
                        help="?¤í–‰???Œì´?„ë¼???¤í…")
    parser.add_argument("--no-sync", action="store_true",
                        help="GitHub ?™ê¸°???¤í‚µ (ë¡œì»¬ ì½”ë“œ ?¬ìš©)")
    parser.add_argument("--no-publish", action="store_true",
                        help="ë°œí–‰ ?¨ê³„ ?¤í‚µ (ì½˜í…ì¸ ë§Œ ?ì„±)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("ì¹´ë“œ?´ìŠ¤ ?ë™?????¤ì?ì¤??¤í–‰ ?œì‘")
    logger.info("=" * 60)

    # 1. API ???•ì¸
    get_api_key()

    # 2. GitHub ?™ê¸°??    if not args.no_sync:
        try:
            sync_repo()
        except Exception as e:
            logger.warning(f"GitHub ?™ê¸°???¤íŒ¨ (ë¡œì»¬ ì½”ë“œë¡?ê³„ì†): {e}")

    # 3. ?œìŠ¤???°íŠ¸ + ?˜ì¡´??    _install_system_fonts()
    _install_deps()

    # 4. config ?Œì¼ ?•ì¸
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"?¤ì • ?Œì¼ ?†ìŒ: {CONFIG_FILE}\n"
            "config/my_job.json ???ì„±?˜ì„¸?? (config/sample_job.json ì°¸ê³ )"
        )

    # 5. ?Œì´?„ë¼???¤í–‰
    run_pipeline(step=args.step, no_publish=args.no_publish)

    logger.info("=" * 60)
    logger.info("???¤ì?ì¤??¤í–‰ ?„ë£Œ")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
