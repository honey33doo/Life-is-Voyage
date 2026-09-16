"""
pipeline.py — 유튜브 카드뉴스 자동화 메인 파이프라인
=====================================================
실행 예시:
  python src/pipeline.py --config config/my_job.json
  python src/pipeline.py --config config/my_job.json --no-publish
  python src/pipeline.py --config config/my_job.json --step research
  python src/pipeline.py --config config/my_job.json --step script
  python src/pipeline.py --config config/my_job.json --step cards
  python src/pipeline.py --config config/my_job.json --step publish

스텝 구조:
  [1] research  → sources.json
  [2] script    → script.json + article.json
  [3] cards     → outputs/cards/*.jpg + video.mp4
  [4] publish   → 각 플랫폼 게시
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path 에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config_loader import load_config, get_anthropic_key
from researcher import run_research
from script_writer import generate_cardnews_script, generate_article
from card_maker import make_cards, make_thumbnail
from video_maker import make_video
from publisher import publish_all

# ────────────────────────────────────────────────
# 로깅 설정
# ────────────────────────────────────────────────

def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"run_{ts}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding="utf-8"),
        ],
    )

logger = logging.getLogger("cardnews.pipeline")


# ────────────────────────────────────────────────
# 상태 저장 / 로드 (Resume 지원)
# ────────────────────────────────────────────────

def _state_path(output_dir: Path) -> Path:
    return output_dir / "state.json"


def load_state(output_dir: Path) -> dict:
    sp = _state_path(output_dir)
    if sp.exists():
        try:
            return json.loads(sp.read_text("utf-8"))
        except Exception:
            pass
    return {}


def save_state(output_dir: Path, state: dict) -> None:
    _state_path(output_dir).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ────────────────────────────────────────────────
# 출력 디렉터리 결정
# ────────────────────────────────────────────────

def get_output_dir(cfg: dict) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = cfg.get("job_id", "job")
    out = ROOT / "outputs" / f"{job_id}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    return out


# ────────────────────────────────────────────────
# 파이프라인 스텝
# ────────────────────────────────────────────────

def step_research(cfg: dict, output_dir: Path, state: dict) -> list[dict]:
    if "sources" in state:
        logger.info("▶ [1/4] 리서치: 기존 결과 재사용")
        return state["sources"]
    logger.info("▶ [1/4] 리서치 시작...")
    sources = run_research(cfg)
    state["sources"] = sources
    (output_dir / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"  → {len(sources)}개 소스 수집 완료")
    return sources


def step_script(cfg: dict, sources: list[dict], output_dir: Path, api_key: str, state: dict) -> tuple[dict, dict]:
    if "script" in state and "article" in state:
        logger.info("▶ [2/4] 스크립트: 기존 결과 재사용")
        return state["script"], state.get("article")
    logger.info("▶ [2/4] 스크립트 생성 중...")
    script = generate_cardnews_script(cfg, sources, api_key)
    article = generate_article(cfg, sources, api_key)
    state["script"] = script
    state["article"] = article
    (output_dir / "script.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if article:
        (output_dir / "article.json").write_text(
            json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    logger.info(f"  → 카드 {len(script.get('cards', []))}장 스크립트 완료")
    return script, article


def step_cards(cfg: dict, script: dict, output_dir: Path, state: dict):
    if "card_paths" in state:
        logger.info("▶ [3/4] 카드 이미지: 기존 결과 재사용")
        card_paths = [Path(p) for p in state["card_paths"]]
        video_path = Path(state["video_path"]) if state.get("video_path") else None
        thumb_path = Path(state["thumbnail_path"]) if state.get("thumbnail_path") else None
        return card_paths, video_path, thumb_path

    logger.info("▶ [3/4] 카드 이미지 생성 중...")
    card_paths = make_cards(script, cfg, output_dir)
    thumbnail_path = make_thumbnail(script, cfg, output_dir)

    # 영상 생성
    as_shorts = cfg.get("publish", {}).get("youtube", {}).get("as_shorts", False)
    video_path = make_video(card_paths, output_dir, cfg, as_shorts=as_shorts)

    state["card_paths"] = [str(p) for p in card_paths]
    state["video_path"] = str(video_path) if video_path else None
    state["thumbnail_path"] = str(thumbnail_path) if thumbnail_path else None

    logger.info(f"  → 카드 {len(card_paths)}장 + 영상 생성 완료")
    return card_paths, video_path, thumbnail_path


def step_publish(cfg: dict, script: dict, article, video_path, thumbnail_path, card_paths, no_publish: bool, state: dict) -> dict:
    if "publish_results" in state:
        logger.info("▶ [4/4] 발행: 이미 완료된 결과 있음")
        return state["publish_results"]
    logger.info("▶ [4/4] 발행 중...")
    results = publish_all(
        script=script,
        article=article,
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        card_paths=card_paths,
        cfg=cfg,
        no_publish=no_publish,
    )
    state["publish_results"] = results
    return results


# ────────────────────────────────────────────────
# 메인
# ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="유튜브 카드뉴스 자동화 파이프라인")
    parser.add_argument("--config", required=True, help="설정 파일 경로 (JSON)")
    parser.add_argument(
        "--step",
        choices=["all", "research", "script", "cards", "publish"],
        default="all",
        help="실행할 스텝 (기본값: all)",
    )
    parser.add_argument(
        "--no-publish",
        action="store_true",
        help="발행 단계를 건너뜁니다 (콘텐츠만 생성)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="출력 디렉터리 경로 (기본값: outputs/job_id_timestamp)",
    )
    args = parser.parse_args()

    # ── 설정 로드 ──
    cfg = load_config(args.config)
    api_key = get_anthropic_key(cfg)

    # require_approval 체크
    no_publish = args.no_publish or cfg.get("require_approval", True)

    # ── 로깅 초기화 ──
    setup_logging(ROOT / "logs")
    logger.info(f"=== 카드뉴스 파이프라인 시작: {cfg['job_id']} ===")
    logger.info(f"주제: {cfg['topic']['main']}")
    logger.info(f"발행 모드: {'검토 필요 (--no-publish)' if no_publish else '자동 발행'}")

    # ── 출력 디렉터리 ──
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = get_output_dir(cfg)
    logger.info(f"출력 경로: {output_dir}")

    # ── Resume 상태 로드 ──
    state = load_state(output_dir)

    # ── 스텝 실행 ──
    step = args.step

    sources = None
    script = None
    article = None
    card_paths = []
    video_path = None
    thumbnail_path = None

    try:
        if step in ("all", "research"):
            sources = step_research(cfg, output_dir, state)
            save_state(output_dir, state)
            if step == "research":
                logger.info("리서치 스텝 완료. 다음: --step script")
                return

        if step in ("all", "script"):
            if sources is None:
                sources = state.get("sources") or step_research(cfg, output_dir, state)
            script, article = step_script(cfg, sources, output_dir, api_key, state)
            save_state(output_dir, state)
            if step == "script":
                logger.info("스크립트 스텝 완료. 다음: --step cards")
                return

        if step in ("all", "cards"):
            if script is None:
                script = state.get("script")
                article = state.get("article")
                if not script:
                    if sources is None:
                        sources = state.get("sources") or step_research(cfg, output_dir, state)
                    script, article = step_script(cfg, sources, output_dir, api_key, state)
            card_paths, video_path, thumbnail_path = step_cards(cfg, script, output_dir, state)
            save_state(output_dir, state)
            if step == "cards":
                logger.info("카드 생성 스텝 완료. 다음: --step publish")
                return

        if step in ("all", "publish"):
            if script is None:
                script = state.get("script")
                article = state.get("article")
                if not card_paths:
                    card_paths = [Path(p) for p in state.get("card_paths", [])]
                if not video_path and state.get("video_path"):
                    video_path = Path(state["video_path"])
                if not thumbnail_path and state.get("thumbnail_path"):
                    thumbnail_path = Path(state["thumbnail_path"])

            results = step_publish(cfg, script, article, video_path, thumbnail_path, card_paths, no_publish, state)
            save_state(output_dir, state)

        # ── 최종 보고 ──
        logger.info("\n" + "="*60)
        logger.info("✅ 파이프라인 완료")
        logger.info(f"  출력 경로   : {output_dir}")
        logger.info(f"  카드 이미지 : {len(card_paths)}장")
        logger.info(f"  영상        : {video_path or 'N/A'}")
        if "publish_results" in state:
            r = state["publish_results"]
            logger.info(f"  YouTube     : {r.get('youtube') or '미발행'}")
            logger.info(f"  Instagram   : {r.get('instagram') or '미발행'}")
            logger.info(f"  네이버      : {r.get('naver') or '미발행'}")
            logger.info(f"  티스토리    : {r.get('tistory') or '미발행'}")
        logger.info("="*60)

    except KeyboardInterrupt:
        logger.warning("사용자가 중단했습니다. state.json 에 진행 상태 저장됨.")
        save_state(output_dir, state)
        sys.exit(1)
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        save_state(output_dir, state)
        sys.exit(1)


if __name__ == "__main__":
    main()
