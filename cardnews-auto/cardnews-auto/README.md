# 데이뉴스 — 유튜브 카드뉴스 자동화 파이프라인

정치·시사 카드뉴스를 자동으로 리서치 → 스크립트 생성 → 이미지 제작 → 멀티플랫폼 발행하는 완전 자동화 파이프라인.

---

## 아키텍처

```
리서치(yt-dlp + 네이버 뉴스) → Claude API 스크립트 생성
→ Pillow 카드 이미지 제작 → ffmpeg 영상 변환
→ YouTube / Instagram / 네이버 블로그 / 티스토리 자동 발행
```

---

## 빠른 시작

```bash
# 1. 환경 설정
bash setup.sh

# 2. credentials 입력
nano config/my_job.json

# 3. 테스트 실행 (발행 없이)
python src/pipeline.py --config config/my_job.json --no-publish

# 4. 스텝별 실행
python src/pipeline.py --config config/my_job.json --step research
python src/pipeline.py --config config/my_job.json --step script
python src/pipeline.py --config config/my_job.json --step cards
python src/pipeline.py --config config/my_job.json --step publish
```

---

## API 설정 가이드

### 1. Anthropic API 키

1. [console.anthropic.com](https://console.anthropic.com) 접속
2. **API Keys** → **Create Key**
3. 발급된 키를 `config/my_job.json` > `credentials.anthropic_key_value` 에 입력
   - 또는 Google Drive 루트에 `anthropic_key.txt` 로 저장

---

### 2. YouTube Data API v3 (업로드)

1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 프로젝트 생성 또는 선택
3. **APIs & Services** → **Library** → `YouTube Data API v3` 활성화
4. **OAuth consent screen** 설정:
   - User type: External
   - App name, 지원 이메일 입력
   - Scopes: `youtube.upload` 추가
   - Test users 에 본인 Gmail 추가
5. **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**:
   - Application type: Desktop app
   - 다운로드한 JSON → `config/youtube_client_secret.json` 으로 저장
6. 첫 실행 시 브라우저 인증 창 → 승인 → 토큰 자동 저장 (`config/youtube_token.json`)

> 💡 **팁**: 앱이 Google 검수를 통과하지 않아도 테스트 사용자로 추가하면 개인 업로드 가능.

---

### 3. Instagram Graph API (카루셀 포스팅)

> ⚠️ Instagram API 는 **비즈니스 계정** + **Facebook 페이지 연결** 필수.

1. [Meta for Developers](https://developers.facebook.com) 접속
2. **앱 만들기** → Business 유형
3. **Instagram Graph API** 제품 추가
4. **Instagram Basic Display** → Instagram 계정 연결
5. 액세스 토큰 발급:
   ```
   Graph API Explorer → 권한 체크:
   - instagram_basic
   - instagram_content_publish
   - pages_read_engagement
   ```
6. 발급된 장기 토큰(Long-lived token) → `config/my_job.json` > `credentials.instagram_access_token`
7. Instagram 사용자 ID → `credentials.instagram_user_id`

> ⚠️ Instagram API 는 **공개 URL 이미지**만 허용. 로컬 파일 직접 업로드 불가.
> 현재 버전: Google Drive 공유 링크를 `image_urls` 에 수동 입력하거나 YouTube 업로드 후 링크 활용.

---

### 4. 네이버 블로그 Open API

1. [네이버 개발자센터](https://developers.naver.com) 접속 → **Application** → **애플리케이션 등록**
2. 사용 API: **블로그** 선택
3. 환경: **PC 웹** → 서비스 URL 입력 (없으면 localhost 가능)
4. 등록 후 **Client ID**, **Client Secret** 확인
5. `config/my_job.json` > `credentials` 에 입력:
   ```json
   "naver_client_id": "발급된_Client_ID",
   "naver_client_secret": "발급된_Client_Secret"
   ```

> ⚠️ 네이버 블로그 API 는 현재 **제한적으로 운영** 중. 일부 계정은 신청 필요.

---

### 5. 티스토리 Open API

1. [티스토리 앱 등록](https://www.tistory.com/guide/api/manage/register) 접속
2. 앱 이름, 서비스 URL, Callback URL 입력
3. **Client ID**, **Client Secret** 확인
4. OAuth 2.0 액세스 토큰 발급:
   ```
   브라우저에서 접속:
   https://www.tistory.com/oauth/authorize
     ?client_id=<발급된_Client_ID>
     &redirect_uri=<등록한_Callback_URL>
     &response_type=code
   
   → 코드 획득 후:
   POST https://www.tistory.com/oauth/access_token
     client_id=...&client_secret=...&code=...&grant_type=authorization_code
   ```
5. 발급된 `access_token` → `credentials.tistory_access_token`
6. 블로그 이름 (URL 의 subdomain) → `credentials.tistory_blog_name`

---

## 설정 파일 구조 (`config/my_job.json`)

| 키 | 설명 |
|----|------|
| `job_id` | 작업 식별자 (출력 폴더명에 사용) |
| `topic.main` | 주요 주제 |
| `topic.keywords` | 검색 키워드 목록 |
| `content.card_count` | 카드 장수 (기본 8장) |
| `require_approval` | `true` = 발행 전 검토 필요, `false` = 자동 발행 |
| `publish.*.enabled` | 각 플랫폼 발행 활성화 여부 |

---

## 출력 구조

```
outputs/
└── daenews_main_20251201_120000/
    ├── state.json          # 실행 상태 (resume 지원)
    ├── sources.json        # 리서치 결과
    ├── script.json         # 카드뉴스 스크립트
    ├── article.json        # 기사 원고
    ├── cards/
    │   ├── card_01.jpg
    │   ├── card_02.jpg
    │   └── ...
    ├── thumbnail.jpg
    ├── video.mp4
    └── video_shorts.mp4
```

---

## Claude Cowork 예약 실행 설정

1. Claude Cowork 에서 **예약 작업 생성**
2. 프롬프트:
   ```
   아래 명령을 실행하세요:
   1. Google Drive 에서 anthropic_key.txt 를 읽어 ANTHROPIC_API_KEY 환경변수에 설정
   2. python /home/claude/cardnews-auto/scheduled_runner.py
   ```
3. 실행 주기 설정 (예: 매일 오전 6시)

---

## 보안 주의사항

- `config/my_job.json` → **git 에 커밋 금지** (`.gitignore` 에 포함됨)
- `config/youtube_client_secret.json` → **git 에 커밋 금지**
- `config/youtube_token.json` → **git 에 커밋 금지**
- `.env` → **git 에 커밋 금지**
- API 키를 코드나 로그에 출력하지 말 것

---

## 라이선스

MIT — 개인/상업적 용도 모두 사용 가능.
