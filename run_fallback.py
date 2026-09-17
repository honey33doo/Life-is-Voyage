"""
run_fallback.py — Anthropic API 크레딧 부족 시 폴백 카드뉴스 생성
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
# 최종 갱신: 2026-09-17
SCRIPT = {
    "style":  "card_news",
    "topic":  "9월 17일 이판사판 뉴스브리핑: 연준 금리인상·코스피 급락·포스코 파업·서울선언·북한 배상",
    "title":  "오늘의 이판사판\n2026년 9월 17일 목요일",
    "description": (
        "미국 연준 3년 만의 금리인상으로 코스피 7천선 붕괴, 포스코·HD현대重 120시간 파업 돌입, "
        "한-중앙아시아 서울선언 채택, 북한 연락사무소 폭파 배상 판결, 추석 성수품 최대 50% 할인 — "
        "오늘 꼭 알아야 할 핵심 뉴스 6가지를 이판사판이 정리했습니다. "
        "#이판사판 #뉴스브리핑 #2pan4pan #오늘의뉴스 #시사"
    ),
    "tags": ["이판사판", "뉴스브리핑", "2pan4pan", "오늘의뉴스", "시사", "9월17일"],
    "cards": [
        {
            "card_num": 1,
            "type": "cover",
            "headline": "오늘의 이판사판\n뉴스브리핑",
            "body": "2026년 9월 17일 목요일\n오늘 반드시 알아야 할 핵심 뉴스 6",
            "source": "이판사판 @2pan4pan",
        },
        {
            "card_num": 2,
            "type": "content",
            "category": "경제",
            "headline": "연준 3년 만의 금리인상\n코스피 7천선 붕괴",
            "body": "미국 연준이 15~16일 FOMC에서 3년 만에 첫 금리 인상을 단행. 충격파로 코스피가 7천선 아래(6,909)로 추락. 삼성전자·SK하이닉스도 3~4% 급락. 한국은행도 기준금리 2.75%→3.00% 인상.",
            "source": "이판사판 2026.09.17",
        },
        {
            "card_num": 3,
            "type": "content",
            "category": "외교",
            "headline": "한-중앙아 서울선언 채택\n신 실크로드 이니셔티브",
            "body": "이재명 대통령이 중앙아시아 5개국 정상회의를 마무리하며 서울선언을 공동 채택. 향후 30년 협력 틀 구축, '신 실크로드' 이니셔티브로 에너지·인프라 공동 프로젝트 착수.",
            "source": "이판사판 2026.09.17",
        },
        {
            "card_num": 4,
            "type": "content",
            "category": "노동",
            "headline": "포스코·HD현대重\n120시간 파업 돌입",
            "body": "포스코 노조가 열연 라인을 겨냥한 120시간 파업에 돌입. HD현대중공업도 부분 파업 확대. 426억 달러 수주 물량의 납기 차질 우려로 수출 경보 발령.",
            "source": "이판사판 2026.09.17",
        },
        {
            "card_num": 5,
            "type": "content",
            "category": "정치",
            "headline": "국회 본회의 개최\n법무·국방 장관 법사위",
            "body": "여야가 오후 2시 국회 본회의를 개최. 국방부 장관이 법사위 전체회의에 참석해 방위사업 현안을 보고. 외교부 1·2차관도 외통위에서 중앙아시아 외교 성과를 보고할 예정.",
            "source": "이판사판 2026.09.17",
        },
        {
            "card_num": 6,
            "type": "content",
            "category": "대북",
            "headline": "법원, 북한에 배상 명령\n연락사무소 폭파 44.6억원",
            "body": "서울 법원이 2020년 북한의 남북공동연락사무소 폭파에 대해 북한 당국에 44.6억원을 배상하라고 판결. 국제법상 선례 없는 대북 배상 판결로 주목.",
            "source": "이판사판 2026.09.17",
        },
        {
            "card_num": 7,
            "type": "content",
            "category": "민생",
            "headline": "추석 성수품 최대 50% 할인\n43조 명절자금 풀린다",
            "body": "정부가 추석 민생 안정을 위해 성수품 18.3만 톤을 공급하고 최대 50% 할인 행사를 진행. 43.4조 원 규모 명절 자금도 시중에 공급해 유동성 확보 지원.",
            "source": "이판사판 2026.09.17",
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

print("[1/5] 16:9 카드 이미지 생성 (1920×1080)...")
cards_169 = make_cards_ipsp(SCRIPT, OUTPUT_DIR, fmt="16:9")
print(f"      → {len(cards_169)}장 생성 완료")

print("[2/5] 9:16 카드 이미지 생성 (1080×1920)...")
cards_916 = make_cards_ipsp(SCRIPT, OUTPUT_DIR, fmt="9:16")
print(f"      → {len(cards_916)}장 생성 완료")

print("[3/5] 썸네일 생성 (1280×720)...")
thumb = make_thumbnail_ipsp(SCRIPT, OUTPUT_DIR)
print(f"      → {thumb}")

print("[4/5] 16:9 MP4 생성 (YouTube용)...")
cfg_video = {"media": {"seconds_per_card": 4}}
video_169 = make_video(cards_169, OUTPUT_DIR, cfg_video, as_shorts=False)
if video_169:
    print(f"      → {video_169}")
else:
    print("      → ffmpeg 없음, 영상 생성 건너뜀")

print("[5/5] 9:16 MP4 생성 (Shorts/Reels용)...")
video_916 = make_video(cards_916, OUTPUT_DIR, cfg_video, as_shorts=True)
if video_916:
    print(f"      → {video_916}")
else:
    print("      → ffmpeg 없음, 영상 생성 건너뜀")

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
