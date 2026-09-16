#!/usr/bin/env bash
# ============================================================
# setup.sh — 첫 실행 환경 구성 스크립트
# ============================================================
# 사용법: bash setup.sh
# 필요 권한: apt-get 실행 가능 (sudo 또는 root)

set -e
cd "$(dirname "$0")"

echo "================================================"
echo " 카드뉴스 자동화 — 환경 설정 시작"
echo "================================================"

# ── 1. 시스템 패키지 ────────────────────────────────────────
echo "[1/4] 시스템 패키지 설치 (폰트 + ffmpeg)..."
apt-get update -qq
apt-get install -y -q \
    fonts-nanum \
    fonts-nanum-extra \
    fonts-nanum-coding \
    ffmpeg \
    python3-pip

# 폰트 캐시 갱신
fc-cache -fv >/dev/null 2>&1 || true
echo "      ✓ 완료"

# ── 2. Python 의존성 ─────────────────────────────────────────
echo "[2/4] Python 패키지 설치..."
pip install -r requirements.txt --break-system-packages -q
echo "      ✓ 완료"

# ── 3. 디렉터리 구조 ─────────────────────────────────────────
echo "[3/4] 필요 디렉터리 생성..."
mkdir -p config outputs logs assets/fonts assets/templates
echo "      ✓ 완료"

# ── 4. 설정 파일 ─────────────────────────────────────────────
echo "[4/4] 설정 파일 확인..."
if [ ! -f "config/my_job.json" ]; then
    cp config/sample_job.json config/my_job.json
    echo "      ⚠  config/my_job.json 이 sample_job.json 에서 복사되었습니다."
    echo "         실제 credentials 를 입력하세요."
else
    echo "      ✓ config/my_job.json 이미 존재"
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "      ⚠  .env 파일이 생성되었습니다. 실제 키를 입력하세요."
else
    echo "      ✓ .env 이미 존재"
fi

echo ""
echo "================================================"
echo " ✅ 환경 설정 완료"
echo "================================================"
echo ""
echo "다음 단계:"
echo "  1. config/my_job.json 에 credentials 입력"
echo "  2. config/youtube_client_secret.json 복사"
echo "  3. python src/pipeline.py --config config/my_job.json --no-publish"
echo ""
