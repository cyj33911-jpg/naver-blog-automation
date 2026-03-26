# gui.py - tkinter GUI 모듈

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os

from file_scanner import find_all_txt_files, read_txt_file
from browser import NaverBlogBrowser

# account.txt 경로 (프로그램과 같은 디렉토리)
ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "account.txt")


class NaverBlogApp:
    """네이버 블로그 자동 글쓰기 GUI 애플리케이션"""

    def __init__(self, root):
        self.root = root
        self.root.title("네이버 블로그 자동 글쓰기")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        self.browser = None
        self.is_running = False

        self._build_ui()
        self._load_account()

    def _load_account(self):
        """account.txt에서 계정 정보를 읽어 자동 입력"""
        if not os.path.exists(ACCOUNT_FILE):
            return
        try:
            with open(ACCOUNT_FILE, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines()]
            if len(lines) >= 1 and lines[0]:
                self.id_entry.insert(0, lines[0])
            if len(lines) >= 2 and lines[1]:
                self.pw_entry.insert(0, lines[1])
            if len(lines) >= 3 and lines[2]:
                self.blog_id_entry.delete(0, tk.END)
                self.blog_id_entry.insert(0, lines[2])
        except Exception:
            pass

    def _build_ui(self):
        """UI 구성"""
        # 상단 입력 영역
        input_frame = ttk.LabelFrame(self.root, text="설정", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # ID
        ttk.Label(input_frame, text="네이버 ID:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.id_entry = ttk.Entry(input_frame, width=40)
        self.id_entry.grid(row=0, column=1, padx=(5, 0), pady=3)

        # PW
        ttk.Label(input_frame, text="비밀번호:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.pw_entry = ttk.Entry(input_frame, width=40, show="*")
        self.pw_entry.grid(row=1, column=1, padx=(5, 0), pady=3)

        # 블로그 ID
        ttk.Label(input_frame, text="블로그 ID:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.blog_id_entry = ttk.Entry(input_frame, width=40)
        self.blog_id_entry.grid(row=2, column=1, padx=(5, 0), pady=3)
        self.blog_id_entry.insert(0, "")

        # 버튼 영역
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.upload_btn = ttk.Button(
            btn_frame, text="디렉토리 선택 및 업로드 시작",
            command=self._on_upload_click
        )
        self.upload_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_btn = ttk.Button(
            btn_frame, text="중단", command=self._on_stop_click, state=tk.DISABLED,
            width=10
        )
        self.stop_btn.pack(side=tk.RIGHT)

        # 로그 영역
        log_frame = ttk.LabelFrame(self.root, text="진행 로그", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 9), state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _log(self, message):
        """로그 메시지를 GUI 텍스트 영역에 출력 (스레드 안전)"""
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def _on_upload_click(self):
        """업로드 버튼 클릭 이벤트"""
        # 입력값 검증
        naver_id = self.id_entry.get().strip()
        naver_pw = self.pw_entry.get().strip()
        blog_id_raw = self.blog_id_entry.get().strip()

        if not naver_id or not naver_pw:
            self._log("[오류] 네이버 ID와 비밀번호를 입력해주세요.")
            return
        if not blog_id_raw:
            self._log("[오류] 블로그 ID를 입력해주세요.")
            return

        # 전체 URL 입력 시 블로그 ID만 추출
        blog_id = blog_id_raw
        if "blog.naver.com/" in blog_id:
            # https://blog.naver.com/jiae7658 → jiae7658
            blog_id = blog_id.rstrip("/").split("blog.naver.com/")[-1]
            blog_id = blog_id.split("/")[0].split("?")[0]
        self._log(f"[설정] 블로그 ID: {blog_id}")

        # 디렉토리 선택
        directory = filedialog.askdirectory(title="TXT 파일이 있는 디렉토리를 선택하세요")
        if not directory:
            return

        # 별도 스레드에서 실행 (GUI 프리징 방지)
        self.is_running = True
        self.upload_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        thread = threading.Thread(
            target=self._run_automation,
            args=(naver_id, naver_pw, blog_id, directory),
            daemon=True
        )
        thread.start()

    def _on_stop_click(self):
        """중단 버튼 클릭"""
        self.is_running = False
        self._log("[중단] 사용자가 중단을 요청했습니다. 현재 글 작성 완료 후 중단됩니다.")

    def _run_automation(self, naver_id, naver_pw, blog_id, directory):
        """자동화 작업 실행 (별도 스레드)"""
        try:
            # 1. TXT 파일 수집
            self._log(f"[탐색] 디렉토리 탐색 중: {directory}")
            txt_files = find_all_txt_files(directory)

            if not txt_files:
                self._log("[오류] TXT 파일을 찾을 수 없습니다.")
                return

            self._log(f"[탐색] {len(txt_files)}개의 TXT 파일을 발견했습니다.")

            # 파일 읽기 및 파싱
            posts = []
            for filepath in txt_files:
                title, blocks = read_txt_file(filepath)
                if title and blocks:
                    # 블록 요약 출력
                    img_count = sum(1 for b in blocks if b["type"] == "image")
                    vid_count = sum(1 for b in blocks if b["type"] == "video")
                    media_info = ""
                    if img_count:
                        media_info += f", 사진 {img_count}장"
                    if vid_count:
                        media_info += f", 영상 {vid_count}개"
                    posts.append((filepath, title, blocks))
                    self._log(f"  - {filepath} (제목: {title[:30]}{media_info})")
                else:
                    self._log(f"  - [건너뜀] {filepath} (형식 오류)")

            if not posts:
                self._log("[오류] 유효한 TXT 파일이 없습니다.")
                return

            self._log(f"\n[준비] 총 {len(posts)}개의 글을 작성합니다.\n")

            # 2. 브라우저 시작
            self.browser = NaverBlogBrowser(log_callback=self._log)
            if not self.browser.start_browser():
                return

            # 3. 로그인
            if not self.browser.login(naver_id, naver_pw):
                return

            # 4. 글 작성
            success = 0
            fail = 0
            for i, (filepath, title, blocks) in enumerate(posts, 1):
                if not self.is_running:
                    self._log("[중단] 작업이 중단되었습니다.")
                    break

                self._log(f"\n{'='*50}")
                self._log(f"[진행] {i}/{len(posts)} - {filepath}")
                self._log(f"{'='*50}")

                result = self.browser.write_post(blog_id, title, blocks)
                if result:
                    success += 1
                else:
                    fail += 1

                # 다음 글 전 대기
                if i < len(posts) and self.is_running:
                    from config import POST_MIN_DELAY, POST_MAX_DELAY
                    from typer import random_pause
                    delay = random_pause(POST_MIN_DELAY, POST_MAX_DELAY)
                    self._log(f"[대기] 다음 글까지 {delay:.1f}초 대기...")

            self._log(f"\n[완료] 전체 결과: 성공 {success}건, 실패 {fail}건")

        except Exception as e:
            self._log(f"[오류] 예기치 않은 오류: {e}")
        finally:
            # 브라우저 종료 및 UI 복원
            if self.browser:
                self.browser.close()
                self.browser = None
            self.is_running = False
            self.root.after(0, lambda: self.upload_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
