"""
run_fallback.py — Anthropic API 크레딧 부족 시 폴백 카드뉴스 생성
====================================================================
• 이판사판(@2pan4pan) 디자인 시스템 v2.0 사용
• 16:9 (YouTube) + 9:16 (Shorts/Reels) 동시 생성
• 매일 수동 스크립트를 갱신하여 실행
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from news_card_maker import make_cards_ipsp, make_thumbnail_ipsp
from video_maker import make_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ── 오늘의 스크립트 (매일 업데이트) ──────────────────────────────────────────
# 최종 갱신: 2026-09-16
SCRIPT = {
    "style":  "card_news",
    "topic":  "9월 16일 이판사판 뉴스브리핑: 버스 파업·GTX·외교·성과급·청문회",
    "title":  "오늘의 이판사판\n2026년 9월 16일 수요일",
    "description": (
        "서울 버스 파업 극적 타결, GTX-C 착공, 이재명 대통령 중앙아시아 외교, "
        "SK하이닉스 성과급 재합의, 법무장관 후보자 청문회 공방, 가을 트윈데믹 경보 — "
        "오늘 꼭 알아야 할 핵심 뉴스 6가지를 이판사판이 정리했습니다. "
        "#이판사판 #뉴스브리핑 #2pan4pan #오늘의뉴스 #시사"
    ),
    "tags": ["이판사판", "뉴스브리핑", "2pan4pan", "오늘의뉴스", "시사", "9월16일"],
    "cards": [
        {
            "card_num": 1,
            "type": "cover",
            "headline": "오늘의 이판사판\n뉴스브리핑",
            "body": "2026년 9월 16일 수요일\n오늘 반드시 알아야 할 핵심 뉴스 6",
            "source": "이판사판 @2pan4pan",
        },
        {
            "card_num": 2,
            "type": "content",
            "category": "교통",
            "headline": "서울 버스 파업\n극적 타결",
            "body": "12시간 넘는 마라톤 협상 끝에 기본급 3.2% 인상 합의. 전면 파업 직전 노사가 극적으로 타결하며 시민 발이 묶일 위기를 피했다.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 3,
            "type": "content",
            "category": "개발",
            "headline": "GTX-C 노선\n본격 착공",
            "body": "덕정~삼성·수원~청량리 구간을 30분대로 연결하는 수도권 광역급행철도 C노선이 본격 착공. 개통 시 수도권 광역 교통망 대폭 개편 예상.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 4,
            "type": "content",
            "category": "외교",
            "headline": "이재명 대통령\n중앙아시아 5개국 릴레이 외교",
            "body": "이재명 대통령이 중앙아시아 5개국과 릴레이 정상회의를 개최해 자원·경제 협력을 논의. 에너지·인프라 분야 공동 프로젝트 협약 체결.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 5,
            "type": "content",
            "category": "경제",
            "headline": "SK하이닉스 성과급\n현금 50% + 자사주 50%",
            "body": "SK하이닉스 노사가 성과급 지급 방식을 기존 방식에서 현금 50%, 자사주 50% 병행 지급으로 재합의. 직원들의 장기 보상 체계 강화 기대.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 6,
            "type": "content",
            "category": "정치",
            "headline": "법무장관 후보자\n청문회 공방 격화",
            "body": "김승원 법무장관 후보자 인사청문회에서 수사·기소 분리 원칙과 가족 조합 의혹을 두고 여야 간 공방이 격화됐다. 야당, 자진 사퇴 압박.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 7,
            "type": "content",
            "category": "보건",
            "headline": "가을 트윈데믹 경보\n독감 + 코로나 동시 대비",
            "body": "방역 당국이 독감과 코로나19 동시 유행 '트윈데믹'에 대비해 조기 백신 접종을 권고. 환절기 기온 편차가 커 면역력 관리가 더욱 중요.",
            "source": "이판사판 2026.09.16",
        },
        {
            "card_num": 8,
            "type": "closing",
            "headline": "이판사판\n@2pan4pan",
            "body": "구독하고 매일\n핵심 뉴스 먼저 받아보세요!",
            "source": "이판사판.kr",
        },
    ],
}

# ── 출력 경로 ──────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = ROOT / "outputs" / f"ipsp_{ts}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'='*60}")
print(f"  이판사판 카드뉴스 폴백 생성기 v2.0")
print(f"  출력 경로: {OUTPUT_DIR}")
print(f"{'='*60}\n")

# ── 1단계: 16:9 카드 이미지 생성 ──────────────────────────────────────────
print("[1/5] 16:9 카드 이미지 생성 (1920×1080)...")
cards_169 = make_cards_ipsp(SCRIPT, OUTPUT_DIR, fmt="16:9")
print(f"      → {len(cards_169)}장 생성 완료")

# ── 2단계: 9:16 카드 이미지 생성 ──────────────────────────────────────────
print("[2/5] 9:16 카드 이미지 생성 (1080×1920)...")
cards_916 = make_cards_ipsp(SCRIPT, OUTPUT_DIR, fmt="9:16")
print(f"      → {len(cards_916)}장 생성 완료")

# ── 3단계: 썸네일 생성 ────────────────────────────────────────────────────
print("[3/5] 썸네일 생성 (1280×720)...")
thumb = make_thumbnail_ipsp(SCRIPT, OUTPUT_DIR)
print(f"      → {thumb}")

# ── 4단계: 16:9 영상 생성 ─────────────────────────────────────────────────
print("[4/5] 16:9 MP4 생성 (YouTube용)...")
cfg_video = {"media": {"seconds_per_card": 4}}
video_169 = make_video(cards_169, OUTPUT_DIR, cfg_video, as_shorts=False)
if video_169:
    print(f"      → {video_169}")
else:
    print("      → ffmpeg 없음, 영상 생성 건너뜀")

# ── 5단계: 9:16 Shorts 영상 생성 ──────────────────────────────────────────
print("[5/5] 9:16 MP4 생성 (Shorts/Reels용)...")
video_916 = make_video(cards_916, OUTPUT_DIR, cfg_video, as_shorts=True)
if video_916:
    print(f"      → {video_916}")
else:
    print("      → ffmpeg 없음, 영상 생성 건너뜀")

# ── 스크립트 저장 ──────────────────────────────────────────────────────────
(OUTPUT_DIR / "script.json").write_text(
    json.dumps(SCRIPT, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"\n{'='*60}")
print(f"  ✅ 생성 완료!")
print(f"  썸네일 : {thumb.name if thumb else '없음'}")
print(f"  16:9 카드: {len(cards_169)}장  |  9:16 카드: {len(cards_916)}장")
print(f"  영상(16:9): {video_169.name if video_169 else '없음'}")
print(f"  영상(9:16): {video_916.name if video_916 else '없음'}")
print(f"  전체 출력: {OUTPUT_DIR}")
print(f"{'='*60}\n")
