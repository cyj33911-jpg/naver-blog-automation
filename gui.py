# gui.py - tkinter GUI 모듈 (v2: 탭 구조)

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os

from file_scanner import find_all_txt_files, read_txt_file
from browser import NaverBlogBrowser

# 파일 경로 (프로그램과 같은 디렉토리)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(BASE_DIR, "account.txt")
API_KEY_FILE = os.path.join(BASE_DIR, "api_key.txt")


class NaverBlogApp:
    """네이버 블로그 자동 글쓰기 GUI 애플리케이션 (v2)"""

    def __init__(self, root):
        self.root = root
        self.root.title("네이버 블로그 자동화 v2")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        self.browser = None
        self.is_running = False

        # v2: 초안 생성용
        self.selected_images = []
        self.is_generating = False

        self._build_ui()
        self._load_account()
        self._load_api_key()

    # ──────────────────────────────────────────────
    #  UI 구성
    # ──────────────────────────────────────────────

    def _build_ui(self):
        """탭 기반 UI 구성"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 탭 1: 블로그 자동 발행 (v1)
        publish_frame = ttk.Frame(self.notebook)
        self.notebook.add(publish_frame, text=" 블로그 자동 발행 ")
        self._build_publish_tab(publish_frame)

        # 탭 2: 블로그 초안 생성 (v2)
        draft_frame = ttk.Frame(self.notebook)
        self.notebook.add(draft_frame, text=" 블로그 초안 생성 ")
        self._build_draft_tab(draft_frame)

    # ── 탭 1: 블로그 자동 발행 ──

    def _build_publish_tab(self, parent):
        """v1 기존 기능: TXT 기반 자동 발행"""
        # 상단 입력 영역
        input_frame = ttk.LabelFrame(parent, text="설정", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(input_frame, text="네이버 ID:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.id_entry = ttk.Entry(input_frame, width=40)
        self.id_entry.grid(row=0, column=1, padx=(5, 0), pady=3)

        ttk.Label(input_frame, text="비밀번호:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.pw_entry = ttk.Entry(input_frame, width=40, show="*")
        self.pw_entry.grid(row=1, column=1, padx=(5, 0), pady=3)

        ttk.Label(input_frame, text="블로그 ID:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.blog_id_entry = ttk.Entry(input_frame, width=40)
        self.blog_id_entry.grid(row=2, column=1, padx=(5, 0), pady=3)

        # 버튼 영역
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.upload_btn = ttk.Button(
            btn_frame, text="디렉토리 선택 및 업로드 시작",
            command=self._on_upload_click,
        )
        self.upload_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_btn = ttk.Button(
            btn_frame, text="중단", command=self._on_stop_click,
            state=tk.DISABLED, width=10,
        )
        self.stop_btn.pack(side=tk.RIGHT)

        # 로그 영역
        log_frame = ttk.LabelFrame(parent, text="진행 로그", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 9), state=tk.DISABLED,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ── 탭 2: 블로그 초안 생성 ──

    def _build_draft_tab(self, parent):
        """v2 신규 기능: 이미지 → 크롤링 → 초안 TXT 생성"""
        # API 키
        api_frame = ttk.LabelFrame(parent, text="API 설정", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.api_key_entry = ttk.Entry(api_frame, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=(5, 0), pady=3)

        # 이미지 선택
        img_frame = ttk.LabelFrame(parent, text="제품 이미지", padding=10)
        img_frame.pack(fill=tk.X, padx=10, pady=5)

        img_btn_frame = ttk.Frame(img_frame)
        img_btn_frame.pack(fill=tk.X)

        self.img_select_btn = ttk.Button(
            img_btn_frame, text="이미지 선택", command=self._on_select_images,
        )
        self.img_select_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.img_clear_btn = ttk.Button(
            img_btn_frame, text="초기화", command=self._on_clear_images, width=8,
        )
        self.img_clear_btn.pack(side=tk.LEFT)

        self.img_listbox = tk.Listbox(img_frame, height=4, font=("Consolas", 9))
        self.img_listbox.pack(fill=tk.X, pady=(5, 0))

        # 생성 버튼
        gen_btn_frame = ttk.Frame(parent)
        gen_btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.generate_btn = ttk.Button(
            gen_btn_frame, text="초안 생성 시작",
            command=self._on_generate_click,
        )
        self.generate_btn.pack(fill=tk.X)

        # 로그 영역
        draft_log_frame = ttk.LabelFrame(parent, text="생성 로그", padding=5)
        draft_log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.draft_log_text = scrolledtext.ScrolledText(
            draft_log_frame, wrap=tk.WORD, font=("Consolas", 9), state=tk.DISABLED,
        )
        self.draft_log_text.pack(fill=tk.BOTH, expand=True)

    # ──────────────────────────────────────────────
    #  데이터 로드/저장
    # ──────────────────────────────────────────────

    def _load_account(self):
        """account.txt에서 계정 정보를 읽어 자동 입력"""
        if not os.path.exists(ACCOUNT_FILE):
            return
        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines()]
            if len(lines) >= 1 and lines[0]:
                self.id_entry.insert(0, lines[0])
            if len(lines) >= 2 and lines[1]:
                self.pw_entry.insert(0, lines[1])
            if len(lines) >= 3 and lines[2]:
                self.blog_id_entry.insert(0, lines[2])
        except Exception:
            pass

    def _load_api_key(self):
        """api_key.txt에서 API 키를 읽어 자동 입력"""
        if not os.path.exists(API_KEY_FILE):
            return
        try:
            with open(API_KEY_FILE, "r", encoding="utf-8") as f:
                key = f.readline().strip()
            if key:
                self.api_key_entry.insert(0, key)
        except Exception:
            pass

    def _save_api_key(self, key):
        """API 키를 파일에 저장"""
        try:
            with open(API_KEY_FILE, "w", encoding="utf-8") as f:
                f.write(key)
        except Exception:
            pass

    # ──────────────────────────────────────────────
    #  로그 출력
    # ──────────────────────────────────────────────

    def _log(self, message):
        """탭 1 로그"""
        self._append_log(self.log_text, message)

    def _draft_log(self, message):
        """탭 2 로그"""
        self._append_log(self.draft_log_text, message)

    def _append_log(self, widget, message):
        """로그 메시지를 GUI 텍스트 영역에 출력 (스레드 안전)"""
        def _append():
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, message + "\n")
            widget.see(tk.END)
            widget.config(state=tk.DISABLED)
        self.root.after(0, _append)

    # ──────────────────────────────────────────────
    #  탭 1: 블로그 자동 발행 이벤트
    # ──────────────────────────────────────────────

    def _on_upload_click(self):
        """업로드 버튼 클릭"""
        naver_id = self.id_entry.get().strip()
        naver_pw = self.pw_entry.get().strip()
        blog_id_raw = self.blog_id_entry.get().strip()

        if not naver_id or not naver_pw:
            self._log("[오류] 네이버 ID와 비밀번호를 입력해주세요.")
            return
        if not blog_id_raw:
            self._log("[오류] 블로그 ID를 입력해주세요.")
            return

        blog_id = blog_id_raw
        if "blog.naver.com/" in blog_id:
            blog_id = blog_id.rstrip("/").split("blog.naver.com/")[-1]
            blog_id = blog_id.split("/")[0].split("?")[0]
        self._log(f"[설정] 블로그 ID: {blog_id}")

        directory = filedialog.askdirectory(title="TXT 파일이 있는 디렉토리를 선택하세요")
        if not directory:
            return

        self.is_running = True
        self.upload_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        thread = threading.Thread(
            target=self._run_automation,
            args=(naver_id, naver_pw, blog_id, directory),
            daemon=True,
        )
        thread.start()

    def _on_stop_click(self):
        """중단 버튼 클릭"""
        self.is_running = False
        self._log("[중단] 사용자가 중단을 요청했습니다. 현재 글 작성 완료 후 중단됩니다.")

    def _run_automation(self, naver_id, naver_pw, blog_id, directory):
        """자동화 작업 실행 (별도 스레드)"""
        try:
            self._log(f"[탐색] 디렉토리 탐색 중: {directory}")
            txt_files = find_all_txt_files(directory)

            if not txt_files:
                self._log("[오류] TXT 파일을 찾을 수 없습니다.")
                return

            self._log(f"[탐색] {len(txt_files)}개의 TXT 파일을 발견했습니다.")

            posts = []
            for filepath in txt_files:
                title, blocks = read_txt_file(filepath)
                if title and blocks:
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

            self.browser = NaverBlogBrowser(log_callback=self._log)
            if not self.browser.start_browser():
                return

            if not self.browser.login(naver_id, naver_pw):
                return

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

                if i < len(posts) and self.is_running:
                    from config import POST_MIN_DELAY, POST_MAX_DELAY
                    from typer import random_pause
                    delay = random_pause(POST_MIN_DELAY, POST_MAX_DELAY)
                    self._log(f"[대기] 다음 글까지 {delay:.1f}초 대기...")

            self._log(f"\n[완료] 전체 결과: 성공 {success}건, 실패 {fail}건")

        except Exception as e:
            self._log(f"[오류] 예기치 않은 오류: {e}")
        finally:
            if self.browser:
                self.browser.close()
                self.browser = None
            self.is_running = False
            self.root.after(0, lambda: self.upload_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    # ──────────────────────────────────────────────
    #  탭 2: 블로그 초안 생성 이벤트
    # ──────────────────────────────────────────────

    def _on_select_images(self):
        """이미지 파일 선택"""
        filetypes = [
            ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
            ("모든 파일", "*.*"),
        ]
        files = filedialog.askopenfilenames(title="제품 이미지를 선택하세요", filetypes=filetypes)
        if files:
            self.selected_images.extend(files)
            self._refresh_image_list()

    def _on_clear_images(self):
        """이미지 목록 초기화"""
        self.selected_images.clear()
        self._refresh_image_list()

    def _refresh_image_list(self):
        """이미지 리스트박스 갱신"""
        self.img_listbox.delete(0, tk.END)
        for path in self.selected_images:
            self.img_listbox.insert(tk.END, os.path.basename(path))

    def _on_generate_click(self):
        """초안 생성 버튼 클릭"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self._draft_log("[오류] Anthropic API Key를 입력해주세요.")
            return
        if not self.selected_images:
            self._draft_log("[오류] 이미지를 1개 이상 선택해주세요.")
            return

        # API 키 저장
        self._save_api_key(api_key)

        # 저장 디렉토리 선택
        output_dir = filedialog.askdirectory(title="초안 TXT를 저장할 디렉토리를 선택하세요")
        if not output_dir:
            return

        self.is_generating = True
        self.generate_btn.config(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_draft_generation,
            args=(api_key, list(self.selected_images), output_dir),
            daemon=True,
        )
        thread.start()

    def _run_draft_generation(self, api_key, image_paths, output_dir):
        """초안 생성 작업 실행 (별도 스레드)"""
        from image_analyzer import analyze_product_image
        from naver_crawler import crawl_product_info
        from draft_generator import generate_draft

        try:
            # 1단계: 이미지 분석
            self._draft_log("[1/3] 제품 이미지 분석 중...")
            product_info = analyze_product_image(api_key, image_paths[0])

            if not product_info:
                self._draft_log("[오류] 이미지 분석 실패.")
                return

            self._draft_log(f"  제품명: {product_info.get('제품명', '?')}")
            self._draft_log(f"  브랜드: {product_info.get('브랜드', '?')}")
            self._draft_log(f"  카테고리: {product_info.get('카테고리', '?')}")
            self._draft_log(f"  특징: {product_info.get('특징', '?')}")

            keyword = product_info.get("검색키워드", product_info.get("제품명", ""))
            self._draft_log(f"  검색 키워드: {keyword}")

            # 2단계: 네이버 크롤링
            self._draft_log(f"\n[2/3] 네이버 검색 크롤링 중: '{keyword}'")
            crawled_data = crawl_product_info(keyword)

            blog_count = len(crawled_data.get("blog", []))
            shop_count = len(crawled_data.get("shopping", []))
            self._draft_log(f"  블로그 결과: {blog_count}건")
            self._draft_log(f"  쇼핑 결과: {shop_count}건")

            # 3단계: 초안 생성
            self._draft_log(f"\n[3/3] 블로그 초안 생성 중...")
            filepath = generate_draft(
                api_key, product_info, crawled_data, image_paths, output_dir,
            )

            if filepath:
                self._draft_log(f"\n{'='*50}")
                self._draft_log(f"[완료] 초안이 생성되었습니다!")
                self._draft_log(f"  파일: {filepath}")
                self._draft_log(f"  이미지 {len(image_paths)}장 포함")
                self._draft_log(f"{'='*50}")
                self._draft_log(f"\n[안내] '블로그 자동 발행' 탭에서 이 디렉토리를 선택하면 바로 발행할 수 있습니다.")
            else:
                self._draft_log("[오류] 초안 생성 실패.")

        except Exception as e:
            self._draft_log(f"[오류] {e}")
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
