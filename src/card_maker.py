"""
card_maker.py
=============
PIL(Pillow)로 카드뉴스 이미지를 생성한다.
다크 모던 스타일, 한글 폰트(NanumSquare) 사용.
"""

import logging
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import colorsys

logger = logging.getLogger("cardnews.card_maker")

# ────────────────────────────────────────────────
# 상수 / 기본값
# ────────────────────────────────────────────────

FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf",        # Bold
    "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",        # Regular
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]

FONT_PATHS_LIGHT = [
    "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """사용 가능한 나눔 폰트를 찾아 반환한다."""
    paths = FONT_PATHS if bold else FONT_PATHS_LIGHT
    for fp in paths:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    # 폴백: PIL 기본 폰트
    logger.warning("나눔 폰트를 찾지 못했습니다. 기본 폰트를 사용합니다.")
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ────────────────────────────────────────────────
# 카드 렌더러
# ────────────────────────────────────────────────

class CardRenderer:
    """단일 카드뉴스 이미지를 렌더링한다."""

    def __init__(self, cfg: dict):
        media = cfg.get("media", {})
        fmt = media.get("card_format", "1080x1080").split("x")
        self.width = int(fmt[0])
        self.height = int(fmt[1])
        self.brand_name = media.get("brand_name", "데이뉴스")
        self.primary = _hex_to_rgb(media.get("brand_color_primary", "#1E3A5F"))
        self.accent = _hex_to_rgb(media.get("brand_color_accent", "#F4A300"))
        self.watermark = media.get("watermark", True)

    # ── 배경 ──────────────────────────────────────

    def _draw_background(self, draw: ImageDraw.Draw, card_type: str) -> None:
        w, h = self.width, self.height
        r, g, b = self.primary

        # 기본 배경
        draw.rectangle([0, 0, w, h], fill=(r, g, b))

        # 하단 그라디언트 효과 (어두운 띠)
        for i in range(int(h * 0.6), h):
            alpha = int((i - h * 0.6) / (h * 0.4) * 40)
            draw.rectangle([0, i, w, i + 1], fill=(max(r-alpha,0), max(g-alpha,0), max(b-alpha,0)))

        # 액센트 상단 띠
        draw.rectangle([0, 0, w, 8], fill=self.accent)

        # 커버 카드 전용 장식
        if card_type == "cover":
            # 대각선 장식 사각형
            draw.polygon(
                [(w*0.65, 0), (w, 0), (w, h*0.45), (w*0.75, h*0.45)],
                fill=(max(r-20,0), max(g-20,0), min(b+30,255)),
            )

    # ── 카드 번호 배지 ─────────────────────────────

    def _draw_badge(self, draw: ImageDraw.Draw, card_num: int, total: int) -> None:
        if card_num in (1, total):
            return  # 커버·클로징 카드에는 번호 없음
        font = _get_font(28, bold=False)
        text = f"{card_num - 1}"
        draw.ellipse([40, 40, 90, 90], fill=self.accent)
        draw.text((65, 65), text, font=font, fill=(20, 20, 20), anchor="mm")

    # ── 텍스트 래핑 ───────────────────────────────

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        """텍스트를 max_width 픽셀 내로 줄 바꿈한다."""
        words = list(text)  # 한글은 글자 단위로 처리
        lines = []
        current = ""
        for char in text:
            test = current + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    # ── 워터마크 ──────────────────────────────────

    def _draw_watermark(self, draw: ImageDraw.Draw) -> None:
        font = _get_font(26, bold=False)
        text = f"◆ {self.brand_name}"
        draw.text(
            (self.width - 40, self.height - 40),
            text,
            font=font,
            fill=(*self.accent, 180),
            anchor="rb",
        )

    # ── 메인 렌더 ─────────────────────────────────

    def render(self, card_data: dict, card_num: int, total: int) -> Image.Image:
        """카드 dict 를 받아 PIL Image 를 반환한다."""
        img = Image.new("RGB", (self.width, self.height), self.primary)
        draw = ImageDraw.Draw(img)

        card_type = card_data.get("type", "content")
        headline = card_data.get("headline", "")
        body = card_data.get("body", "")
        source = card_data.get("source", "")

        self._draw_background(draw, card_type)

        pad = 80  # 좌우 패딩
        center_x = self.width // 2

        if card_type == "cover":
            # ── 커버 카드 ──
            # 카드 번호 라벨
            label_font = _get_font(30, bold=False)
            draw.text((pad, self.height // 2 - 180), "CARD NEWS", font=label_font, fill=self.accent)
            draw.rectangle([pad, self.height//2 - 150, pad+80, self.height//2 - 146], fill=self.accent)

            # 헤드라인 (큰 제목)
            h_font = _get_font(min(72, int(1800 / max(len(headline), 1))))
            lines = self._wrap_text(headline, h_font, self.width - pad*2)
            y = self.height // 2 - 120
            for line in lines[:3]:
                draw.text((pad, y), line, font=h_font, fill=(255, 255, 255))
                y += h_font.size + 10

            # 부제목
            b_font = _get_font(38, bold=False)
            b_lines = self._wrap_text(body, b_font, self.width - pad*2)
            y += 20
            for line in b_lines[:2]:
                draw.text((pad, y), line, font=b_font, fill=(220, 220, 230))
                y += b_font.size + 8

        elif card_type == "closing":
            # ── 클로징 카드 ──
            h_font = _get_font(56)
            draw.text((center_x, self.height//2 - 100), headline, font=h_font, fill=self.accent, anchor="mm")
            b_font = _get_font(36, bold=False)
            b_lines = self._wrap_text(body, b_font, self.width - pad*2)
            y = self.height//2 - 20
            for line in b_lines:
                draw.text((center_x, y), line, font=b_font, fill=(200, 210, 230), anchor="mm")
                y += b_font.size + 8
            # 액센트 라인
            draw.rectangle([center_x-120, self.height//2-120, center_x+120, self.height//2-116], fill=self.accent)
            # 출처
            if source:
                s_font = _get_font(24, bold=False)
                draw.text((center_x, self.height - 80), source, font=s_font, fill=(160, 170, 190), anchor="mm")

        else:
            # ── 일반 콘텐츠 카드 ──
            self._draw_badge(draw, card_num, total)

            # 헤드라인
            h_font = _get_font(58)
            h_lines = self._wrap_text(headline, h_font, self.width - pad*2)
            y = 180
            for line in h_lines[:2]:
                draw.text((pad, y), line, font=h_font, fill=(255, 255, 255))
                y += h_font.size + 14

            # 구분선
            draw.rectangle([pad, y+20, self.width-pad, y+24], fill=self.accent)
            y += 50

            # 본문
            b_font = _get_font(40, bold=False)
            b_lines = self._wrap_text(body, b_font, self.width - pad*2)
            for line in b_lines[:4]:
                draw.text((pad, y), line, font=b_font, fill=(215, 220, 235))
                y += b_font.size + 12

            # 출처
            if source:
                s_font = _get_font(26, bold=False)
                draw.text((pad, self.height - 90), source, font=s_font, fill=(140, 150, 175))

        if self.watermark:
            self._draw_watermark(draw)

        return img


# ────────────────────────────────────────────────
# 퍼블릭 인터페이스
# ────────────────────────────────────────────────

def make_cards(script: dict, cfg: dict, output_dir: Path) -> list[Path]:
    """
    스크립트 dict 를 받아 카드뉴스 이미지 파일 목록을 반환한다.
    output_dir/cards/ 에 저장된다.
    """
    cards_dir = output_dir / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    renderer = CardRenderer(cfg)
    card_list = script.get("cards", [])
    total = len(card_list)
    saved_paths: list[Path] = []

    for card_data in card_list:
        num = card_data.get("card_num", 0)
        img = renderer.render(card_data, num, total)
        out_path = cards_dir / f"card_{num:02d}.jpg"
        img.save(str(out_path), "JPEG", quality=92)
        saved_paths.append(out_path)
        logger.info(f"카드 저장: {out_path.name}")

    logger.info(f"카드 생성 완료: {len(saved_paths)}장")
    return saved_paths


def make_thumbnail(script: dict, cfg: dict, output_dir: Path) -> Path:
    """YouTube 썸네일(1280x720)을 생성한다."""
    thumb_dir = output_dir
    thumb_dir.mkdir(parents=True, exist_ok=True)

    # 썸네일용 설정 오버라이드
    thumb_cfg = {**cfg, "media": {**cfg.get("media", {}), "card_format": "1280x720"}}
    renderer = CardRenderer(thumb_cfg)

    first_card = script.get("cards", [{}])[0]
    img = renderer.render(first_card, 1, len(script.get("cards", [1])))

    thumb_path = thumb_dir / "thumbnail.jpg"
    img.save(str(thumb_path), "JPEG", quality=95)
    logger.info(f"썸네일 저장: {thumb_path}")
    return thumb_path
