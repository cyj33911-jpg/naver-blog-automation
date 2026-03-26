# image_analyzer.py - Gemini Vision API로 제품 이미지 분석

import os
import google.generativeai as genai
import PIL.Image

from config import GEMINI_MODEL


def analyze_product_image(api_key, image_path):
    """이미지를 Gemini Vision API에 보내 제품 정보를 추출한다.

    Args:
        api_key: Google Gemini API 키
        image_path: 분석할 이미지 파일 경로

    Returns:
        dict: {제품명, 브랜드, 카테고리, 특징, 검색키워드} 또는 실패 시 None
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

    img = PIL.Image.open(image_path)

    prompt = (
        "이 이미지에 있는 제품을 분석해주세요.\n"
        "다음 형식으로 정확히 답변해주세요:\n\n"
        "제품명: (정확한 제품명)\n"
        "브랜드: (브랜드명)\n"
        "카테고리: (제품 카테고리)\n"
        "특징: (주요 특징 3~5개, 쉼표로 구분)\n"
        "검색키워드: (네이버 검색에 사용할 핵심 키워드)"
    )

    response = model.generate_content([prompt, img])
    return _parse_response(response.text)


def _parse_response(text):
    """Gemini 응답 텍스트를 딕셔너리로 파싱"""
    info = {}
    for line in text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info
