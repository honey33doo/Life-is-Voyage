# 이판사판(@2pan4pan) 카드뉴스 자동화 스킬
> **최종 업데이트**: 2026-09-16 | **버전**: 2.0.0

---

## 스킬 개요

온라인 언론 플랫폼 "이판사판"의 카드뉴스를 자동 생성하는 스킬.  
Claude Cowork 스케줄 세션에서 매일 자동 실행되며, Anthropic API 사용 가능 여부에 따라 두 가지 경로로 분기한다.

```
[전체 파이프라인]

  Google Drive API Key
        ↓
  GitHub repo pull (honey33doo/Life-is-Voyage)
        ↓
  경로 A (API 있음): prompt_pipeline.py → Claude API → 자동 스크립트
  경로 B (API 없음): run_fallback.py   → 수동 스크립트 직접 주입
        ↓
  news_card_maker.py (이판사판 렌더러)
        ↓
  16:9 카드 8장 + 9:16 카드 8장 + 썸네일
        ↓
  ffmpeg → video_16x9.mp4 / video_9x16_shorts.mp4
        ↓
  SendUserFile → PushNotification
```

---

## 폴더 구조

```
cardnews-auto/
├── src/
│   ├── news_card_maker.py      ← 이판사판 렌더러 (v2.0, 메인)
│   ├── card_maker.py           ← 구버전 렌더러 (레거시)
│   ├── video_maker.py          ← ffmpeg 영상 생성
│   ├── prompt_pipeline.py      ← Claude API 스크립트 생성
│   ├── publisher.py            ← YouTube/Blog 발행
│   ├── content_styles.py       ← 콘텐츠 스타일 정의
│   └── config_loader.py        ← 설정 및 API 키 로드
├── config/
│   ├── my_job.json             ← 운영 설정
│   └── sample_job.json         ← 설정 템플릿
├── outputs/                    ← 생성 결과물 (자동 생성)
├── run_fallback.py             ← API 크레딧 없을 때 폴백
├── SKILL.md                    ← 이 파일
└── .env                        ← API 키 (git 제외)
```

---

## 폰트 시스템

경로: `/usr/share/fonts/truetype/2pan4pan/`

| 폰트 파일 | 용도 | 적용 부위 |
|---|---|---|
| `GmarketSansTTFBold.ttf` | 브랜드/로고 | 이판사판 로고, 헤더 |
| `Hakgyoansim_PosterB.ttf` | 헤드라인 | 메인 제목 (임팩트·포스터형) |
| `paybooc_ExtraBold.ttf` | 서브헤드 | 카드 번호 뱃지, 강조 |
| `NeoHyundai_B.ttf` | 본문 | 카드 본문, 설명 텍스트 |
| `Cafe24Dangdanghae-v2.0.ttf` | 속보 배너 | 빨간 속보 태그 |
| `KoPub_Dotum_Bold.ttf` | 출처/날짜 | 하단 바, 캡션 |
| `H2HDRM.ttf` | 장식/배경 | 대형 배경 숫자 |
| `samlip-creamy-white-regular.ttf` | 예비/소프트 | 필요 시 추가 활용 |

**장평·자간 정책**
- 헤드라인: 장평 100%, 자간 -30 (Tight — 신문 스타일)
- 본문: 장평 100%, 자간 -10 (Normal)
- 로고: 장평 100%, 자간 +20 (Loose — 브랜드 각인)

---

## 출력 포맷

| 포맷 | 해상도 | 용도 |
|---|---|---|
| 16:9 카드 | 1920 × 1080 px | YouTube 기본 송출 |
| 9:16 카드 | 1080 × 1920 px | YouTube Shorts / Instagram Reels |
| 썸네일 | 1280 × 720 px | YouTube 썸네일 |
| video_16x9.mp4 | 1920×1080, H.264 | YouTube 업로드 |
| video_9x16_shorts.mp4 | 1080×1920, H.264 | Shorts/Reels 업로드 |

---

## 브랜드 컬러 시스템

```python
BRAND = {
    "bg_dark":     (8,  10,  20),     # 최심 다크 배경   #080A14
    "accent_red":  (220, 38,  38),    # 속보 빨강        #DC2626
    "accent_gold": (251, 191, 36),    # 하이라이트 골드  #FBBF24
    "accent_cyan": (6,  182, 212),    # 링크·핸들 시안   #06B6D4
    "text_white":  (255, 255, 255),   # 메인 텍스트
    "text_silver": (203, 213, 225),   # 본문 텍스트
    "text_muted":  (100, 116, 139),   # 보조 정보
}
```

---

## 실행 방법

### 1. 폴백 실행 (API 없을 때)
```bash
cd /home/claude/cardnews-auto
python run_fallback.py
```

### 2. 전체 AI 파이프라인 (API 있을 때)
```bash
python src/prompt_pipeline.py \
  --topic "오늘의 주요 정치 이슈" \
  --style card_news \
  --no-publish
```

### 3. 이판사판 렌더러 단독 실행
```python
from src.news_card_maker import make_cards_ipsp, make_thumbnail_ipsp
import json
from pathlib import Path

script = json.loads(Path("outputs/.../script.json").read_text())
outdir = Path("outputs/test_run")
outdir.mkdir(exist_ok=True)

cards_169 = make_cards_ipsp(script, outdir, fmt="16:9")
cards_916 = make_cards_ipsp(script, outdir, fmt="9:16")
thumb     = make_thumbnail_ipsp(script, outdir)
```

---

## 배경 효과 구현 원리

실제 배경 영상 없이 **5겹 레이어 합성**으로 방송 블러 배경 시뮬레이션:

```
Layer 1: 딥 다크 베이스 (#080A14)
Layer 2: 컬러 노이즈  ← 시네마틱 그레인
Layer 3: 방사형 그라데이션 ← 중앙 스팟라이트
Layer 4: 대각선 라이트빔 ← 시네마틱 레이
Layer 5: 비네트 ← 가장자리 어두움
+ 최종 Gaussian Blur (radius=1.5) ← 아웃포커스
```

---

## Anthropic API 크레딧 복구 절차

1. https://console.anthropic.com → Plans & Billing
2. 크레딧 충전 ($5+)
3. `.env` 파일 확인 (`ANTHROPIC_API_KEY=sk-ant-...`)
4. 다음 스케줄 실행 시 자동으로 경로 A (AI 스크립트 생성)로 전환

---

## 향후 개선 계획

- [ ] 실제 유튜브 영상 구간을 배경으로 사용 (Higgsfield MCP 연동)
- [ ] 카드별 AI 이미지 생성 (Higgsfield generate_image)
- [ ] YouTube API 자동 업로드 (publisher.py 완성)
- [ ] Naver Blog / Tistory 자동 발행
- [ ] 다국어 지원 (영문 카드뉴스)
