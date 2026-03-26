# file_scanner.py - 디렉토리 탐색 및 TXT 파일 수집 모듈

import os
import re


def find_all_txt_files(root_dir):
    """디렉토리를 재귀적으로 탐색하여 모든 txt 파일 경로를 반환"""
    txt_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.txt'):
                txt_files.append(os.path.join(dirpath, filename))
    return sorted(txt_files)


def read_txt_file(filepath):
    """TXT 파일을 읽어서 제목과 콘텐츠 블록을 파싱하여 반환

    형식:
        첫 번째 줄: 제목 (또는 "제목: 내용" 형태)
        (빈 줄)
        나머지: 본문 (중간에 [사진N] 파일명, [영상] 파일명 포함 가능)

    Returns:
        (title, blocks) 튜플.
        blocks = [{"type": "text"/"image"/"video", "content"/"filepath": ...}, ...]
        파싱 실패 시 (None, None) 반환.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[오류] 파일 읽기 실패: {filepath} - {e}")
        return None, None

    lines = content.split('\n')
    if not lines:
        return None, None

    # 제목 추출
    title = lines[0].strip()
    if title.startswith('제목:'):
        title = title[len('제목:'):].strip()
    elif title.startswith('제목 :'):
        title = title[len('제목 :'):].strip()

    # 본문 시작 위치
    body_start = 1
    if len(lines) > 1 and lines[1].strip() == '':
        body_start = 2

    # TXT 파일이 있는 디렉토리 (미디어 파일 경로 해석용)
    txt_dir = os.path.dirname(os.path.abspath(filepath))

    # 미디어 참조 패턴
    image_pattern = re.compile(r'^\[사진\d*\]\s*(.+)$')
    video_pattern = re.compile(r'^\[영상\d*\]\s*(.+)$')

    blocks = []
    text_buffer = []

    for line in lines[body_start:]:
        stripped = line.strip()

        # 구분선, 태그 라인 건너뛰기
        if stripped == '---' or stripped == '===':
            continue
        if stripped.startswith('추천 태그:') or stripped.startswith('태그:'):
            continue

        # 이미지 참조
        img_match = image_pattern.match(stripped)
        if img_match:
            # 이전 텍스트 버퍼 저장
            if text_buffer:
                text = '\n'.join(text_buffer).strip()
                if text:
                    blocks.append({"type": "text", "content": text})
                text_buffer = []

            filename = img_match.group(1).strip()
            img_path = _resolve_media_path(txt_dir, filename)
            if img_path:
                blocks.append({"type": "image", "filepath": img_path, "filename": filename})
            continue

        # 영상 참조
        vid_match = video_pattern.match(stripped)
        if vid_match:
            if text_buffer:
                text = '\n'.join(text_buffer).strip()
                if text:
                    blocks.append({"type": "text", "content": text})
                text_buffer = []

            filename = vid_match.group(1).strip()
            vid_path = _resolve_media_path(txt_dir, filename)
            if vid_path:
                blocks.append({"type": "video", "filepath": vid_path, "filename": filename})
            continue

        # 일반 텍스트
        text_buffer.append(line)

    # 남은 텍스트 버퍼
    if text_buffer:
        text = '\n'.join(text_buffer).strip()
        if text:
            blocks.append({"type": "text", "content": text})

    if not blocks:
        return None, None

    return title, blocks


def _resolve_media_path(txt_dir, filename):
    """미디어 파일의 절대 경로를 찾는다 (같은 디렉토리 및 하위 디렉토리 탐색)"""
    # 같은 디렉토리에서 찾기
    path = os.path.join(txt_dir, filename)
    if os.path.exists(path):
        return os.path.abspath(path)

    # 하위 디렉토리에서 찾기
    for dirpath, dirnames, filenames in os.walk(txt_dir):
        if filename in filenames:
            return os.path.abspath(os.path.join(dirpath, filename))

    # 상위 디렉토리에서 찾기
    parent = os.path.dirname(txt_dir)
    path = os.path.join(parent, filename)
    if os.path.exists(path):
        return os.path.abspath(path)

    print(f"[경고] 미디어 파일을 찾을 수 없음: {filename}")
    return None
