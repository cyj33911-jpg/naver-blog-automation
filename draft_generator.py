# draft_generator.py - Gemini API로 블로그 초안(TXT) 생성

import os
import google.generativeai as genai

from config import GEMINI_MODEL


def generate_draft(api_key, product_info, crawled_data, image_paths, output_dir):
    """제품 정보 + 크롤링 데이터를 바탕으로 블로그 초안 TXT를 생성한다.

    생성되는 TXT는 v1 자동 발행 형식과 호환된다:
        첫 줄: 제목
        (빈 줄)
        본문 (중간에 [사진N] 파일명 포함)

    Args:
        api_key: Google Gemini API 키
        product_info: image_analyzer에서 반환된 제품 정보 dict
        crawled_data: naver_crawler에서 반환된 {"blog": [...], "shopping": [...]}
        image_paths: 사용자가 선택한 이미지 파일 경로 리스트
        output_dir: TXT 저장 디렉토리

    Returns:
        str: 생성된 TXT 파일 경로. 실패 시 None
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = _build_prompt(product_info, crawled_data, image_paths)

    response = model.generate_content(prompt)
    draft_text = response.text

    # TXT 파일 저장
    product_name = product_info.get("제품명", "제품").replace("/", "_").replace("\\", "_")
    filename = f"{product_name}_초안.txt"
    filepath = os.path.join(output_dir, filename)

    # 이미지 파일을 출력 디렉토리로 복사 (원본과 다른 경우)
    _copy_images_if_needed(image_paths, output_dir)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(draft_text)

    return filepath


def _build_prompt(product_info, crawled_data, image_paths):
    """Gemini API에 보낼 프롬프트를 구성한다."""

    # 이미지 파일명 목록
    image_filenames = [os.path.basename(p) for p in image_paths]
    image_tags = "\n".join(
        f"  [사진{i+1}] {name}" for i, name in enumerate(image_filenames)
    )

    # 크롤링 데이터 정리
    blog_info = ""
    for i, b in enumerate(crawled_data.get("blog", []), 1):
        blog_info += f"  {i}. {b['title']}\n"
        if b.get("snippet"):
            blog_info += f"     {b['snippet']}\n"
    if not blog_info:
        blog_info = "  (검색 결과 없음)\n"

    shopping_info = ""
    for i, s in enumerate(crawled_data.get("shopping", []), 1):
        line = f"  {i}. {s['title']}"
        if s.get("price"):
            line += f" - {s['price']}"
        if s.get("mall"):
            line += f" ({s['mall']})"
        shopping_info += line + "\n"
    if not shopping_info:
        shopping_info = "  (검색 결과 없음)\n"

    prompt = f"""당신은 네이버 블로그 전문 작가입니다.
아래 제품 정보와 참고 자료를 바탕으로 자연스러운 블로그 글을 작성해주세요.

## 제품 정보
- 제품명: {product_info.get('제품명', '알 수 없음')}
- 브랜드: {product_info.get('브랜드', '알 수 없음')}
- 카테고리: {product_info.get('카테고리', '알 수 없음')}
- 특징: {product_info.get('특징', '알 수 없음')}

## 네이버 블로그 참고 글
{blog_info}
## 네이버 쇼핑 정보
{shopping_info}
## 사용 가능한 이미지
{image_tags}

## 작성 규칙 (반드시 지켜주세요)

1. **첫 줄**에 블로그 글 제목만 작성 (앞에 "제목:" 붙이지 말 것)
2. 제목 다음에 **빈 줄 하나**
3. 본문 작성 (자연스럽고 친근한 블로그 톤)
4. 본문 중간중간 적절한 위치에 아래 이미지 태그를 삽입:
{image_tags}
5. 이미지 태그는 반드시 별도 줄에 단독으로 작성
6. 글 길이: 800~1500자 정도
7. 마크다운 문법 사용하지 말 것 (**, ##, - 등 금지)
8. 순수 텍스트만 사용

## 출력 형식 예시

맛있는 커피 리뷰 - OO 브랜드

안녕하세요, 오늘은 제가 최근에 발견한 커피를 소개해드릴게요.

[사진1] coffee1.jpg

이 커피는 정말 향이 좋은데요...

[사진2] coffee2.jpg

가격도 합리적이라 추천드립니다.
"""
    return prompt


def _copy_images_if_needed(image_paths, output_dir):
    """이미지가 출력 디렉토리에 없으면 복사"""
    import shutil

    for src in image_paths:
        dst = os.path.join(output_dir, os.path.basename(src))
        if os.path.abspath(src) != os.path.abspath(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass
