#!/usr/bin/env python3
"""
make.py — 데이뉴스 콘텐츠 제작 인터페이스
==========================================
가장 간단한 실행 방법:

  python make.py

인터랙티브 메뉴로 스타일 선택 + 주제 입력 → 자동 제작.

또는 인수 직접 지정:

  python make.py --topic "강남역이 비만 오면 잠기는 이유"
  python make.py --topic "고향의 봄, 어머니 생각" --style retro_trot
  python make.py --topic "이재명 정부 주요 성과" --style card_news
  python make.py --topic "된장찌개 황금 레시피" --style cooking_shorts

옵션:
  --style      콘텐츠 스타일 (미지정 시 메뉴 표시)
  --topic      주제/키워드 (미지정 시 입력 요청)
  --no-publish 발행 없이 파일만 생성
  --config     설정 파일 경로 (기본: config/my_job.json)
"""

import argparse
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent

STYLE_MENU = {
    "1": ("architecture_doc", "🏗️  신비한 건축사전 스타일  (팩트 다큐, 수치 기반)"),
    "2": ("retro_trot",       "🎵  레트로 트로트 뮤직비디오  (AI 음원 + 영상)"),
    "3": ("card_news",        "📰  정치/시사 카드뉴스        (데이뉴스 메인)"),
    "4": ("cooking_shorts",   "🍜  한국 요리 숏츠            (레시피 카드)"),
}

EXAMPLES = {
    "architecture_doc": [
        "강남역이 비만 오면 잠기는 이유",
        "아파트 지하주차장이 물 위에 떠 있는 이유",
        "광화문이 원래 자리가 아니었던 이유",
    ],
    "retro_trot": [
        "고향의 봄, 어머니 생각",
        "첫사랑 그리움",
        "도시에서 살아가는 시골 청춘",
    ],
    "card_news": [
        "이재명 정부 3대 경제 성과",
        "김어준 과거 발언 팩트체크",
        "야당의 주장 vs 실제 사실",
    ],
    "cooking_shorts": [
        "백종원 스타일 김치찌개",
        "10분 완성 간장계란밥",
        "꿀떡 같은 뼈다귀해장국",
    ],
}


def print_banner():
    print("\n" + "=" * 55)
    print("  데이뉴스 콘텐츠 자동 제작 시스템")
    print("  by Claude AI × 완전 자동화")
    print("=" * 55)


def select_style_interactive() -> str:
    print("\n📌 콘텐츠 스타일을 선택하세요:\n")
    for num, (key, label) in STYLE_MENU.items():
        print(f"  [{num}] {label}")
    print()

    while True:
        choice = input("번호 입력 (1-4): ").strip()
        if choice in STYLE_MENU:
            style_key = STYLE_MENU[choice][0]
            print(f"\n  ✓ 선택: {STYLE_MENU[choice][1]}")
            return style_key
        print("  ⚠️  1~4 중에서 선택하세요.")


def input_topic_interactive(style_key: str) -> str:
    examples = EXAMPLES.get(style_key, [])
    print("\n📝 주제를 입력하세요 (한 문장):")
    if examples:
        print("  예시:")
        for ex in examples:
            print(f"    · {ex}")
    print()
    topic = input("주제 → ").strip()
    if not topic:
        print("  ⚠️  주제를 입력해야 합니다.")
        sys.exit(1)
    return topic


def confirm_and_run(style_key: str, topic: str, no_publish: bool, config: str):
    style_label = next(
        label for key, label in STYLE_MENU.values() if key == style_key
    ) if style_key in [k for k, _ in STYLE_MENU.values()] else style_key

    print("\n" + "─" * 55)
    print(f"  스타일 : {style_key}")
    print(f"  주제   : {topic}")
    print(f"  발행   : {'❌ 스킵 (파일만 생성)' if no_publish else '✅ 자동 발행'}")
    print("─" * 55)
    answer = input("\n제작을 시작하시겠습니까? [Y/n] ").strip().lower()
    if answer in ("n", "no"):
        print("취소되었습니다.")
        sys.exit(0)

    cmd = [
        sys.executable,
        str(ROOT / "src" / "prompt_pipeline.py"),
        "--topic", topic,
        "--style", style_key,
        "--config", config,
    ]
    if no_publish:
        cmd.append("--no-publish")

    print("\n🚀 제작 시작!\n")
    result = subprocess.run(cmd, cwd=str(ROOT))
    sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="데이뉴스 콘텐츠 자동 제작",
        add_help=True,
    )
    parser.add_argument("--topic",  default=None, help="주제 (미지정 시 대화형 입력)")
    parser.add_argument("--style",  default=None, help="스타일 키 (미지정 시 메뉴)")
    parser.add_argument("--no-publish", action="store_true", help="발행 스킵")
    parser.add_argument("--config", default=str(ROOT / "config" / "my_job.json"),
                        help="설정 파일 경로")
    args = parser.parse_args()

    print_banner()

    style_key = args.style or select_style_interactive()
    topic     = args.topic or input_topic_interactive(style_key)

    confirm_and_run(style_key, topic, args.no_publish, args.config)


if __name__ == "__main__":
    main()
