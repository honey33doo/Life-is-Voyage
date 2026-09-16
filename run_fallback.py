"""
run_fallback.py - API 크레딧 부족 시 레포 렌더러로 폴백 카드뉴스 생성
"""
import json, logging, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
from card_maker import make_cards, make_thumbnail
from video_maker import make_video

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)])

SCRIPT = {
    "style": "card_news",
    "topic": "이재명 대통령 18일 기자회견: 공소취소·파병·개헌 핵심 정리",
    "title": "이재명 대통령 18일 기자회견\n공소취소·파병·개헌 핵심 정리",
    "description": ("이재명 대통령이 2026년 9월 18일 청와대에서 기자회견을 열고 "
        "세 가지 주요 현안 — 공소취소·파병·연임개헌 — 에 대한 공식 입장을 밝힐 예정입니다. "
        "이 영상에서는 세 쟁점의 배경과 각 세력 입장을 핵심만 짚어드립니다. "
        "#이재명 #기자회견 #공소취소 #파병 #개헌 #데이뉴스"),
    "tags": ["이재명","기자회견","공소취소","파병","개헌","시사","데이뉴스"],
    "cards": [
        {"card_num":1,"type":"cover","headline":"이재명 대통령\n18일 기자회견","body":"공소취소 · 파병 · 개헌\n세 가지 핵심 현안 입장 발표","source":"데이뉴스 2026.09.16"},
        {"card_num":2,"type":"content","headline":"왜 지금 기자회견?","body":"취임 이후 최대 정치적 현안이 동시에 쏟아지며 여야 모두 대통령의 공식 입장을 요구하는 상황. 18일 청와대에서 전면 발표 예정.","source":"서울신문 2026.09.16"},
        {"card_num":3,"type":"content","headline":"① 공소취소 논란","body":"전직 대통령 관련 공소 취소 요구가 제기됐다. 야당 일부는 '사법 쿠데타'라며 반발하고 여당은 '사법 정상화'라고 맞서는 중.","source":"경향신문·한국일보"},
        {"card_num":4,"type":"content","headline":"② 파병 문제","body":"우크라이나 및 중동 지역 파병 요청에 대한 한국 정부의 첫 공식 입장 표명. 국제사회 압박 vs 국내 여론 간 균형점이 관건.","source":"파이낸셜뉴스 2026.09.15"},
        {"card_num":5,"type":"content","headline":"③ 연임 개헌","body":"현행 5년 단임제 → 4년 중임제 개헌 추진 여부. 개헌 추진 시 2028년 대선 일정에 직접적 영향을 미치는 초대형 현안.","source":"네이트뉴스 2026.09.15"},
        {"card_num":6,"type":"content","headline":"여야 입장 충돌","body":"여당: 신속 개헌·파병 검토 지지\n야당: 공소취소 철회·파병 반대\n핵심 변수는 대통령이 세 현안을 연계하느냐 분리하느냐.","source":""},
        {"card_num":7,"type":"content","headline":"18일 이후 전망","body":"기자회견 내용에 따라 정국은 '개헌 협상 모드' 또는 '사법·외교 갈등 심화'로 갈린다. 국회 회기 중 처리 가능 여부가 최대 관전 포인트.","source":""},
        {"card_num":8,"type":"closing","headline":"📰 데이뉴스","body":"구독하고 정치 이슈\n가장 먼저 받아보세요!","source":"daenews.kr"},
    ],
}
CFG = {"media":{"card_format":"1080x1080","card_style":"dark_modern","brand_name":"데이뉴스","brand_color_primary":"#1E3A5F","brand_color_accent":"#F4A300","watermark":True,"seconds_per_card":4}}

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = ROOT / "outputs" / f"card_news_fallback_{ts}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"[1/3] 카드 이미지 생성 -> {OUTPUT_DIR}")
card_paths = make_cards(SCRIPT, CFG, OUTPUT_DIR)
print("[2/3] 썸네일 생성")
thumb_path = make_thumbnail(SCRIPT, CFG, OUTPUT_DIR)
print("[3/3] 비디오 생성")
video_path = make_video(card_paths, OUTPUT_DIR, CFG, as_shorts=False)
(OUTPUT_DIR / "script.json").write_text(json.dumps(SCRIPT, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n완료!\n  썸네일: {thumb_path}\n  카드:   {OUTPUT_DIR}/cards/\n  영상:   {video_path}")