"""
news_card_maker.py — 이판사판(@2pan@4pan) 온라인 언론 플랫폼 카드 렌더러
=======================================================================
• 16:9 (1920×1080) — YouTube 기본 송출 포맷
• 9:16 (1080×1920) — YouTube Shorts / Instagram Reels
• 배경: 영상 블러 효과 시뮬레이션 (노이즈 + 그라데이션 레이어)
• 언론사 UI: 속보 배너 · 로고 바 · 출처 바 · 카드 진행 인디케이터
• 폰트 체계:
    로고/브랜드  ← GmarketSansTTFBold
    헤드라인     ← Hakgyoansim_PosterB  (임팩트·포스터형)
    서브헤드     ← paybooc_ExtraBold    (강조 보조)
    본문         ← NeoHyundai_B         (가독성 최우선)
    속보 배너    ← Cafe24Dangdanghae    (긴급·주목 효과)
    출처/날짜    ← KoPub_Dotum_Bold     (신뢰·정보성)
    장식/아이콘  ← H2HDRM              (디스플레이 헤드)
"""

from __future__ import annotations

import math
import random
import textwrap
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── 경로 ─────────────────────────────────────────────────────────────────────
FONT_DIR = Path("/usr/share/fonts/truetype/2pan4pan")

FONTS = {
    "logo":      FONT_DIR / "GmarketSansTTFBold.ttf",
    "headline":  FONT_DIR / "Hakgyoansim_PosterB.ttf",
    "subhead":   FONT_DIR / "paybooc_ExtraBold.ttf",
    "body":      FONT_DIR / "NeoHyundai_B.ttf",
    "breaking":  FONT_DIR / "Cafe24Dangdanghae-v2.0.ttf",
    "source":    FONT_DIR / "KoPub_Dotum_Bold.ttf",
    "display":   FONT_DIR / "H2HDRM.ttf",
    "deco":      FONT_DIR / "samlip-creamy-white-regular.ttf",
}

# ── 이판사판 브랜드 색상 ──────────────────────────────────────────────────────
BRAND = {
    "bg_dark":     (8,  10,  20),          # 최심 다크 배경
    "bg_mid":      (14, 18,  36),          # 패널 배경
    "bg_panel":    (20, 24,  48, 210),     # 반투명 콘텐츠 패널
    "accent_red":  (220, 38,  38),         # 속보 빨강  #DC2626
    "accent_gold": (251, 191, 36),         # 하이라이트 골드  #FBBF24
    "accent_cyan": (6,  182, 212),         # 링크·태그 시안  #06B6D4
    "text_white":  (255, 255, 255),
    "text_silver": (203, 213, 225),        # 본문 밝은 회색
    "text_muted":  (100, 116, 139),        # 보조 정보 흐린 회색
    "divider":     (51,  65,  85),         # 구분선
    "overlay":     (0,   0,   0,  160),    # 오버레이
    "breaking_bg": (220, 38,  38),
    "tag_bg":      (30,  41,  59,  220),   # 태그 배경
}


def _load_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """폰트 로드 — 실패 시 기본 폰트 폴백."""
    path = FONTS.get(role)
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _hex(rgb: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


# ── 배경 생성: 영상 블러 시뮬레이션 ─────────────────────────────────────────

def _make_video_bg(w: int, h: int, seed: int = 42) -> Image.Image:
    """
    실제 영상 대신 노이즈 + 그라데이션으로 '방송 블러 배경' 효과 구현.
    레이어:
      L1. 딥 다크 베이스
      L2. 컬러 노이즈 (시네마틱 그레인)
      L3. 방사형 그라데이션 (스팟라이트)
      L4. 대각선 라이트빔
      L5. 비네트 (가장자리 어두움)
    """
    rng = np.random.default_rng(seed)
    bg = BRAND["bg_dark"]

    # L1: 기본 배경
    base = np.full((h, w, 3), bg, dtype=np.uint8)

    # L2: 시네마틱 그레인 (저채도 컬러 노이즈)
    noise = rng.integers(-18, 18, (h, w, 3), dtype=np.int16)
    base = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(base, "RGB")

    # L3: 방사형 그라데이션 (중앙 스팟)
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    cx, cy = w // 2, h // 2
    for r in range(min(w, h) // 2, 0, -1):
        alpha = int(30 * (1 - r / (min(w, h) / 2)))
        gd.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(30, 50, 100, alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), grad)

    # L4: 대각선 라이트빔 (시네마틱 레이)
    beam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd   = ImageDraw.Draw(beam)
    for i in range(4):
        x0 = rng.integers(w // 4, 3 * w // 4)
        bd.polygon(
            [(x0, 0), (x0 + 60, 0), (x0 + 300, h), (x0 + 180, h)],
            fill=(255, 255, 255, 6),
        )
    img = Image.alpha_composite(img, beam)

    # L5: 비네트
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd       = ImageDraw.Draw(vignette)
    steps    = 80
    for i in range(steps):
        ratio = i / steps
        alpha = int(180 * ratio ** 1.8)
        pad   = int(ratio * min(w, h) * 0.42)
        # 비네트: 바깥 테두리 rectangle을 직접 그리는 대신
        # 어두운 알파로 채운 테두리 박스 4개를 그려 비네트 효과 구현
        if pad > 2 and (w - 2 * pad) > 0 and (h - 2 * pad) > 0:
            vd.rectangle([0, 0, w, pad], fill=(0, 0, 0, alpha))          # top
            vd.rectangle([0, h - pad, w, h], fill=(0, 0, 0, alpha))      # bottom
            vd.rectangle([0, pad, pad, h - pad], fill=(0, 0, 0, alpha))  # left
            vd.rectangle([w - pad, pad, w, h - pad], fill=(0, 0, 0, alpha))  # right
    img = Image.alpha_composite(img, vignette)

    # 마지막 Gaussian Blur (영상 아웃포커스 느낌)
    img = img.convert("RGB").filter(ImageFilter.GaussianBlur(radius=1.5))
    return img


# ── 텍스트 유틸 ───────────────────────────────────────────────────────────────

def _draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    shadow_offset: int = 3,
    shadow_alpha: int = 120,
):
    """그림자 있는 텍스트 렌더링."""
    sx, sy = xy[0] + shadow_offset, xy[1] + shadow_offset
    draw.text((sx, sy), text, font=font, fill=(0, 0, 0, shadow_alpha))
    draw.text(xy, text, font=font, fill=fill)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """폰트 너비 기준 자동 줄바꿈."""
    # \n 이 포함된 경우 수동 줄바꿈 우선 처리
    manual_lines = text.split("\n")
    lines = []
    for ml in manual_lines:
        words = list(ml)  # 한국어: 글자 단위로 처리
        cur = ""
        for ch in ml:
            test = cur + ch
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
    return lines


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    bbox: tuple[int, int, int, int],
    radius: int,
    fill: tuple,
):
    """PIL에 기본 내장된 rounded_rectangle 래퍼."""
    draw.rounded_rectangle(bbox, radius=radius, fill=fill)


def _get_text_size(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ── 언론사 UI 컴포넌트 ────────────────────────────────────────────────────────

class NewsUIKit:
    """이판사판 언론사 UI 컴포넌트 라이브러리."""

    def __init__(self, w: int, h: int, is_portrait: bool):
        self.w    = w
        self.h    = h
        self.port = is_portrait   # True = 9:16

        # 비율 스케일 팩터 (1080 기준)
        self.sf = w / 1080

        # 폰트 사이즈 — 가로형 / 세로형 각각 튜닝
        if is_portrait:
            self.sz_logo      = int(44 * self.sf)
            self.sz_handle    = int(28 * self.sf)
            self.sz_breaking  = int(36 * self.sf)
            self.sz_category  = int(30 * self.sf)
            self.sz_headline  = int(72 * self.sf)
            self.sz_body      = int(42 * self.sf)
            self.sz_source    = int(30 * self.sf)
            self.sz_counter   = int(28 * self.sf)
            self.sz_number    = int(200 * self.sf)
        else:  # 16:9
            self.sz_logo      = int(38 * self.sf * 0.65)
            self.sz_handle    = int(24 * self.sf * 0.65)
            self.sz_breaking  = int(32 * self.sf * 0.65)
            self.sz_category  = int(26 * self.sf * 0.65)
            self.sz_headline  = int(78 * self.sf * 0.65)
            self.sz_body      = int(36 * self.sf * 0.65)
            self.sz_source    = int(26 * self.sf * 0.65)
            self.sz_counter   = int(24 * self.sf * 0.65)
            self.sz_number    = int(160 * self.sf * 0.65)

    def header_bar(self, img: Image.Image, card_num: int, total: int) -> Image.Image:
        """
        최상단 헤더: [이판사판 로고] [속보] [카드 N/T]
        반투명 다크 패널.
        """
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        h_bar   = int(90 * self.sf) if self.port else int(64 * self.sf)

        # 헤더 배경 (반투명)
        draw.rectangle([0, 0, self.w, h_bar], fill=(8, 10, 20, 220))
        # 하단 구분선 (골드)
        draw.rectangle([0, h_bar - 3, self.w, h_bar], fill=BRAND["accent_gold"])

        f_logo   = _load_font("logo",    self.sz_logo)
        f_handle = _load_font("source",  self.sz_handle)
        f_count  = _load_font("source",  self.sz_counter)

        pad = int(28 * self.sf)

        # 로고 "이판사판"
        draw.text((pad, (h_bar - self.sz_logo) // 2 - 2), "이판사판",
                  font=f_logo, fill=BRAND["text_white"])
        tw, _ = _get_text_size("이판사판", f_logo)

        # 핸들 "@2pan4pan"
        hx = pad + tw + int(14 * self.sf)
        hy = h_bar // 2 + 4
        draw.text((hx, hy), "@2pan4pan",
                  font=f_handle, fill=BRAND["accent_cyan"])

        # 카드 진행 인디케이터 (우측)
        cnt_text = f"{card_num}  /  {total}"
        ctw, _   = _get_text_size(cnt_text, f_count)
        cx       = self.w - pad - ctw
        draw.text((cx, (h_bar - self.sz_counter) // 2),
                  cnt_text, font=f_count, fill=BRAND["text_muted"])

        # 진행 바
        bar_w     = int(120 * self.sf)
        bar_h     = 4
        bar_x     = cx - bar_w - int(16 * self.sf)
        bar_y     = h_bar // 2 - 2
        progress  = int(bar_w * card_num / max(total, 1))
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                                radius=2, fill=BRAND["divider"])
        draw.rounded_rectangle([bar_x, bar_y, bar_x + progress, bar_y + bar_h],
                                radius=2, fill=BRAND["accent_gold"])

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def breaking_band(self, img: Image.Image, category: str = "기자회견") -> Image.Image:
        """속보 배너 밴드 (헤더 직하단)."""
        overlay  = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw     = ImageDraw.Draw(overlay)
        h_hdr    = int(90 * self.sf) if self.port else int(64 * self.sf)
        band_h   = int(52 * self.sf)
        f_brk    = _load_font("breaking", self.sz_breaking)
        f_cat    = _load_font("source",   self.sz_category)

        # 빨강 속보 태그
        label    = "  속  보  "
        lw, _    = _get_text_size(label, f_brk)
        tag_pad  = int(10 * self.sf)
        tag_rect = [0, h_hdr, lw + tag_pad * 2, h_hdr + band_h]
        draw.rectangle(tag_rect, fill=BRAND["accent_red"])
        draw.text((tag_pad, h_hdr + (band_h - self.sz_breaking) // 2 - 2),
                  label, font=f_brk, fill=BRAND["text_white"])

        # 카테고리 텍스트
        cat_x = tag_rect[2] + int(20 * self.sf)
        draw.rectangle([tag_rect[2], h_hdr, self.w, h_hdr + band_h],
                       fill=(14, 18, 36, 200))
        draw.text((cat_x, h_hdr + (band_h - self.sz_category) // 2),
                  f"▶  {category}", font=f_cat, fill=BRAND["accent_gold"])

        # 하단 구분선
        draw.rectangle([0, h_hdr + band_h - 1, self.w, h_hdr + band_h],
                       fill=BRAND["divider"])

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def footer_bar(
        self, img: Image.Image, source: str, date: str = "2026.09.16"
    ) -> Image.Image:
        """하단 출처 바 (반투명)."""
        overlay  = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw     = ImageDraw.Draw(overlay)
        bar_h    = int(72 * self.sf) if self.port else int(54 * self.sf)
        f_src    = _load_font("source", self.sz_source)

        # 배경
        draw.rectangle([0, self.h - bar_h, self.w, self.h],
                       fill=(8, 10, 20, 230))
        # 상단 골드선
        draw.rectangle([0, self.h - bar_h, self.w, self.h - bar_h + 2],
                       fill=BRAND["accent_gold"])

        pad  = int(28 * self.sf)
        mid_y = self.h - bar_h + (bar_h - self.sz_source) // 2

        # 출처
        if source:
            draw.text((pad, mid_y), f"출처  |  {source}",
                      font=f_src, fill=BRAND["text_muted"])

        # 날짜 (우측)
        dw, _ = _get_text_size(date, f_src)
        draw.text((self.w - pad - dw, mid_y), date,
                  font=f_src, fill=BRAND["text_muted"])

        # 이판사판 watermark (중앙)
        wm_text = "이판사판  |  @2pan4pan"
        ww, _   = _get_text_size(wm_text, f_src)
        draw.text(((self.w - ww) // 2, mid_y), wm_text,
                  font=f_src, fill=(60, 80, 100, 180))

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def content_panel(
        self, img: Image.Image, y_start: int, y_end: int, alpha: int = 200
    ) -> Image.Image:
        """콘텐츠 영역 반투명 패널."""
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        pad     = int(32 * self.sf)
        draw.rounded_rectangle(
            [pad, y_start, self.w - pad, y_end],
            radius=int(12 * self.sf),
            fill=(14, 18, 36, alpha),
        )
        # 좌측 액센트 바
        draw.rounded_rectangle(
            [pad, y_start, pad + int(6 * self.sf), y_end],
            radius=int(3 * self.sf),
            fill=BRAND["accent_gold"],
        )
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def draw_headline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        max_w: int,
        color: tuple = None,
    ) -> int:
        """헤드라인 텍스트 렌더링 (줄바꿈 포함), 다음 y 반환."""
        if color is None:
            color = BRAND["text_white"]
        f  = _load_font("headline", self.sz_headline)
        lines = _wrap_text(text, f, max_w)
        line_h = int(self.sz_headline * 1.25)
        for line in lines:
            _draw_text_shadow(draw, (x, y), line, f, color, shadow_offset=4)
            y += line_h
        return y

    def draw_body(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        max_w: int,
        color: tuple = None,
    ) -> int:
        """본문 텍스트 렌더링, 다음 y 반환."""
        if color is None:
            color = BRAND["text_silver"]
        f      = _load_font("body", self.sz_body)
        lines  = _wrap_text(text, f, max_w)
        line_h = int(self.sz_body * 1.6)
        for line in lines:
            draw.text((x, y), line, font=f, fill=color)
            y += line_h
        return y

    def draw_large_number(
        self, img: Image.Image, number: str
    ) -> Image.Image:
        """배경에 대형 번호 워터마크 (반투명)."""
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        f       = _load_font("display", self.sz_number)
        tw, th  = _get_text_size(number, f)
        x = self.w - tw - int(40 * self.sf)
        y = (self.h - th) // 2
        draw.text((x, y), number, font=f, fill=(255, 255, 255, 18))
        return Image.alpha_composite(img.convert("RGBA"), overlay)


# ── 카드 렌더링 메인 ──────────────────────────────────────────────────────────

class IPSPCardRenderer:
    """
    이판사판 NewsCardRenderer
    format: '16:9' (1920×1080) | '9:16' (1080×1920)
    """

    FORMAT_16_9 = (1920, 1080)
    FORMAT_9_16 = (1080, 1920)

    def __init__(self, fmt: Literal["16:9", "9:16"] = "16:9"):
        self.fmt  = fmt
        self.w, self.h = (
            self.FORMAT_9_16 if fmt == "9:16" else self.FORMAT_16_9
        )
        self.port = fmt == "9:16"
        self.ui   = NewsUIKit(self.w, self.h, self.port)

    def _base(self, seed: int = 0) -> Image.Image:
        return _make_video_bg(self.w, self.h, seed=seed)

    def _content_area(self) -> tuple[int, int, int, int]:
        """헤더·푸터 제외 콘텐츠 영역 (x, y, max_w, max_h)."""
        h_hdr   = int(90 * self.w / 1080) if self.port else int(64 * self.w / 1080)
        band_h  = int(52 * self.w / 1080)
        foot_h  = int(72 * self.w / 1080) if self.port else int(54 * self.w / 1080)
        pad     = int(60 * self.w / 1080)
        y_top   = h_hdr + band_h + pad
        y_bot   = self.h - foot_h - pad
        x_left  = pad + int(32 * self.w / 1080) + int(24 * self.w / 1080)
        max_w   = self.w - x_left - pad
        return x_left, y_top, max_w, y_bot - y_top

    # ── 커버 카드 ────────────────────────────────────────────────────────────

    def render_cover(self, card: dict, total: int) -> Image.Image:
        img  = self._base(seed=1)
        ui   = self.ui
        sf   = self.w / 1080

        img = ui.header_bar(img, 1, total)
        img = ui.breaking_band(img, card.get("category", "이판사판 단독"))

        # 중앙 대형 제목 패널
        cx_top = int(155 * sf) if self.port else int(120 * sf)
        cx_bot = self.h - int(72 * sf) if self.port else self.h - int(54 * sf)
        img = ui.content_panel(img, cx_top, cx_bot, alpha=210)

        # 대형 배경 숫자 장식
        img = ui.draw_large_number(img, "①")

        draw = ImageDraw.Draw(img.convert("RGBA"))
        img  = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        x, y_top, max_w, _ = self._content_area()

        # 주제 태그
        f_tag = _load_font("source", ui.sz_category)
        tag   = f"  ◆  {card.get('category', '정치·시사')}  "
        tw, th = _get_text_size(tag, f_tag)
        draw.rounded_rectangle(
            [x, y_top, x + tw + 8, y_top + th + 12],
            radius=4, fill=BRAND["accent_cyan"] + (220,),
        )
        draw.text((x + 4, y_top + 6), tag, font=f_tag,
                  fill=BRAND["bg_dark"])
        y = y_top + th + int(36 * sf)

        # 메인 헤드라인
        f_hl = _load_font("headline", ui.sz_headline)
        y    = ui.draw_headline(draw, card.get("headline", ""), x, y, max_w,
                                 color=BRAND["text_white"])
        y   += int(20 * sf)

        # 구분선
        draw.rectangle([x, y, x + int(80 * sf), y + 4],
                       fill=BRAND["accent_gold"])
        y += int(28 * sf)

        # 부제 / body
        if card.get("body"):
            f_sub = _load_font("subhead", ui.sz_body)
            lines = _wrap_text(card["body"], f_sub, max_w)
            for line in lines[:3]:
                draw.text((x, y), line, font=f_sub,
                          fill=BRAND["text_silver"])
                y += int(ui.sz_body * 1.5)

        img = ui.footer_bar(img, card.get("source", ""), "2026.09.16")
        return img.convert("RGB")

    # ── 콘텐츠 카드 ──────────────────────────────────────────────────────────

    def render_content(self, card: dict, total: int) -> Image.Image:
        num  = card.get("card_num", 2)
        img  = self._base(seed=num)
        ui   = self.ui
        sf   = self.w / 1080

        img = ui.header_bar(img, num, total)
        img = ui.breaking_band(img, card.get("category", ""))

        h_hdr   = int(90 * sf) if self.port else int(64 * sf)
        band_h  = int(52 * sf)
        foot_h  = int(72 * sf) if self.port else int(54 * sf)
        pad     = int(60 * sf)
        y_top   = h_hdr + band_h + pad // 2
        y_bot   = self.h - foot_h - pad // 2
        img     = ui.content_panel(img, y_top, y_bot, alpha=215)
        img     = ui.draw_large_number(img, str(num))

        draw = ImageDraw.Draw(img.convert("RGBA"))
        img  = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        x, y, max_w, _ = self._content_area()

        # 카드 번호 뱃지
        f_num  = _load_font("subhead", ui.sz_category)
        badge  = f"  {num:02d}  "
        bw, bh = _get_text_size(badge, f_num)
        draw.rounded_rectangle(
            [x, y, x + bw + 8, y + bh + 10], radius=4,
            fill=BRAND["accent_gold"] + (240,),
        )
        draw.text((x + 4, y + 5), badge, font=f_num,
                  fill=BRAND["bg_dark"])
        y += bh + int(28 * sf)

        # 헤드라인
        y = ui.draw_headline(draw, card.get("headline", ""), x, y, max_w)
        y += int(16 * sf)

        # 골드 구분선
        draw.rectangle([x, y, x + int(60 * sf), y + 3],
                       fill=BRAND["accent_gold"])
        y += int(24 * sf)

        # 본문
        y = ui.draw_body(draw, card.get("body", ""), x, y, max_w)

        img = ui.footer_bar(img, card.get("source", ""), "2026.09.16")
        return img.convert("RGB")

    # ── 클로징 카드 ──────────────────────────────────────────────────────────

    def render_closing(self, card: dict, total: int) -> Image.Image:
        img = self._base(seed=99)
        ui  = self.ui
        sf  = self.w / 1080

        img = ui.header_bar(img, total, total)

        # 클로징 전용 중앙 패널
        h_hdr  = int(90 * sf) if self.port else int(64 * sf)
        foot_h = int(72 * sf) if self.port else int(54 * sf)
        pad    = int(80 * sf)
        img    = ui.content_panel(img, h_hdr + pad, self.h - foot_h - pad,
                                   alpha=220)

        draw = ImageDraw.Draw(img.convert("RGBA"))
        img  = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        cx = self.w // 2
        sf = self.w / 1080

        # 로고 대형 출력
        f_big = _load_font("logo", int(88 * sf))
        logo  = "이판사판"
        lw, lh = _get_text_size(logo, f_big)
        cy   = self.h // 2 - int(120 * sf)
        _draw_text_shadow(draw, (cx - lw // 2, cy), logo, f_big,
                          BRAND["text_white"], shadow_offset=5)

        # 핸들
        f_hd  = _load_font("source", int(40 * sf))
        handle = "@2pan4pan"
        hw, hh = _get_text_size(handle, f_hd)
        draw.text((cx - hw // 2, cy + lh + int(16 * sf)), handle,
                  font=f_hd, fill=BRAND["accent_cyan"])

        # 구분선
        dy = cy + lh + hh + int(40 * sf)
        line_w = int(200 * sf)
        draw.rectangle([cx - line_w // 2, dy, cx + line_w // 2, dy + 3],
                       fill=BRAND["accent_gold"])
        dy += int(30 * sf)

        # CTA
        f_cta = _load_font("subhead", int(36 * sf))
        cta   = card.get("body", "구독하고 정치 이슈\n가장 먼저 받아보세요!")
        cta_lines = cta.split("\n")
        for line in cta_lines:
            tw, th = _get_text_size(line, f_cta)
            draw.text((cx - tw // 2, dy), line, font=f_cta,
                      fill=BRAND["text_silver"])
            dy += int(th * 1.5)

        # 소스/사이트
        if card.get("source"):
            f_url = _load_font("source", int(28 * sf))
            uw, _ = _get_text_size(card["source"], f_url)
            draw.text((cx - uw // 2, dy + int(20 * sf)), card["source"],
                      font=f_url, fill=BRAND["accent_cyan"])

        img = ui.footer_bar(img, "", "2026.09.16")
        return img.convert("RGB")

    # ── 썸네일 ──────────────────────────────────────────────────────────────

    def render_thumbnail(self, script: dict) -> Image.Image:
        """YouTube 썸네일 (1280×720)."""
        W, H = 1280, 720
        img  = _make_video_bg(W, H, seed=77)
        sf   = W / 1080
        ui_t = NewsUIKit(W, H, False)

        # 헤더
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)

        # 좌측 세로 액센트 바
        draw.rectangle([0, 0, int(10 * sf), H], fill=BRAND["accent_red"])

        # 배경 패널
        draw.rounded_rectangle([int(40 * sf), int(60 * sf),
                                  W - int(40 * sf), H - int(60 * sf)],
                                 radius=int(16 * sf), fill=(8, 10, 20, 200))

        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(img)

        pad  = int(80 * sf)
        y    = int(90 * sf)
        max_w = W - pad * 2

        # 속보 태그
        f_brk = _load_font("breaking", int(32 * sf))
        brk   = "  속  보  "
        bw, bh = _get_text_size(brk, f_brk)
        draw.rounded_rectangle([pad, y, pad + bw + 8, y + bh + 8],
                                radius=4, fill=BRAND["accent_red"])
        draw.text((pad + 4, y + 4), brk, font=f_brk, fill=BRAND["text_white"])
        y += bh + int(24 * sf)

        # 제목
        f_hl = _load_font("headline", int(68 * sf))
        title = script.get("title", script.get("topic", ""))
        lines = _wrap_text(title, f_hl, max_w)
        for line in lines[:3]:
            _draw_text_shadow(draw, (pad, y), line, f_hl,
                              BRAND["text_white"], shadow_offset=4)
            y += int(f_hl.size * 1.3)

        # 구분선
        y += int(10 * sf)
        draw.rectangle([pad, y, pad + int(100 * sf), y + 5],
                       fill=BRAND["accent_gold"])
        y += int(28 * sf)

        # 설명
        if script.get("description"):
            f_desc = _load_font("body", int(30 * sf))
            desc   = script["description"][:60] + "…"
            draw.text((pad, y), desc, font=f_desc, fill=BRAND["text_silver"])

        # 로고 (우하단)
        f_logo = _load_font("logo", int(42 * sf))
        logo   = "이판사판  |  @2pan4pan"
        lw, lh = _get_text_size(logo, f_logo)
        draw.text((W - lw - int(50 * sf), H - lh - int(70 * sf)),
                  logo, font=f_logo, fill=BRAND["accent_gold"])

        return img.convert("RGB")


# ── 퍼블릭 API ────────────────────────────────────────────────────────────────

def make_cards_ipsp(
    script: dict,
    output_dir: Path,
    fmt: Literal["16:9", "9:16"] = "16:9",
) -> list[Path]:
    """
    script의 cards 목록을 이판사판 스타일로 렌더링.
    Returns: 생성된 카드 이미지 파일 경로 목록
    """
    renderer  = IPSPCardRenderer(fmt=fmt)
    cards_dir = output_dir / f"cards_{fmt.replace(':', 'x')}"
    cards_dir.mkdir(parents=True, exist_ok=True)

    cards = script.get("cards", [])
    total = len(cards)
    paths = []

    for card in cards:
        n    = card.get("card_num", 1)
        typ  = card.get("type", "content")
        ctype = card.get("category", _guess_category(card))

        # 카테고리 주입
        card = {**card, "category": ctype}

        if typ == "cover":
            img = renderer.render_cover(card, total)
        elif typ == "closing":
            img = renderer.render_closing(card, total)
        else:
            img = renderer.render_content(card, total)

        p = cards_dir / f"card_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=95, subsampling=0)
        paths.append(p)
        print(f"  [IPSP] 카드 저장: {p.name}  ({fmt})")

    return paths


def make_thumbnail_ipsp(script: dict, output_dir: Path) -> Path:
    """YouTube 썸네일 (1280×720) 렌더링."""
    renderer = IPSPCardRenderer(fmt="16:9")
    img      = renderer.render_thumbnail(script)
    p        = output_dir / "thumbnail_ipsp.jpg"
    img.save(str(p), "JPEG", quality=95, subsampling=0)
    print(f"  [IPSP] 썸네일 저장: {p}")
    return p


def _guess_category(card: dict) -> str:
    """카드 헤드라인에서 카테고리 추측."""
    hl = card.get("headline", "")
    if "파병" in hl:
        return "국방·외교"
    if "개헌" in hl:
        return "헌법·정치"
    if "공소" in hl or "검찰" in hl:
        return "법조·사법"
    if "대통령" in hl or "기자회견" in hl:
        return "청와대·정치"
    return "이판사판 단독"


# ── 독립 실행 테스트 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json, sys
    from datetime import datetime

    ROOT      = Path(__file__).parent.parent
    SCRIPT_PATH = ROOT / "outputs" / "card_news_fallback_20260916_185439" / "script.json"

    if not SCRIPT_PATH.exists():
        print(f"script.json 없음: {SCRIPT_PATH}")
        sys.exit(1)

    script = json.loads(SCRIPT_PATH.read_text("utf-8"))
    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "outputs" / f"ipsp_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)

    print("=== 이판사판 카드 렌더링 (16:9) ===")
    paths_169 = make_cards_ipsp(script, outdir, fmt="16:9")

    print("=== 이판사판 카드 렌더링 (9:16) ===")
    paths_916 = make_cards_ipsp(script, outdir, fmt="9:16")

    print("=== 썸네일 ===")
    thumb = make_thumbnail_ipsp(script, outdir)

    print(f"\n✅ 완료 → {outdir}")
    print(f"  16:9 카드 : {len(paths_169)}장")
    print(f"  9:16 카드 : {len(paths_916)}장")
    print(f"  썸네일    : {thumb.name}")
