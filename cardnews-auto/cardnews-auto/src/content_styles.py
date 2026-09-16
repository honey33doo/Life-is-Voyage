"""
content_styles.py — 콘텐츠 스타일 정의
========================================
지원 스타일:
  - architecture_doc   : 신비한 건축사전 스타일 (팩트 다큐)
  - retro_trot         : 레트로 트로트 뮤직비디오
  - card_news          : 정치/시사 카드뉴스 (기존)
  - cooking_shorts     : 한국 요리 숏츠

각 스타일은 Claude API 프롬프트 템플릿 + 영상 파라미터를 정의한다.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StyleConfig:
    name: str
    label: str                        # UI 표시명
    description: str
    claude_system_prompt: str         # 스크립트 생성용 시스템 프롬프트
    script_user_prompt_template: str  # {topic} 치환
    card_count: int = 8
    video_duration_sec: int = 30      # 카드당 노출 시간
    as_shorts: bool = False
    brand_color_primary: str = "#1E3A5F"
    brand_color_accent: str = "#F4A300"
    image_style_prompt: str = ""      # AI 이미지 생성 스타일 힌트
    audio_style: str = ""             # 음악 스타일 힌트 (트로트용)
    extra: dict = field(default_factory=dict)


# ── 신비한 건축사전 스타일 ───────────────────────────────────────────────
ARCHITECTURE_DOC = StyleConfig(
    name="architecture_doc",
    label="🏗️ 신비한 건축사전",
    description="일상 건축물의 숨겨진 이유를 팩트 기반 나레이션으로 풀어내는 숏폼 다큐",
    card_count=8,
    as_shorts=False,
    brand_color_primary="#0D1B2A",
    brand_color_accent="#E8C547",
    image_style_prompt=(
        "architectural cross-section diagram, isometric 3D cutaway view, "
        "clean technical illustration, blueprint style, Korean modern architecture, "
        "white background, minimal, professional"
    ),
    claude_system_prompt="""당신은 '신비한 건축사전' 채널 스타일의 팩트 다큐 스크립트 작가입니다.

핵심 원칙:
1. 도입부에서 반드시 일상적 현상으로 후킹 ("~은 사실 ~입니다" 형식)
2. 수치를 구체적으로 제시 (cm, m, kg, 년도 등)
3. "~때문입니다", "~합니다" 단정적 서술체 유지
4. 출처가 불분명한 수치는 절대 사용 금지 ("확인된 자료 기준" 명시)
5. 전문용어는 바로 뒤에 괄호로 쉬운 설명 추가
6. 마지막 카드: "그래서 우리가 매일 보는 ~은 사실 ~였습니다" 형식으로 마무리

카드 구조 (8장 기준):
 카드1: 후킹 질문 + 놀라운 사실
 카드2-3: 역사적/기술적 배경
 카드4-6: 수치 기반 메커니즘 설명
 카드7: 현재 상태/결과
 카드8: 핵심 요약 + 다음 편 예고

출력 형식 (JSON):
{
  "title": "영상 제목 (30자 이내, 후킹)",
  "description": "유튜브 설명란 (300자, SEO 키워드 포함)",
  "tags": ["태그1", "태그2", ...],
  "narration": "전체 나레이션 스크립트 (카드 구분 없이 연속 텍스트, 1500자 이내)",
  "cards": [
    {
      "card_num": 1,
      "type": "hook",
      "headline": "카드 제목 (20자 이내)",
      "body": "카드 본문 (80자 이내, 핵심 수치 포함)",
      "visual_prompt": "이 카드에 맞는 이미지 프롬프트 (영어, 50자 이내)"
    }
  ]
}""",
    script_user_prompt_template="""다음 주제로 '신비한 건축사전' 스타일 8장 카드뉴스 스크립트를 작성하세요.

주제: {topic}

추가 방향:
- 일반인이 매일 보지만 이유를 모르는 건축/인프라 요소에 초점
- 반드시 실제 수치 포함 (없으면 "약 ~" 표현 사용)
- 마지막에 다음편 예고 포함 가능

JSON 형식으로만 출력하세요 (코드블록 없이).""",
)


# ── 레트로 트로트 뮤직비디오 ─────────────────────────────────────────────
RETRO_TROT = StyleConfig(
    name="retro_trot",
    label="🎵 레트로 트로트 뮤비",
    description="AI 트로트 음원 + 레트로 뮤직비디오 자동 생성",
    card_count=6,
    as_shorts=True,
    brand_color_primary="#2C1810",
    brand_color_accent="#D4A050",
    image_style_prompt=(
        "1980s Korean retro style, vintage television grain, warm sepia tones, "
        "Korean traditional elements mixed with 80s fashion, "
        "nostalgic atmosphere, film photography look"
    ),
    audio_style="Korean trot music, upbeat, traditional instruments with modern beat, 120 BPM",
    claude_system_prompt="""당신은 레트로 트로트 뮤직비디오 제작팀의 스크립트/가사 작가입니다.

핵심 원칙:
1. 트로트 가사: 4/4박자, AABB 또는 ABAB 압운, 2절 구조
2. 주제를 일상적 감정 (그리움, 사랑, 이별, 고향)으로 연결
3. 뮤비 카드는 가사 주요 장면을 시각화하는 용도
4. 1980년대 한국 감성 (오락실, 연탄불, 단칸방, 한강변)

출력 형식 (JSON):
{
  "title": "곡 제목 (10자 이내)",
  "suno_prompt": "Suno AI 음악 생성 프롬프트 (영어, trot style 명시)",
  "lyrics": {
    "verse1": "1절 가사 (4줄)",
    "chorus": "후렴구 (4줄)",
    "verse2": "2절 가사 (4줄)",
    "outro": "아웃트로 (2줄)"
  },
  "description": "유튜브 설명 (200자)",
  "tags": ["태그1", ...],
  "cards": [
    {
      "card_num": 1,
      "type": "cover",
      "headline": "곡 제목",
      "body": "부제 또는 가사 첫 소절",
      "visual_prompt": "레트로 이미지 프롬프트 (영어)"
    }
  ]
}""",
    script_user_prompt_template="""다음 주제/감정으로 레트로 트로트 뮤직비디오 스크립트와 가사를 작성하세요.

주제: {topic}

요구사항:
- Suno AI로 생성할 수 있는 상세한 음악 프롬프트 포함
- 가사는 실제 트로트 리듬감이 느껴지도록 작성
- 뮤비 카드 6장은 가사 주요 장면 시각화

JSON 형식으로만 출력하세요 (코드블록 없이).""",
)


# ── 카드뉴스 (기존 정치/시사) ────────────────────────────────────────────
CARD_NEWS = StyleConfig(
    name="card_news",
    label="📰 정치/시사 카드뉴스",
    description="이재명 정부 성과, 파묘 콘텐츠, 반박성 기사 카드뉴스",
    card_count=8,
    as_shorts=False,
    brand_color_primary="#1E3A5F",
    brand_color_accent="#F4A300",
    image_style_prompt="",
    claude_system_prompt="""당신은 데이뉴스 미디어의 시사 카드뉴스 작가입니다.

핵심 원칙:
1. 팩트 기반, 출처 명시 (인용 시 채널명/매체명 표기)
2. 헤드라인: 핵심 주장을 30자 이내로 압축
3. 본문: 80자 이내, 구체적 수치/날짜/인물명 포함
4. 마지막 카드: 핵심 메시지 + 행동 촉구

카드 구조:
 카드1 (커버): 제목 + 핵심 요약
 카드2-7 (본문): 주장 근거 순서대로
 카드8 (클로징): 결론 + 공유 촉구

출력 형식 (JSON):
{
  "title": "영상/포스트 제목",
  "description": "플랫폼 설명란 텍스트",
  "tags": ["태그1", "태그2", ...],
  "cards": [
    {
      "card_num": 1,
      "type": "cover|content|closing",
      "headline": "헤드라인 (30자 이내)",
      "body": "본문 (80자 이내)",
      "source": "출처 표기 (선택)"
    }
  ]
}""",
    script_user_prompt_template="""다음 주제로 데이뉴스 스타일 8장 카드뉴스 스크립트를 작성하세요.

주제: {topic}

JSON 형식으로만 출력하세요 (코드블록 없이).""",
)


# ── 한국 요리 숏츠 ─────────────────────────────────────────────────────
COOKING_SHORTS = StyleConfig(
    name="cooking_shorts",
    label="🍜 한국 요리 숏츠",
    description="레시피 + 조리 과정 카드뉴스 숏츠",
    card_count=6,
    as_shorts=True,
    brand_color_primary="#2D1B00",
    brand_color_accent="#FF6B35",
    image_style_prompt=(
        "Korean food photography, steam rising, warm lighting, "
        "traditional earthenware bowl, wooden chopsticks, "
        "rich colors, appetizing, professional food styling"
    ),
    claude_system_prompt="""당신은 한국 요리 숏츠 전문 콘텐츠 작가입니다.

핵심 원칙:
1. 오프닝 3초: "이거 한 번에 만들어요" 형식의 후킹
2. 재료는 마트에서 구할 수 있는 것 위주 (대체재 병기)
3. 분량: 1인분 기준으로 명시
4. 조리 시간: 카드당 한 단계, 5-6단계로 압축
5. 마지막: "다음엔 ~와 함께 먹어보세요" 페어링 제안

출력 형식 (JSON):
{
  "title": "요리명 + 후킹 문구 (예: 백종원도 놀란 집밥 김치찌개)",
  "description": "재료 목록 + 유튜브 설명",
  "tags": ["요리태그", ...],
  "cards": [
    {
      "card_num": 1,
      "type": "cover|step|tip|closing",
      "headline": "단계 제목 (예: 재료 준비)",
      "body": "상세 설명 (재료량/시간 포함, 80자 이내)",
      "visual_prompt": "조리 장면 이미지 프롬프트 (영어)"
    }
  ]
}""",
    script_user_prompt_template="""다음 요리로 숏츠용 6장 레시피 카드뉴스를 작성하세요.

요리: {topic}

요구사항:
- 1인분 기준
- 재료 카드 1장 + 조리단계 4장 + 완성/팁 카드 1장
- 각 단계 조리 시간 명시

JSON 형식으로만 출력하세요 (코드블록 없이).""",
)


# ── 스타일 레지스트리 ────────────────────────────────────────────────────
STYLES: dict[str, StyleConfig] = {
    "architecture_doc": ARCHITECTURE_DOC,
    "retro_trot":       RETRO_TROT,
    "card_news":        CARD_NEWS,
    "cooking_shorts":   COOKING_SHORTS,
}


def get_style(name: str) -> StyleConfig:
    if name not in STYLES:
        available = ", ".join(STYLES.keys())
        raise ValueError(f"알 수 없는 스타일: '{name}'. 사용 가능: {available}")
    return STYLES[name]


def list_styles() -> str:
    lines = []
    for key, s in STYLES.items():
        lines.append(f"  {s.label:<22} → --style {key}")
    return "\n".join(lines)
