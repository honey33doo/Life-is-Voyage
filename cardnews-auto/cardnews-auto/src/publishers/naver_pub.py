"""
naver_pub.py
============
네이버 블로그 API 로 게시물을 올린다.
네이버 Developer Center → 애플리케이션 등록 → Blog 권한 필요.

설정 방법:
  1. https://developers.naver.com → 애플리케이션 등록
  2. Blog 서비스 선택
  3. Client ID / Client Secret 발급
  4. config/my_job.json 의 credentials 에 입력
"""

import logging
from typing import Optional
import requests

logger = logging.getLogger("cardnews.naver")

NAVER_BLOG_API = "https://openapi.naver.com/blog/writePost.json"


def post_article(
    title: str,
    content_html: str,
    tags: list[str],
    cfg: dict,
) -> Optional[str]:
    """
    네이버 블로그에 HTML 게시물을 작성한다.
    반환값: 포스트 ID (성공 시)
    """
    pub_cfg = cfg.get("publish", {}).get("naver_blog", {})
    creds = cfg.get("credentials", {})
    client_id = creds.get("naver_client_id", "").strip()
    client_secret = creds.get("naver_client_secret", "").strip()

    if not pub_cfg.get("enabled", False):
        logger.info("네이버 블로그 발행 비활성화 — 스킵")
        return None

    if not client_id or not client_secret:
        logger.warning(
            "네이버 API 키가 없습니다.\n"
            "config/my_job.json 의 credentials 에 naver_client_id/naver_client_secret 을 입력하세요."
        )
        return None

    category = pub_cfg.get("category", "")
    tags_str = ",".join(tags[:10])

    try:
        resp = requests.post(
            NAVER_BLOG_API,
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "title": title,
                "contents": content_html,
                "tags": tags_str,
                "categoryNo": category,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        post_id = data.get("postId", data.get("logNo", ""))
        logger.info(f"네이버 블로그 게시 완료: post_id={post_id}")
        return str(post_id)
    except Exception as e:
        logger.error(f"네이버 블로그 게시 실패: {e}")
        return None


def article_to_html(article: dict, card_image_paths: list = None) -> str:
    """
    기사 dict 를 네이버 블로그용 HTML 로 변환한다.
    이미지는 base64 또는 img 태그로 삽입.
    """
    headline = article.get("headline", "")
    sub = article.get("sub_headline", "")
    lead = article.get("lead", "")
    body = article.get("body", "")
    tags = article.get("tags", [])

    # 마크다운 → 간단 HTML 변환
    body_html = body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    body_html = f"<p>{body_html}</p>"

    html = f"""<div style="font-family: 'Nanum Gothic', sans-serif; max-width: 800px; margin: 0 auto; line-height: 1.8;">
<h1 style="color: #1E3A5F; font-size: 24px; border-bottom: 3px solid #F4A300; padding-bottom: 10px;">{headline}</h1>
{f'<h2 style="color: #555; font-size: 16px;">{sub}</h2>' if sub else ''}
<div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #F4A300; margin: 20px 0;">
  <strong>📌 핵심 요약</strong><br>{lead}
</div>
{body_html}
<div style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
  태그: {', '.join('#' + t for t in tags)}
</div>
</div>"""
    return html
