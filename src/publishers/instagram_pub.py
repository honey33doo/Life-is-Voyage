"""
instagram_pub.py
================
Instagram Graph API (Meta) 로 카드뉴스 이미지를 게시한다.
비즈니스/크리에이터 계정 + 장기 액세스 토큰 필요.

설정 방법:
  1. Meta for Developers → 앱 생성
  2. Instagram Graph API 추가
  3. 인스타그램 비즈니스/크리에이터 계정 연결
  4. 장기 액세스 토큰 발급
  5. config/my_job.json 의 credentials.instagram_token 에 입력
"""

import logging
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("cardnews.instagram")

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def _get_ig_user_id(token: str) -> Optional[str]:
    """Instagram 비즈니스 계정 ID를 조회한다."""
    try:
        resp = requests.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": token, "fields": "instagram_business_account"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("data", []):
            ig = page.get("instagram_business_account", {})
            if ig.get("id"):
                return ig["id"]
    except Exception as e:
        logger.error(f"Instagram 계정 ID 조회 실패: {e}")
    return None


def _create_media_container(
    ig_user_id: str, token: str, image_url: str, caption: str
) -> Optional[str]:
    """미디어 컨테이너 생성 (이미지 URL 기반)."""
    try:
        resp = requests.post(
            f"{GRAPH_API_BASE}/{ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error(f"미디어 컨테이너 생성 실패: {e}")
        return None


def _create_carousel_container(
    ig_user_id: str, token: str, children_ids: list[str], caption: str
) -> Optional[str]:
    """캐러셀(여러 장) 컨테이너 생성."""
    try:
        resp = requests.post(
            f"{GRAPH_API_BASE}/{ig_user_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
                "access_token": token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error(f"캐러셀 컨테이너 생성 실패: {e}")
        return None


def _publish_container(ig_user_id: str, token: str, container_id: str) -> Optional[str]:
    """컨테이너를 실제 게시한다."""
    try:
        resp = requests.post(
            f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": token},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error(f"Instagram 게시 실패: {e}")
        return None


def upload_carousel(
    image_urls: list[str],
    caption: str,
    cfg: dict,
) -> Optional[str]:
    """
    Instagram 에 캐러셀(카드뉴스) 포스트를 게시한다.
    image_urls: 공개적으로 접근 가능한 이미지 URL 목록 (최대 10개)
    반환값: post_id

    주의: Instagram Graph API 는 공개 URL 이 필요하므로
    로컬 이미지를 먼저 CDN/저장소에 업로드해야 한다.
    현재 버전에서는 Google Drive 공유 링크 또는 직접 URL 을 사용한다.
    """
    pub_cfg = cfg.get("publish", {}).get("instagram", {})
    token = cfg.get("credentials", {}).get("instagram_token", "").strip()

    if not pub_cfg.get("enabled", False):
        logger.info("Instagram 발행 비활성화 — 스킵")
        return None

    if not token:
        logger.warning(
            "Instagram 액세스 토큰이 없습니다.\n"
            "config/my_job.json 의 credentials.instagram_token 에 입력하세요."
        )
        return None

    if not image_urls:
        logger.error("업로드할 이미지 URL 이 없습니다.")
        return None

    ig_user_id = _get_ig_user_id(token)
    if not ig_user_id:
        return None

    # 개별 미디어 컨테이너 생성 (최대 10장)
    urls = image_urls[:10]
    child_ids = []
    for i, url in enumerate(urls):
        logger.info(f"Instagram 미디어 컨테이너 생성 중 ({i+1}/{len(urls)})...")
        cid = _create_media_container(ig_user_id, token, url, "")
        if cid:
            child_ids.append(cid)
        time.sleep(1)  # API 속도 제한 방지

    if not child_ids:
        logger.error("미디어 컨테이너 생성 실패")
        return None

    if len(child_ids) == 1:
        # 단일 이미지
        container_id = _create_media_container(ig_user_id, token, urls[0], caption)
    else:
        # 캐러셀
        container_id = _create_carousel_container(ig_user_id, token, child_ids, caption)

    if not container_id:
        return None

    # 컨테이너 준비 대기 (최대 30초)
    logger.info("게시 준비 중...")
    time.sleep(5)

    post_id = _publish_container(ig_user_id, token, container_id)
    if post_id:
        logger.info(f"Instagram 게시 완료: post_id={post_id}")
    return post_id
