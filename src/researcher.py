"""
researcher.py
=============
웹 검색 및 YouTube 검색으로 원본 자료를 수집한다.
yt-dlp 로 YouTube 메타데이터만 가져오고 영상은 다운로드하지 않는다.
(짧은 클립 발췌가 필요할 경우 별도 처리)
"""

import json
import logging
import re
import subprocess
from datetime import datetime, timedelta
from typing import Optional
import requests

logger = logging.getLogger("cardnews.researcher")


# ────────────────────────────────────────────────
# YouTube 메타데이터 검색 (yt-dlp 사용, 다운로드 없음)
# ────────────────────────────────────────────────

def search_youtube(queries: list[str], max_results: int = 5) -> list[dict]:
    """
    주어진 검색어 목록으로 YouTube 에서 영상 메타데이터를 검색한다.
    반환값: [{"title", "url", "channel", "description", "published", "views"}]
    """
    results = []
    for query in queries:
        try:
            cmd = [
                "yt-dlp",
                f"ytsearch{max_results}:{query}",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                "--quiet",
                "--ignore-errors",
            ]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in out.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    meta = json.loads(line)
                    results.append({
                        "source_type": "youtube",
                        "title": meta.get("title", ""),
                        "url": meta.get("webpage_url", ""),
                        "channel": meta.get("channel", meta.get("uploader", "")),
                        "description": (meta.get("description", "") or "")[:500],
                        "published": meta.get("upload_date", ""),
                        "views": meta.get("view_count", 0),
                        "thumbnail": meta.get("thumbnail", ""),
                        "duration": meta.get("duration", 0),
                    })
                except json.JSONDecodeError:
                    continue
        except subprocess.TimeoutExpired:
            logger.warning(f"YouTube 검색 타임아웃: {query}")
        except Exception as e:
            logger.warning(f"YouTube 검색 오류 ({query}): {e}")
    logger.info(f"YouTube 검색 완료: {len(results)}건")
    return results


# ────────────────────────────────────────────────
# 네이버 뉴스 검색 API
# ────────────────────────────────────────────────

def search_naver_news(
    queries: list[str],
    client_id: str,
    client_secret: str,
    max_results: int = 5,
) -> list[dict]:
    """
    네이버 뉴스 검색 API 로 기사를 가져온다.
    API 키가 없으면 빈 리스트 반환.
    """
    if not client_id or not client_secret:
        logger.info("네이버 API 키 없음 — 뉴스 검색 스킵")
        return []

    results = []
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    for query in queries:
        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/news.json",
                headers=headers,
                params={"query": query, "display": max_results, "sort": "date"},
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            for item in items:
                # HTML 태그 제거
                title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                desc = re.sub(r"<[^>]+>", "", item.get("description", ""))
                results.append({
                    "source_type": "naver_news",
                    "title": title,
                    "url": item.get("originallink", item.get("link", "")),
                    "channel": item.get("bloggername", ""),
                    "description": desc,
                    "published": item.get("pubDate", ""),
                    "views": 0,
                })
        except Exception as e:
            logger.warning(f"네이버 뉴스 검색 오류 ({query}): {e}")
    logger.info(f"네이버 뉴스 검색 완료: {len(results)}건")
    return results


# ────────────────────────────────────────────────
# 통합 리서치
# ────────────────────────────────────────────────

def run_research(cfg: dict) -> list[dict]:
    """
    설정에 따라 YouTube + 뉴스 검색을 실행하고
    중복 제거 후 소스 목록을 반환한다.
    """
    sources_cfg = cfg.get("sources", {})
    queries = sources_cfg.get("search_queries", [cfg["topic"]["main"]])
    max_sources = sources_cfg.get("max_sources", 10)

    all_results: list[dict] = []

    # YouTube 검색
    if sources_cfg.get("youtube_search", True):
        yt_results = search_youtube(queries, max_results=3)
        all_results.extend(yt_results)

    # 네이버 뉴스 검색
    creds = cfg.get("credentials", {})
    if sources_cfg.get("web_search", True):
        naver_results = search_naver_news(
            queries,
            client_id=creds.get("naver_client_id", ""),
            client_secret=creds.get("naver_client_secret", ""),
            max_results=5,
        )
        all_results.extend(naver_results)

    # 중복 URL 제거
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    # 최대 개수 제한
    final = unique_results[:max_sources]
    logger.info(f"리서치 완료: 총 {len(final)}개 소스")
    return final
