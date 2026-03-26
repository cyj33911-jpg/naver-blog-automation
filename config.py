# config.py - 설정값 모듈

# 타이핑 속도 (초)
TYPING_MIN_DELAY = 0.05
TYPING_MAX_DELAY = 0.15

# 문단 끝 대기 시간 (초)
PARAGRAPH_MIN_DELAY = 0.3
PARAGRAPH_MAX_DELAY = 0.8

# 글 작성 간 대기 시간 (초)
POST_MIN_DELAY = 30
POST_MAX_DELAY = 120

# 페이지 로드 대기 시간 (초)
PAGE_LOAD_TIMEOUT = 20

# 네이버 URL
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# 네이버 블로그 글쓰기 URL 템플릿 ({blog_id} 치환)
BLOG_WRITE_URL = "https://blog.naver.com/{blog_id}/postwrite"

# 네이버 블로그 에디터 CSS 셀렉터 (후보순 - 첫 번째 매칭 사용)
SELECTORS = {
    # 로그인
    "login_id": "#id",
    "login_pw": "#pw",
    "login_btn": "#log\\.login",

    # 에디터 iframe 후보들
    "editor_iframes": [
        "iframe#mainFrame",
        "iframe[name='mainFrame']",
        "iframe[src*='postwrite']",
        "iframe[src*='PostWrite']",
    ],

    # 제목 영역 후보들
    "title_areas": [
        ".se-title-text .se-text-paragraph",
        ".se-title-text",
        "span.se-fs-",
        "[placeholder*='제목']",
        ".title_area",
        "#title",
    ],

    # 본문 영역 후보들
    "body_areas": [
        ".se-component.se-text .se-text-paragraph",
        ".se-component-content .se-text-paragraph",
        ".se-main-container .se-component.se-text",
        "#content",
        ".content_area",
    ],

    # 발행 버튼 후보들
    "publish_btns": [
        "button.publish_btn__Y4pat",
        "[class*='publish_btn']",
        "button[data-testid='publish']",
        #  "발행" 텍스트가 포함된 버튼은 XPath로 처리
    ],

    # 발행 확인 버튼 후보들
    "publish_confirm_btns": [
        "button.confirm_btn__WEaBq",
        "[class*='confirm_btn']",
        "button[data-testid='confirm']",
    ],
}

# 수동 로그인 대기 시간 (초) - 캡차/2차 인증 대응
MANUAL_LOGIN_WAIT = 120

# --- v2: 블로그 초안 생성 설정 ---

# API 키 파일 경로 (프로그램과 같은 디렉토리)
import os
API_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")

# Claude API 모델
CLAUDE_MODEL = "claude-sonnet-4-6"

# 크롤링 설정
CRAWL_TIMEOUT = 10
CRAWL_BLOG_COUNT = 5
CRAWL_SHOPPING_COUNT = 5

# HTTP 요청 헤더
CRAWL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
