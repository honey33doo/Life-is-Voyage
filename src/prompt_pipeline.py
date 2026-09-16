"""
prompt_pipeline.py — 사용자 프롬프트 → 콘텐츠 자동 제작
=========================================================
사용법:
  python src/prompt_pipeline.py \\
    --topic "강남역이 비만 오면 잠기는 이유" \\
    --style architecture_doc \\
    --no-publish

  python src/prompt_pipeline.py \\
    --topic "고향의 봄, 어머니 생각" \\
    --style retro_trot

스타일 목록:
  architecture_doc   → 신비한 건축사전 스타일
  retro_trot         → 레트로 트로트 뮤비
  card_news          → 정치/시사 카드뉴스
  cooking_shorts     → 한국 요리 숏츠
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from config_loader import load_config, get_anthropic_key
from content_styles import get_style, list_styles, StyleConfig
from card_maker import make_cards, make_thumbnail
from video_maker import make_video
from publisher import publish_all

logger = logging.getLogger("cardnews.prompt_pipeline")


# ── Claude API 호출 ──────────────────────────────────────────────────────

def generate_script_from_prompt(
    topic: str,
    style: StyleConfig,
    api_key: str,
    model: str = "claude-sonnet-4-5",
) -> dict:
    """
    사용자 입력 주제 + 스타일 정의 → Claude API 호출 → 스크립트 JSON 반환
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = style.script_user_prompt_template.format(topic=topic)

    logger.info(f"Claude API 호출 중 (스타일: {style.label}, 주제: {topic})")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=style.claude_system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # JSON 파싱 (코드블록 제거)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}\n원문: {raw[:200]}")
        raise

    # 스타일 메타 주입
    script.setdefault("style", style.name)
    script.setdefault("topic", topic)

    return script


# ── 트로트 음원 생성 (Higgsfield) ───────────────────────────────────────

def generate_trot_audio(suno_prompt: str, output_dir: Path) -> Path | None:
    """
    Higgsfield AI 로 트로트 음원을 생성한다.
    실패 시 None 반환 (영상은 무음으로 계속 진행).
    """
    try:
        import subprocess
        # Higgsfield는 MCP 도구이므로 직접 subprocess 호출 불가
        # → 이 함수는 Claude 세션에서만 동작 (MCP 툴 직접 호출)
        # → 실제 구현은 scheduled_runner 또는 Claude 세션에서 처리
        logger.info("트로트 음원 생성: Higgsfield AI (MCP 세션에서 처리됩니다)")
        logger.info(f"Suno 프롬프트: {suno_prompt}")
        return None
    except Exception as e:
        logger.warning(f"음원 생성 스킵: {e}")
        return None


# ── AI 이미지 생성 힌트 주입 ─────────────────────────────────────────────

def enrich_cards_with_image_hints(script: dict, style: StyleConfig) -> dict:
    """
    카드의 visual_prompt 가 비어있으면 스타일 기본 이미지 프롬프트를 주입.
    """
    for card in script.get("cards", []):
        if not card.get("visual_prompt") and style.image_style_prompt:
            # 카드 제목으로 이미지 프롬프트 자동 생성
            card["visual_prompt"] = (
                f"{card.get('headline', '')} — {style.image_style_prompt}"
            )
    return script


# ── 출력 디렉터리 ─────────────────────────────────────────────────────────

def get_output_dir(style_name: str, topic: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic[:20].replace(" ", "_").replace("/", "_")
    out = ROOT / "outputs" / f"{style_name}_{safe_topic}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    return out


# ── 메인 ──────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    parser = argparse.ArgumentParser(
        description="프롬프트 입력 → 콘텐츠 자동 제작",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--topic", required=True, help="콘텐츠 주제 (한 문장)")
    parser.add_argument(
        "--style", default="card_news",
        help=f"콘텐츠 스타일:\n{list_styles()}"
    )
    parser.add_argument(
        "--config", default=str(ROOT / "config" / "my_job.json"),
        help="설정 파일 경로"
    )
    parser.add_argument("--no-publish", action="store_true", help="발행 스킵")
    parser.add_argument("--output-dir", default=None, help="출력 경로 지정")
    args = parser.parse_args()

    # ── 설정 로드 ──
    cfg = load_config(args.config)
    api_key = get_anthropic_key(cfg)
    style = get_style(args.style)

    logger.info("=" * 60)
    logger.info(f"✏️  주제  : {args.topic}")
    logger.info(f"🎨 스타일: {style.label}")
    logger.info("=" * 60)

    # ── 출력 디렉터리 ──
    output_dir = (
        Path(args.output_dir) if args.output_dir
        else get_output_dir(args.style, args.topic)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"출력 경로: {output_dir}")

    # ── [1] 스크립트 생성 ──
    logger.info("[1/4] 스크립트 생성 중...")
    script = generate_script_from_prompt(args.topic, style, api_key)
    script = enrich_cards_with_image_hints(script, style)

    # 스타일 설정 병합 (카드 색상 등)
    cfg_for_style = dict(cfg)
    cfg_for_style["media"] = {
        **cfg.get("media", {}),
        "card_format": "1080x1080",
        "card_style": "dark_modern",
        "brand_color_primary": style.brand_color_primary,
        "brand_color_accent": style.brand_color_accent,
        "brand_name": cfg.get("media", {}).get("brand_name", "데이뉴스"),
    }
    if style.as_shorts:
        cfg_for_style.setdefault("publish", {}).setdefault("youtube", {})["as_shorts"] = True

    (output_dir / "script.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"  → 카드 {len(script.get('cards', []))}장 스크립트 완료")

    # ── [2] 음원 생성 (트로트 전용) ──
    bgm_path = None
    if style.name == "retro_trot" and script.get("suno_prompt"):
        logger.info("[2/4] 트로트 음원 생성 중 (Higgsfield AI)...")
        bgm_path = generate_trot_audio(script["suno_prompt"], output_dir)
    else:
        logger.info("[2/4] 음원 생성 스킵 (해당 스타일 아님)")

    # ── [3] 카드 이미지 + 영상 제작 ──
    logger.info("[3/4] 카드 이미지 생성 중...")
    card_paths = make_cards(script, cfg_for_style, output_dir)
    thumbnail_path = make_thumbnail(script, cfg_for_style, output_dir)
    video_path = make_video(
        card_paths, output_dir, cfg_for_style,
        as_shorts=style.as_shorts,
        bgm_path=bgm_path,
    )
    logger.info(f"  → 카드 {len(card_paths)}장 + 영상 생성 완료")

    # ── [4] 발행 ──
    logger.info("[4/4] 발행 처리 중...")
    no_publish = args.no_publish or cfg.get("require_approval", True)
    results = publish_all(
        script=script,
        article=None,
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        card_paths=card_paths,
        cfg=cfg_for_style,
        no_publish=no_publish,
    )

    # ── 결과 보고 ──
    logger.info("\n" + "=" * 60)
    logger.info("✅ 제작 완료")
    logger.info(f"  스타일  : {style.label}")
    logger.info(f"  주제    : {args.topic}")
    logger.info(f"  카드    : {len(card_paths)}장")
    logger.info(f"  영상    : {video_path or 'N/A'}")
    logger.info(f"  출력    : {output_dir}")
    if results.get("youtube"):
        logger.info(f"  YouTube : https://youtu.be/{results['youtube']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
