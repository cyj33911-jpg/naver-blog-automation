# 네이버 블로그 자동화 프로그램 - 개발 명세서

## 프로젝트 개요

네이버 블로그에 TXT 파일 기반으로 글을 자동 작성하는 데스크톱 프로그램.
Selenium을 이용하여 실제 브라우저에서 사람이 타이핑하는 것처럼 글을 작성한다.

---

## 기술 스택

- **언어**: Python 3.10+
- **브라우저 자동화**: Selenium WebDriver
- **드라이버 관리**: `webdriver-manager` (크롬 드라이버 자동 업데이트)
- **GUI**: `tkinter` (기본 내장 UI 라이브러리)

---

## 필수 패키지 설치

```bash
pip install selenium webdriver-manager
```

---

## 핵심 기능 요구사항

### 1. 크롬 드라이버 자동 업데이트

- `webdriver-manager`를 사용하여 프로그램 실행 시마다 크롬 드라이버를 최신 버전으로 자동 업데이트한다.

```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

### 2. Selenium 기반 브라우저 제어

- Chrome 브라우저를 Selenium으로 제어한다.
- 네이버 로그인 → 블로그 글쓰기 페이지 이동 → 본문 작성 → 발행까지 자동화한다.

### 3. GUI (tkinter) 구성 요소

프로그램 UI에는 다음 입력 요소가 있어야 한다:

| UI 요소 | 설명 |
|---------|------|
| **ID 입력창** | 네이버 아이디 입력 |
| **PW 입력창** | 네이버 비밀번호 입력 (마스킹 처리) |
| **블로그 글쓰기 URL** | 네이버 블로그 글쓰기 페이지 URL 입력 |
| **업로드 버튼** | 디렉토리 선택 후 자동 글쓰기 시작 |

### 4. TXT 파일 읽기 및 타이핑 입력

- TXT 파일을 읽어서 그 안에 있는 내용을 **타이핑 방식으로 한 글자씩 입력**한다.
- **복사 붙여넣기(Ctrl+V)를 사용하지 않는다.**
- 네이버는 복사 붙여넣기, 체류시간, 탭 전환, 복사 붙여넣기 패턴을 감지하므로, 반드시 타이핑으로 입력해야 한다.

#### 타이핑 시뮬레이션 구현 방향

```python
import time
import random

def type_like_human(element, text):
    """사람처럼 한 글자씩 타이핑하는 함수"""
    for char in text:
        element.send_keys(char)
        # 글자마다 랜덤 딜레이 (0.05초 ~ 0.15초)
        time.sleep(random.uniform(0.05, 0.15))
    # 문단 끝에서 잠시 멈춤
    time.sleep(random.uniform(0.3, 0.8))
```

#### 감지 우회 주의사항

- 탭 전환 최소화: 브라우저 탭을 전환하지 않도록 한다.
- 적절한 체류시간: 글 작성 중간중간 랜덤한 대기 시간을 넣는다.
- 마우스 움직임: 필요 시 마우스 이동 이벤트도 자연스럽게 추가한다.
- 스크롤: 긴 글 작성 시 자연스러운 스크롤 동작을 넣는다.

### 5. 업로드 버튼 동작 (디렉토리 재귀 탐색)

**업로드 버튼을 누르면 다음 순서로 동작한다:**

1. `tkinter.filedialog.askdirectory()`로 대표 디렉토리를 선택한다.
2. 선택한 디렉토리 안에 있는 모든 하위 디렉토리를 **재귀적으로** 탐색한다.
3. 각 디렉토리 안에 있는 `.txt` 파일을 찾는다.
4. 찾은 `.txt` 파일을 순차적으로 읽는다.
5. 각 `.txt` 파일의 내용을 Selenium으로 네이버 블로그에 자동 작성한다.

#### 디렉토리 탐색 구현 방향

```python
import os

def find_all_txt_files(root_dir):
    """디렉토리를 재귀적으로 탐색하여 모든 txt 파일 경로를 반환"""
    txt_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.txt'):
                txt_files.append(os.path.join(dirpath, filename))
    return sorted(txt_files)
```

---

## 프로그램 실행 흐름

```
1. 프로그램 실행
2. GUI 표시 (ID, PW, 블로그 URL 입력)
3. 사용자가 업로드 버튼 클릭
4. 대표 디렉토리 선택 (파일 다이얼로그)
5. 디렉토리 재귀 탐색 → 모든 .txt 파일 수집
6. 크롬 드라이버 자동 업데이트 및 브라우저 실행
7. 네이버 로그인 (ID/PW 입력)
8. 각 .txt 파일에 대해 반복:
   a. 블로그 글쓰기 URL로 이동
   b. TXT 파일 내용 읽기
   c. 제목 입력 (타이핑 방식)
   d. 본문 입력 (타이핑 방식, 한 글자씩)
   e. 발행 버튼 클릭
   f. 다음 글 작성 전 랜덤 대기 (30초~120초)
9. 모든 파일 처리 완료 후 브라우저 종료
```

---

## TXT 파일 형식 규칙

각 TXT 파일은 다음 형식을 따른다:

```
첫 번째 줄: 블로그 글 제목
(빈 줄)
나머지 줄: 블로그 글 본문 내용
```

**예시 (post01.txt):**

```
오늘의 맛집 리뷰 - 강남 파스타

안녕하세요, 오늘은 강남에 있는 파스타 맛집을 소개합니다.
이 가게는 분위기가 정말 좋고...
```

---

## 프로젝트 파일 구조

```
naver-blog-automation/
├── main.py              # 프로그램 진입점 (GUI 실행)
├── gui.py               # tkinter GUI 모듈
├── browser.py           # Selenium 브라우저 제어 모듈
├── typer.py             # 타이핑 시뮬레이션 모듈
├── file_scanner.py      # 디렉토리 탐색 및 TXT 파일 수집
├── config.py            # 설정값 (딜레이, URL 등)
├── requirements.txt     # 패키지 목록
└── README.md            # 사용 설명서
```

---

## 모듈별 상세 설명

### main.py

- 프로그램 진입점
- GUI를 실행하고 이벤트 루프를 시작한다.

### gui.py

- tkinter 기반 UI 구성
- ID/PW/URL 입력 필드, 업로드 버튼, 진행 상황 로그 표시
- 업로드 버튼 클릭 시 `file_scanner`와 `browser` 모듈을 호출한다.

### browser.py

- Selenium WebDriver 초기화 (크롬 드라이버 자동 업데이트 포함)
- 네이버 로그인 함수
- 블로그 글쓰기 페이지 이동 함수
- 제목/본문 입력 함수 (typer 모듈 사용)
- 발행 버튼 클릭 함수

### typer.py

- 한 글자씩 타이핑하는 함수
- 랜덤 딜레이로 사람처럼 보이게 하는 로직
- 줄바꿈, 특수문자 처리

### file_scanner.py

- `os.walk()`를 이용한 재귀 디렉토리 탐색
- `.txt` 파일만 필터링하여 리스트 반환
- 파일 읽기 (UTF-8 인코딩)

### config.py

- 타이핑 속도 범위 (최소/최대 딜레이)
- 글 작성 간 대기 시간
- 네이버 블로그 관련 CSS 셀렉터 / XPath

---

## 주의사항 및 고려사항

1. **네이버 캡차/2차 인증**: 로그인 시 캡차가 뜰 수 있으므로, 수동 로그인 대기 옵션을 넣는 것을 권장한다.
2. **네이버 에디터 구조**: 네이버 스마트에디터는 iframe 내부에 있으므로, `driver.switch_to.frame()`으로 iframe 전환이 필요하다.
3. **글 작성 속도 조절**: 너무 빠르면 봇으로 감지될 수 있으므로 적절한 딜레이를 넣는다.
4. **에러 핸들링**: 네트워크 오류, 요소 미발견 등 예외 처리를 반드시 추가한다.
5. **로그 기록**: 어떤 파일이 성공/실패했는지 로그를 남긴다.
6. **한글 입력 이슈**: Selenium에서 한글 입력 시 `send_keys()` 호환성 문제가 있을 수 있으므로 `pyperclip` + `ActionChains` 조합 또는 JavaScript `document.execCommand('insertText')` 사용을 고려한다.

---

## 추가 개선 아이디어 (선택)

- 글 작성 완료 후 작성된 글 URL 수집 및 저장
- 예약 발행 기능
- 카테고리 자동 선택
- 태그 자동 입력 (TXT 파일에 태그 정보 포함)
- 이미지 자동 첨부 (디렉토리 내 이미지 파일 탐지)
- 작성 진행률 표시 (프로그레스 바)
- 작업 중단/재개 기능
