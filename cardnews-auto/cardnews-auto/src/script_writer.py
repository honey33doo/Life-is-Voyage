"""
script_writer.py
================
Anthropic Claude API 를 호출해 카드뉴스 스크립트와 기사를 자동 생성한다.
"""

import json
import logging
from typing import Optional
import anthropic

logger = logging.getLogger("cardnews.script_writer")

# ────────────────────────────────────────────────
# 카드뉴스 스크립트 생성
# ────────────────────────────────────────────────

CARDNEWS_SYSTEM_PROMPT = """당신은 한국의 전문 카드뉴스 작가입니다.
주어진 소스 자료를 바탕으로 SNS 카드뉴스 스크립트를 작성합니다.

규칙:
- 각 카드는 제목(최대 20자)과 본문(최대 80자, 2-3줄)으로 구성
- 첫 번째 카드는 커버(훅/제목 카드)
- 마지막 카드는 출처 및 채널 안내
- 사실에 기반하며 출처를 반드시 표기
- 독자가 3초 안에 관심을 갖도록 커버 작성
- JSON 형식으로만 반환"""

CARDNEWS_USER_TEMPLATE = """다음 소스 자료를 바탕으로 카드뉴스 {card_count}장 스크립트를 작성하세요.

주제: {main_topic}
분위기: {tone}
스타일: {style}

소스 자료:
{sources_text}

다음 JSON 형식으로 반환하세요:
{{
  "title": "전체 제목 (YouTube/SNS 제목으로 사용)",
  "description": "영상/포스트 설명문 (300자 이내)",
  "tags": ["태그1", "태그2", ...],
  "cards": [
    {{
      "card_num": 1,
      "type": "cover",
      "headline": "강렬한 훅 문구",
      "body": "부제목 또는 핵심 요약",
      "source": ""
    }},
    ...
    {{
      "card_num": {card_count},
      "type": "closing",
      "headline": "구독/팔로우 CTA",
      "body": "채널명 및 출처 안내",
      "source": "출처: [원본 채널/기사명]"
    }}
  ]
}}"""


ARTICLE_SYSTEM_PROMPT = """당신은 한국의 전문 기자입니다.
주어진 소스 자료를 바탕으로 스트레이트 보도 기사 또는 반박성 박스 기사를 작성합니다.

규칙:
- 5W1H 원칙 준수
- 사실과 의견을 명확히 구분
- 출처 반드시 표기
- 선정적이지 않고 객관적 어조
- 네이버 블로그/티스토리 SEO 최적화"""

ARTICLE_USER_TEMPLATE = """다음 소스 자료를 바탕으로 {article_type} 기사를 작성하세요.

주제: {main_topic}
기사 유형: {article_type_desc}

소스 자료:
{sources_text}

다음 JSON 형식으로 반환하세요:
{{
  "headline": "기사 제목",
  "sub_headline": "부제목",
  "lead": "리드 문단 (핵심 내용 1-2문장)",
  "body": "본문 (마크다운 허용, 출처 인용 포함)",
  "tags": ["태그1", "태그2"],
  "meta_description": "SEO 메타 설명 (150자)"
}}"""


# ────────────────────────────────────────────────
# Claude API 호출
# ────────────────────────────────────────────────

def _call_claude(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 4096,
) -> str:
    """Claude API를 호출하고 텍스트 응답을 반환한다."""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _sources_to_text(sources: list[dict]) -> str:
    """소스 목록을 텍스트로 변환한다."""
    lines = []
    for i, src in enumerate(sources, 1):
        lines.append(
            f"[{i}] {src.get('title', '')} | {src.get('channel', '')} | {src.get('url', '')}\n"
            f"    {src.get('description', '')[:200]}"
        )
    return "\n\n".join(lines)


def _parse_json_response(raw: str) -> dict:
    """Claude 응답에서 JSON을 추출한다."""
    # ```json ... ``` 블록 제거
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(raw)


# ────────────────────────────────────────────────
# 퍼블릭 인터페이스
# ────────────────────────────────────────────────

def generate_cardnews_script(
    cfg: dict, sources: list[dict], api_key: str
) -> dict:
    """카드뉴스 스크립트를 생성하고 dict 로 반환한다."""
    topic = cfg["topic"]
    content = cfg["content"]

    style_map = {
        "achievement": "성과 강조형 (긍정적, 팩트 중심)",
        "rebuttal": "반박형 (과거 발언 인용, 팩트 대조)",
        "expose": "고발형 (문제점 지적, 증거 중심)",
        "informative": "정보 전달형 (중립적, 요약 중심)",
    }
    tone_map = {
        "informative": "정보 전달, 중립적",
        "informative_positive": "긍정적, 성과 중심",
        "critical": "비판적, 문제 제기",
    }

    user_prompt = CARDNEWS_USER_TEMPLATE.format(
        card_count=content.get("card_count", 8),
        main_topic=topic["main"],
        tone=tone_map.get(topic.get("tone", "informative"), topic.get("tone", "")),
        style=style_map.get(topic.get("style", "informative"), topic.get("style", "")),
        sources_text=_sources_to_text(sources),
    )

    logger.info("카드뉴스 스크립트 생성 중...")
    raw = _call_claude(api_key, CARDNEWS_SYSTEM_PROMPT, user_prompt)
    script = _parse_json_response(raw)
    logger.info(f"스크립트 생성 완료: {len(script.get('cards', []))}장")
    return script


def generate_article(
    cfg: dict, sources: list[dict], api_key: str
) -> Optional[dict]:
    """기사를 생성하고 dict 로 반환한다. 기사 생성이 비활성화된 경우 None."""
    content = cfg["content"]
    if not content.get("include_article", False):
        return None

    article_type = content.get("article_type", "straight")
    type_desc_map = {
        "straight": "스트레이트 보도 (5W1H, 사실 중심)",
        "rebuttal": "반박 박스 기사 (과거 발언 vs 현재 팩트)",
        "expose": "고발성 기사 (문제점 폭로, 증거 인용)",
    }

    user_prompt = ARTICLE_USER_TEMPLATE.format(
        article_type=article_type,
        article_type_desc=type_desc_map.get(article_type, article_type),
        main_topic=cfg["topic"]["main"],
        sources_text=_sources_to_text(sources),
    )

    logger.info(f"기사 생성 중 ({article_type})...")
    raw = _call_claude(api_key, ARTICLE_SYSTEM_PROMPT, user_prompt)
    article = _parse_json_response(raw)
    logger.info("기사 생성 완료")
    return article
