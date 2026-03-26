# tone_cloner.py - 기존 블로그 톤 분석 및 클론 모듈

import os
import json
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import google.generativeai as genai

from config import CRAWL_HEADERS, CRAWL_TIMEOUT, GEMINI_MODEL

TONE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tone_profile.json")


def crawl_blog_posts(blog_id, num=5):
    """블로그의 최근 글을 크롤링한다.

    Args:
        blog_id: 네이버 블로그 ID
        num: 가져올 글 수

    Returns:
        list[dict]: [{"title": ..., "content": ...}, ...]
    """
    # 1차: RSS 피드 시도
    posts = _crawl_via_rss(blog_id, num)
    if posts:
        return posts

    # 2차: 블로그 페이지 직접 크롤링
    return _crawl_via_page(blog_id, num)


def analyze_tone(api_key, posts):
    """Gemini로 블로그 글들의 톤/스타일을 분석한다.

    Args:
        api_key: Gemini API 키
        posts: crawl_blog_posts()에서 반환된 글 목록

    Returns:
        dict: {"summary": 톤 요약, "style": 스타일 설명, "examples": 예시 표현들}
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # 글 내용을 프롬프트에 포함
    posts_text = ""
    for i, post in enumerate(posts, 1):
        content = post["content"][:800]  # 각 글 800자까지
        posts_text += f"\n--- 글 {i}: {post['title']} ---\n{content}\n"

    prompt = f"""아래는 한 블로거가 작성한 실제 블로그 글들입니다.
이 블로거의 글쓰기 톤과 스타일을 정밀하게 분석해주세요.

{posts_text}

다음 형식으로 정확히 답변해주세요:

말투: (해요체/합니다체/반말 등 구체적인 말투 스타일)
어조: (밝은/차분한/유머러스한/진지한 등)
특징적 표현: (자주 사용하는 표현이나 패턴 5개, 쉼표로 구분)
문장 길이: (짧은/보통/긴 문장 선호)
문단 구성: (짧은 문단/긴 문단, 줄바꿈 빈도)
감정 표현: (감정 표현 많음/적당/절제됨)
독자 호칭: (여러분/친구들/독자님 등 독자를 부르는 방식)
글 구조: (도입-본론-마무리 패턴 설명)
전체 톤 요약: (이 블로거의 글쓰기 스타일을 3~4문장으로 요약)"""

    response = model.generate_content(prompt)
    return _parse_tone(response.text)


def save_tone(tone_data):
    """톤 프로필을 파일에 저장"""
    with open(TONE_FILE, "w", encoding="utf-8") as f:
        json.dump(tone_data, f, ensure_ascii=False, indent=2)


def load_tone():
    """저장된 톤 프로필 로드. 없으면 None"""
    if not os.path.exists(TONE_FILE):
        return None
    try:
        with open(TONE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_tone_prompt(tone_data):
    """톤 데이터를 프롬프트용 텍스트로 변환"""
    if not tone_data:
        return ""

    lines = []
    for key, value in tone_data.items():
        if key != "raw" and value:
            lines.append(f"- {key}: {value}")

    return "\n".join(lines)


# --- 내부 함수 ---

def _crawl_via_rss(blog_id, num):
    """RSS 피드에서 블로그 글 가져오기"""
    url = f"https://rss.blog.naver.com/{blog_id}.xml"
    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"

        root = ET.fromstring(resp.text)
        posts = []

        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            desc = item.findtext("description", "").strip()
            # HTML 태그 제거
            content = BeautifulSoup(desc, "html.parser").get_text(strip=True)
            if title and content and len(content) > 50:
                posts.append({"title": title, "content": content})
            if len(posts) >= num:
                break

        return posts
    except Exception:
        return []


def _crawl_via_page(blog_id, num):
    """블로그 페이지에서 직접 최근 글 목록 + 내용 크롤링"""
    # 최근 글 목록 가져오기
    list_url = f"https://blog.naver.com/PostList.naver?blogId={blog_id}&categoryNo=0&from=postList"
    try:
        resp = requests.get(list_url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 글 링크 수집
        post_urls = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if f"/{blog_id}/" in href and "logNo=" not in href:
                if href.startswith("/"):
                    href = "https://blog.naver.com" + href
                if href not in post_urls:
                    post_urls.append(href)

        posts = []
        for url in post_urls[:num]:
            post = _crawl_single_post(url)
            if post:
                posts.append(post)

        return posts
    except Exception:
        return []


def _crawl_single_post(url):
    """개별 블로그 글 크롤링"""
    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        title = ""
        title_el = soup.select_one(".se-title-text, .pcol1, .itemSubjectBoldfont")
        if title_el:
            title = title_el.get_text(strip=True)

        content = ""
        body_el = soup.select_one(".se-main-container, #postViewArea, .post-view")
        if body_el:
            content = body_el.get_text(separator="\n", strip=True)

        if title and content and len(content) > 50:
            return {"title": title, "content": content}
    except Exception:
        pass
    return None


def _parse_tone(text):
    """Gemini 응답을 딕셔너리로 파싱"""
    tone = {"raw": text}
    for line in text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lstrip("- ")
            tone[key] = value.strip()
    return tone
