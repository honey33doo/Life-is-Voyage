"""
video_maker.py
==============
PIL 카드 이미지들을 ffmpeg 로 슬라이드쇼 영상으로 변환한다.
YouTube Shorts (세로) 또는 일반 유튜브 영상(가로) 모두 지원.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("cardnews.video_maker")

# 카드 1장당 표시 시간 (초)
DEFAULT_SECONDS_PER_CARD = 4
# 기본 배경음악 (없으면 무음)
DEFAULT_BGM_PATH: Optional[str] = None


def _check_ffmpeg() -> bool:
    """ffmpeg 설치 여부 확인."""
    return shutil.which("ffmpeg") is not None


def _make_concat_list(card_paths: list[Path], duration: int, tmp_dir: Path) -> Path:
    """
    ffmpeg concat demuxer 용 파일 목록을 생성한다.
    각 이미지를 duration 초 동안 표시한다.
    """
    list_file = tmp_dir / "concat_list.txt"
    lines = []
    for cp in card_paths:
        lines.append(f"file '{cp.resolve()}'")
        lines.append(f"duration {duration}")
    # 마지막 이미지 한 번 더 (ffmpeg 요구사항)
    if card_paths:
        lines.append(f"file '{card_paths[-1].resolve()}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")
    return list_file


def make_video(
    card_paths: list[Path],
    output_dir: Path,
    cfg: dict,
    as_shorts: bool = False,
    bgm_path: Optional[str] = None,
) -> Optional[Path]:
    """
    카드 이미지들을 이어 붙여 MP4 영상을 생성한다.
    반환값: 생성된 영상 경로 (ffmpeg 없으면 None)
    """
    if not _check_ffmpeg():
        logger.warning("ffmpeg 를 찾을 수 없습니다. 영상 생성을 건너뜁니다.")
        return None

    if not card_paths:
        logger.error("카드 이미지가 없어 영상을 만들 수 없습니다.")
        return None

    tmp_dir = output_dir / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 카드당 표시 시간
    seconds_per_card = cfg.get("media", {}).get("seconds_per_card", DEFAULT_SECONDS_PER_CARD)
    concat_file = _make_concat_list(card_paths, seconds_per_card, tmp_dir)

    # 출력 해상도: Shorts(1080x1920) 또는 일반(1920x1080)
    if as_shorts:
        scale = "1080:1920"
        out_name = "video_shorts.mp4"
    else:
        scale = "1920:1080"
        out_name = "video.mp4"

    out_path = output_dir / out_name

    # ffmpeg 명령 구성
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-vf", f"scale={scale}:force_original_aspect_ratio=decrease,"
               f"pad={scale}:(ow-iw)/2:(oh-ih)/2:color=#1E3A5F,"
               f"format=yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-r", "24",
        "-movflags", "+faststart",
    ]

    # 배경음악 추가 (옵션)
    bgm = bgm_path or DEFAULT_BGM_PATH
    if bgm and Path(bgm).exists():
        total_duration = len(card_paths) * seconds_per_card
        cmd = (
            cmd[:3]  # ffmpeg -y -f concat
            + ["-safe", "0", "-i", str(concat_file)]
            + ["-stream_loop", "-1", "-i", bgm]
            + cmd[7:]  # -vf 이후
            + [
                "-c:a", "aac",
                "-b:a", "128k",
                "-t", str(total_duration),
                "-shortest",
            ]
        )

    cmd.append(str(out_path))

    logger.info("ffmpeg 영상 생성 중...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error(f"ffmpeg 오류:\n{result.stderr[-1000:]}")
        return None

    # 임시 파일 정리
    shutil.rmtree(tmp_dir, ignore_errors=True)
    logger.info(f"영상 생성 완료: {out_path}")
    return out_path
