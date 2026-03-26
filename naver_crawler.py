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
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []

        # 블로그 검색 결과 컨테이너
        items = soup.select(".api_txt_lines.total_tit")
        snippets = soup.select(".api_txt_lines.dsc_txt")

        for i, item in enumerate(items[:num]):
            entry = {
                "title": item.get_text(strip=True),
                "url": item.get("href", ""),
                "snippet": "",
            }
            if i < len(snippets):
                entry["snippet"] = snippets[i].get_text(strip=True)
            results.append(entry)

        # 결과가 없으면 대체 셀렉터 시도
        if not results:
            for item in soup.select(".title_link, .link_tit")[:num]:
                results.append({
                    "title": item.get_text(strip=True),
                    "url": item.get("href", ""),
                    "snippet": "",
                })

        return results

    except Exception as e:
        print(f"[크롤링 오류] 블로그 검색 실패: {e}")
        return []


def search_naver_shopping(keyword, num=5):
    """네이버 쇼핑 검색 결과 크롤링

    Returns:
        list[dict]: [{"title": ..., "price": ..., "url": ..., "mall": ...}, ...]
    """
    encoded = urllib.parse.quote(keyword)
    url = f"https://search.shopping.naver.com/search/all?query={encoded}"

    try:
        resp = requests.get(url, headers=CRAWL_HEADERS, timeout=CRAWL_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []

        # 쇼핑 상품 목록
        items = soup.select(".product_item, .basicList_item__0T9JD")
        for item in items[:num]:
            title_el = item.select_one(
                ".product_title, .basicList_title__VfX3c, a[class*='title']"
            )
            price_el = item.select_one(
                ".product_num, .price_num__S2p_v, [class*='price']"
            )
            link_el = item.select_one("a[href]")
            mall_el = item.select_one(
                ".product_mall, .basicList_mall__O2yNt, [class*='mall']"
            )

            results.append({
                "title": title_el.get_text(strip=True) if title_el else "",
                "price": price_el.get_text(strip=True) if price_el else "",
                "url": link_el["href"] if link_el else "",
                "mall": mall_el.get_text(strip=True) if mall_el else "",
            })

        # JSON 데이터 추출 시도 (SSR 데이터)
        if not results:
            results = _extract_shopping_json(soup, num)

        return results

    except Exception as e:
        print(f"[크롤링 오류] 쇼핑 검색 실패: {e}")
        return []


def _extract_shopping_json(soup, num):
    """페이지 내 <script> 태그에서 SSR JSON 데이터 추출 시도"""
    import json

    results = []
    for script in soup.select("script"):
        text = script.string or ""
        if "products" not in text and "items" not in text:
            continue
        try:
            # __NEXT_DATA__ 패턴
            if "__NEXT_DATA__" in text:
                start = text.index("{")
                data = json.loads(text[start:])
                products = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("initialState", {})
                    .get("products", {})
                    .get("list", [])
                )
                for p in products[:num]:
                    item = p.get("item", p)
                    results.append({
                        "title": item.get("productTitle", ""),
                        "price": item.get("price", ""),
                        "url": item.get("mallProductUrl", ""),
                        "mall": item.get("mallName", ""),
                    })
                if results:
                    break
        except (json.JSONDecodeError, ValueError, KeyError):
            continue

    return results
