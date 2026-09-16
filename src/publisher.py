"""
publisher.py
============
모든 플랫폼 발행을 조율하는 라우터.
require_approval=true 이면 발행 단계를 건너뛴다.
"""

import logging
from pathlib import Path
from typing import Optional

from publishers.youtube_pub import upload_video
from publishers.instagram_pub import upload_carousel
from publishers.naver_pub import post_article as naver_post, article_to_html
from publishers.tistory_pub import post_article as tistory_post

logger = logging.getLogger("cardnews.publisher")


def publish_all(
    script: dict,
    article: Optional[dict],
    video_path: Optional[Path],
    thumbnail_path: Optional[Path],
    card_paths: list[Path],
    cfg: dict,
    no_publish: bool = False,
) -> dict:
    """
    모든 플랫폼에 콘텐츠를 발행한다.
    no_publish=True 이면 발행 없이 결과 구조만 반환.

    반환값: {"youtube": video_id, "instagram": post_id, "naver": post_id, "tistory": post_id}
    """
    results = {"youtube": None, "instagram": None, "naver": None, "tistory": None}

    if no_publish:
        logger.info("=== require_approval=true — 발행 단계 건너뜀 ===")
        logger.info("콘텐츠 파일이 outputs/ 폴더에 저장되었습니다.")
        logger.info("승인 후 --step publish 로 재실행하세요.")
        return results

    title = script.get("title", cfg["topic"]["main"])
    description = script.get("description", "")
    tags = script.get("tags", [])

    # ── YouTube ──────────────────────────────────
    if video_path:
        vid = upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path,
            cfg=cfg,
        )
        results["youtube"] = vid

    # ── Instagram ─────────────────────────────────
    # 인스타그램은 공개 URL이 필요하므로 YouTube 업로드 후 링크 or 별도 CDN 필요
    # 현재 버전: 이미지 업로드 시 로컬 경로를 지원하지 않아 스킵 알림 후 진행
    instagram_cfg = cfg.get("publish", {}).get("instagram", {})
    if instagram_cfg.get("enabled", False):
        logger.info(
            "Instagram: 공개 이미지 URL이 필요합니다.\n"
            "  → YouTube 업로드 완료 후 유튜브 URL을 활용하거나\n"
            "  → Google Drive 공유 링크를 image_urls에 입력하여 수동 게시하세요."
        )
        # TODO: Google Drive 업로드 후 공유 링크로 자동 게시 (다음 버전)
        results["instagram"] = "REQUIRES_PUBLIC_URL"

    # ── 네이버 블로그 + 티스토리 ──────────────────
    if article:
        html_content = article_to_html(article, card_paths)
        art_title = article.get("headline", title)
        art_tags = article.get("tags", tags)

        naver_id = naver_post(art_title, html_content, art_tags, cfg)
        results["naver"] = naver_id

        tistory_id = tistory_post(art_title, html_content, art_tags, cfg)
        results["tistory"] = tistory_id

    return results
