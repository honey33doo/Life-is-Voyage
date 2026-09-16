"""
tistory_pub.py
==============
티스토리 Open API 로 게시물을 올린다.

설정 방법:
  1. https://www.tistory.com/guide/api/manage/register → 앱 등록
  2. OAuth 2.0 액세스 토큰 발급
     (브라우저에서: https://www.tistory.com/oauth/authorize?client_id=<ID>&redirect_uri=<URI>&response_type=code)
  3. config/my_job.json 의 credentials.tistory_access_token 에 입력
"""

import logging
from typing import Optional
import requests

logger = logging.getLogger("cardnews.tistory")

TISTORY_POST_API = "https://www.tistory.com/apis/post/write"


def post_article(
    title: str,
    content_html: str,
    tags: list[str],
    cfg: dict,
) -> Optional[str]:
    """
    티스토리에 게시물을 발행한다.
    반환값: post_id
    """
    pub_cfg = cfg.get("publish", {}).get("tistory", {})
    access_token = cfg.get("credentials", {}).get("tistory_access_token", "").strip()

    if not pub_cfg.get("enabled", False):
        logger.info("티스토리 발행 비활성화 — 스킵")
        return None

    if not access_token:
        logger.warning(
            "티스토리 액세스 토큰이 없습니다.\n"
            "config/my_job.json 의 credentials.tistory_access_token 을 입력하세요."
        )
        return None

    blog_name = cfg.get("credentials", {}).get("tistory_blog_name", "")
    if not blog_name:
        logger.error("티스토리 블로그 이름(credentials.tistory_blog_name)이 없습니다.")
        return None

    category_id = pub_cfg.get("category_id", "0")
    tags_str = ",".join(tags[:10])

    try:
        resp = requests.post(
            TISTORY_POST_API,
            params={
                "access_token": access_token,
                "output": "json",
                "blogName": blog_name,
                "title": title,
                "content": content_html,
                "visibility": 3,  # 3=공개
                "categoryId": category_id,
                "tag": tags_str,
                "acceptComment": 1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        tistory_item = data.get("tistory", {})
        post_id = tistory_item.get("postId", "")
        url = tistory_item.get("url", "")
        logger.info(f"티스토리 게시 완료: {url}")
        return str(post_id)
    except Exception as e:
        logger.error(f"티스토리 게시 실패: {e}")
        return None
