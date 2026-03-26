# naver_crawler.py - 네이버 검색 크롤링 모듈

import urllib.parse
import requests
from bs4 import BeautifulSoup

from config import CRAWL_HEADERS, CRAWL_TIMEOUT, CRAWL_BLOG_COUNT, CRAWL_SHOPPING_COUNT


def crawl_product_info(keyword):
    """키워드로 네이버 블로그 + 쇼핑 검색 결과를 수집한다.

    Args:
        keyword: 검색 키워드

    Returns:
        dict: {"blog": [...], "shopping": [...]}
    """
    return {
        "blog": search_naver_blog(keyword, CRAWL_BLOG_COUNT),
        "shopping": search_naver_shopping(keyword, CRAWL_SHOPPING_COUNT),
    }


def search_naver_blog(keyword, num=5):
    """네이버 블로그 검색 결과 크롤링

    Returns:
        list[dict]: [{"title": ..., "snippet": ..., "url": ...}, ...]
    """
    encoded = urllib.parse.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=blog&query={encoded}"

    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # blog.naver.com 링크가 포함된 a 태그에서 제목 추출
        results = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "blog.naver.com" in href and len(text) > 10 and text not in seen:
                # 광고/네비게이션 링크 제외
                if "blog.naver.com›" in text:
                    continue
                seen.add(text)
                results.append({
                    "title": text,
                    "url": href,
                    "snippet": "",
                })

        # 본문 스니펫 매칭 (.desc_wrap)
        snippets = [d.get_text(strip=True) for d in soup.select(".desc_wrap")]
        for i, entry in enumerate(results):
            if i < len(snippets):
                entry["snippet"] = snippets[i]

        return results[:num]

    except Exception as e:
        print(f"[크롤링 오류] 블로그 검색 실패: {e}")
        return []


def search_naver_shopping(keyword, num=5):
    """네이버 통합검색 내 쇼핑 영역에서 상품 정보 크롤링

    Returns:
        list[dict]: [{"title": ..., "price": ..., "url": ..., "mall": ...}, ...]
    """
    encoded = urllib.parse.quote(keyword)
    # 통합검색에서 쇼핑 정보 추출 (쇼핑 전용 페이지는 JS 렌더링 필요)
    url = f"https://search.naver.com/search.naver?query={encoded}"

    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []

        # 쇼핑 영역의 상품 아이템
        items = soup.select("[class*='product_item'], [class*='shop_list'] li, [class*='lst_total'] li")
        for item in items[:num]:
            title_el = item.select_one("[class*='tit'], a[title]")
            price_el = item.select_one("[class*='price'], [class*='prc']")
            link_el = item.select_one("a[href]")
            mall_el = item.select_one("[class*='mall'], [class*='name']")

            title = ""
            if title_el:
                title = title_el.get("title", "") or title_el.get_text(strip=True)

            if title and len(title) > 3:
                results.append({
                    "title": title,
                    "price": price_el.get_text(strip=True) if price_el else "",
                    "url": link_el["href"] if link_el else "",
                    "mall": mall_el.get_text(strip=True) if mall_el else "",
                })

        # 결과 부족 시 쇼핑 링크에서 추가 추출
        if not results:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if ("shopping" in href or "shop" in href) and len(text) > 5:
                    results.append({
                        "title": text,
                        "price": "",
                        "url": href,
                        "mall": "",
                    })
                if len(results) >= num:
                    break

        return results[:num]

    except Exception as e:
        print(f"[크롤링 오류] 쇼핑 검색 실패: {e}")
        return []
