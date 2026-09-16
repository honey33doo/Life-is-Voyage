"""
youtube_pub.py
==============
YouTube Data API v3 를 이용해 영상과 썸네일을 업로드한다.
OAuth 2.0 인증 (로컬 최초 1회) + 토큰 저장으로 이후 자동 갱신.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("cardnews.youtube")

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("google-api-python-client 미설치. YouTube 업로드 불가.")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = Path("config/youtube_token.json")


def _get_youtube_client(client_secret_path: str):
    """YouTube API 클라이언트를 반환한다. 토큰이 없으면 브라우저 인증을 시도한다."""
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("google-api-python-client 가 설치되지 않았습니다.")

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(client_secret_path).exists():
                raise FileNotFoundError(
                    f"YouTube client_secret.json 파일이 없습니다: {client_secret_path}\n"
                    "Google Cloud Console 에서 OAuth 2.0 자격증명을 다운로드하세요."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: Optional[Path],
    cfg: dict,
) -> Optional[str]:
    """
    YouTube 에 영상을 업로드한다.
    반환값: video_id (업로드 실패 시 None)
    """
    pub_cfg = cfg.get("publish", {}).get("youtube", {})
    creds_cfg = cfg.get("credentials", {})
    client_secret = creds_cfg.get("youtube_client_secret", "config/youtube_client_secret.json")

    if not pub_cfg.get("enabled", False):
        logger.info("YouTube 발행 비활성화 — 스킵")
        return None

    if not video_path or not video_path.exists():
        logger.error(f"영상 파일 없음: {video_path}")
        return None

    try:
        youtube = _get_youtube_client(client_secret)
        privacy = pub_cfg.get("privacy", "public")
        category_id = pub_cfg.get("category_id", "25")  # 25 = News & Politics
        all_tags = list(set(tags + pub_cfg.get("default_tags", [])))

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": all_tags[:500],
                "categoryId": category_id,
                "defaultLanguage": "ko",
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 5,  # 5MB 청크
        )

        logger.info(f"YouTube 업로드 시작: {video_path.name}")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"업로드 진행: {int(status.progress() * 100)}%")

        video_id = response.get("id", "")
        logger.info(f"YouTube 업로드 완료: https://youtube.com/watch?v={video_id}")

        # 썸네일 설정
        if thumbnail_path and thumbnail_path.exists() and video_id:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
                ).execute()
                logger.info("썸네일 설정 완료")
            except Exception as e:
                logger.warning(f"썸네일 설정 실패 (계속 진행): {e}")

        return video_id

    except Exception as e:
        logger.error(f"YouTube 업로드 실패: {e}")
        return None
