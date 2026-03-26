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
