# gui.py - customtkinter 기반 모던 다크 UI

import customtkinter as ctk
from tkinter import filedialog
import threading
import os

from file_scanner import find_all_txt_files, read_txt_file
from browser import NaverBlogBrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(BASE_DIR, "account.txt")
API_KEY_FILE = os.path.join(BASE_DIR, "api_key.txt")

# ── 디자인 토큰 ──────────────────────────────────────
C = {
    "bg":      "#1a1b26",
    "surface": "#1e2030",
    "card":    "#24283b",
    "border":  "#2f3347",
    "primary": "#0d9488",
    "primary_hover": "#0f766e",
    "cta":     "#f97316",
    "cta_hover": "#ea6c04",
    "danger":  "#ef4444",
    "danger_hover": "#dc2626",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "text":    "#e2e8f0",
    "muted":   "#94a3b8",
    "outline_hover": "#3b4266",
}

TAG_COLORS = {
    "[오류]":  "#ef4444",
    "[완료]":  "#22c55e",
    "[진행]":  "#0d9488",
    "[대기]":  "#f59e0b",
    "[탐색]":  "#94a3b8",
    "[설정]":  "#94a3b8",
    "[준비]":  "#94a3b8",
    "[중단]":  "#f59e0b",
    "[안내]":  "#7c86c4",
    "[톤 분석]": "#a78bfa",
    "[톤 분석 완료]": "#22c55e",
    "[톤]":    "#94a3b8",
    "[템플릿]": "#94a3b8",
    "[저장]":  "#22c55e",
    "[1/2]":   "#7c86c4",
    "[2/2]":   "#7c86c4",
    "[3/3]":   "#7c86c4",
}

FONT_BODY   = ("Malgun Gothic", 11)
FONT_BOLD   = ("Malgun Gothic", 11, "bold")
FONT_SMALL  = ("Malgun Gothic", 10)
FONT_LABEL  = ("Malgun Gothic", 10)
FONT_LOG    = ("Consolas", 10)
FONT_SECTION = ("Malgun Gothic", 11, "bold")


def _card(parent, **kw):
    """섹션 카드 프레임"""
    return ctk.CTkFrame(
        parent,
        corner_radius=10,
        fg_color=C["card"],
        border_width=1,
        border_color=C["border"],
        **kw,
    )


def _section_label(parent, text):
    """카드 제목 레이블"""
    return ctk.CTkLabel(
        parent, text=text,
        font=FONT_SECTION,
        text_color=C["primary"],
        anchor="w",
    )


class NaverBlogApp:
    """네이버 블로그 자동화 GUI (customtkinter 다크 테마)"""

    def __init__(self, root):
        self.root = root
        self.root.title("네이버 블로그 자동화 v2")
        self.root.geometry("800x720")
        self.root.minsize(720, 620)
        self.root.configure(fg_color=C["bg"])

        self.browser = None
        self.is_running = False
        self.selected_images = []
        self.is_generating = False

        self._build_ui()
        self._load_account()
        self._load_api_key()

    # ──────────────────────────────────────────────
    #  UI 구성
    # ──────────────────────────────────────────────

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(
            self.root,
            fg_color=C["surface"],
            segmented_button_fg_color=C["card"],
            segmented_button_selected_color=C["primary"],
            segmented_button_selected_hover_color=C["primary_hover"],
            segmented_button_unselected_color=C["card"],
            segmented_button_unselected_hover_color=C["outline_hover"],
            text_color=C["text"],
            corner_radius=12,
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tab_draft   = self.tabview.add("  블로그 초안 생성  ")
        tab_publish = self.tabview.add("  블로그 자동 발행  ")

        self._build_draft_tab(tab_draft)
        self._build_publish_tab(tab_publish)

    # ── 탭: 블로그 초안 생성 ──────────────────────

    def _build_draft_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent", corner_radius=0,
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        scroll.columnconfigure(0, weight=1)

        # ── API 설정 ──
        api_card = _card(scroll)
        api_card.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        api_card.columnconfigure(1, weight=1)
        _section_label(api_card, "API 설정").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 6))
        ctk.CTkLabel(api_card, text="Gemini API Key", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        self.api_key_entry = ctk.CTkEntry(
            api_card, show="*", corner_radius=8,
            fg_color=C["surface"], border_color=C["border"],
            text_color=C["text"], placeholder_text="AIza...",
        )
        self.api_key_entry.grid(row=1, column=1, sticky="ew", padx=(6, 14), pady=(0, 10))

        # ── 제품 정보 ──
        prod_card = _card(scroll)
        prod_card.grid(row=1, column=0, sticky="ew", padx=6, pady=4)
        prod_card.columnconfigure(1, weight=1)
        _section_label(prod_card, "제품 정보").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 6))

        ctk.CTkLabel(prod_card, text="제품명", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))
        self.product_name_entry = ctk.CTkEntry(
            prod_card, corner_radius=8,
            fg_color=C["surface"], border_color=C["border"],
            text_color=C["text"], placeholder_text="예: 에뉴 공기청정기 S3",
        )
        self.product_name_entry.grid(row=1, column=1, columnspan=2, sticky="ew",
                                     padx=(6, 14), pady=(0, 6))

        ctk.CTkLabel(prod_card, text="템플릿", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

        from templates import get_all_template_names
        self.template_var = ctk.StringVar(value="자유형")
        self.template_combo = ctk.CTkComboBox(
            prod_card, variable=self.template_var, width=180,
            values=get_all_template_names(), state="readonly",
            fg_color=C["surface"], border_color=C["border"],
            button_color=C["primary"], button_hover_color=C["primary_hover"],
            dropdown_fg_color=C["card"], text_color=C["text"],
            corner_radius=8,
        )
        self.template_combo.grid(row=2, column=1, sticky="w", padx=(6, 4), pady=(0, 10))

        tmpl_btn_frame = ctk.CTkFrame(prod_card, fg_color="transparent")
        tmpl_btn_frame.grid(row=2, column=2, sticky="w", padx=(0, 14), pady=(0, 10))
        ctk.CTkButton(
            tmpl_btn_frame, text="+ 추가", width=65, height=28,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            corner_radius=6, font=FONT_SMALL,
            command=self._on_add_template,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            tmpl_btn_frame, text="관리", width=55, height=28,
            fg_color="transparent", border_width=1, border_color=C["border"],
            hover_color=C["outline_hover"], text_color=C["muted"],
            corner_radius=6, font=FONT_SMALL,
            command=self._on_manage_templates,
        ).pack(side="left")

        # ── 제품 이미지 ──
        img_card = _card(scroll)
        img_card.grid(row=2, column=0, sticky="ew", padx=6, pady=4)
        img_card.columnconfigure(0, weight=1)
        _section_label(img_card, "제품 이미지").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 6))

        img_btn_row = ctk.CTkFrame(img_card, fg_color="transparent")
        img_btn_row.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))
        ctk.CTkButton(
            img_btn_row, text="이미지 선택", width=110, height=30,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            corner_radius=8, font=FONT_SMALL,
            command=self._on_select_images,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            img_btn_row, text="초기화", width=70, height=30,
            fg_color="transparent", border_width=1, border_color=C["border"],
            hover_color=C["outline_hover"], text_color=C["muted"],
            corner_radius=8, font=FONT_SMALL,
            command=self._on_clear_images,
        ).pack(side="left")
        self.img_count_label = ctk.CTkLabel(
            img_btn_row, text="", font=FONT_SMALL, text_color=C["muted"],
        )
        self.img_count_label.pack(side="left", padx=(10, 0))

        self.img_scroll_frame = ctk.CTkScrollableFrame(
            img_card, height=80, fg_color=C["surface"],
            corner_radius=6, border_width=1, border_color=C["border"],
        )
        self.img_scroll_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.img_scroll_frame.columnconfigure(0, weight=1)

        # ── 작성자 프로필 ──
        profile_card = _card(scroll)
        profile_card.grid(row=3, column=0, sticky="ew", padx=6, pady=4)
        _section_label(profile_card, "작성자 프로필").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(10, 6))

        ctk.CTkLabel(profile_card, text="성별", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=1, column=0, sticky="w", padx=(14, 6), pady=(0, 10))
        self.gender_var = ctk.StringVar(value="여성")
        ctk.CTkComboBox(
            profile_card, variable=self.gender_var, width=100,
            values=["여성", "남성"], state="readonly",
            fg_color=C["surface"], border_color=C["border"],
            button_color=C["primary"], button_hover_color=C["primary_hover"],
            dropdown_fg_color=C["card"], text_color=C["text"], corner_radius=8,
        ).grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 10))

        ctk.CTkLabel(profile_card, text="연령대", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=1, column=2, sticky="w", padx=(0, 6), pady=(0, 10))
        self.age_var = ctk.StringVar(value="30대")
        ctk.CTkComboBox(
            profile_card, variable=self.age_var, width=120,
            values=["10대", "20대", "30대", "40대", "50대", "60대 이상"], state="readonly",
            fg_color=C["surface"], border_color=C["border"],
            button_color=C["primary"], button_hover_color=C["primary_hover"],
            dropdown_fg_color=C["card"], text_color=C["text"], corner_radius=8,
        ).grid(row=1, column=3, sticky="w", padx=(0, 14), pady=(0, 10))

        # ── 톤 클론 ──
        tone_card = _card(scroll)
        tone_card.grid(row=4, column=0, sticky="ew", padx=6, pady=4)
        tone_card.columnconfigure(1, weight=1)
        _section_label(tone_card, "블로그 톤 클론 (선택)").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(10, 6))

        ctk.CTkLabel(tone_card, text="블로그 ID", font=FONT_LABEL,
                     text_color=C["muted"]).grid(row=1, column=0, sticky="w", padx=(14, 6), pady=(0, 6))
        self.tone_blog_entry = ctk.CTkEntry(
            tone_card, width=180, corner_radius=8,
            fg_color=C["surface"], border_color=C["border"],
            text_color=C["text"], placeholder_text="블로그 ID 또는 URL",
        )
        self.tone_blog_entry.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=(0, 6))

        self.tone_analyze_btn = ctk.CTkButton(
            tone_card, text="톤 분석", width=80, height=30,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            corner_radius=8, font=FONT_SMALL,
            command=self._on_analyze_tone,
        )
        self.tone_analyze_btn.grid(row=1, column=2, sticky="w", padx=(0, 6), pady=(0, 6))

        ctk.CTkButton(
            tone_card, text="톤 해제", width=70, height=30,
            fg_color="transparent", border_width=1, border_color=C["border"],
            hover_color=C["outline_hover"], text_color=C["muted"],
            corner_radius=8, font=FONT_SMALL,
            command=self._on_clear_tone,
        ).grid(row=1, column=3, sticky="w", padx=(0, 14), pady=(0, 6))

        self.tone_badge = ctk.CTkLabel(
            tone_card, text=" 톤 미설정 ",
            font=FONT_SMALL, corner_radius=6,
            fg_color=C["border"], text_color=C["muted"],
        )
        self.tone_badge.grid(row=2, column=0, columnspan=4, sticky="w",
                             padx=14, pady=(0, 10))
        self._load_saved_tone()

        # ── 생성 버튼 + 진행 바 ──
        gen_card = _card(scroll)
        gen_card.grid(row=5, column=0, sticky="ew", padx=6, pady=4)
        gen_card.columnconfigure(0, weight=1)

        self.generate_btn = ctk.CTkButton(
            gen_card, text="초안 생성 시작",
            height=42, corner_radius=10,
            fg_color=C["cta"], hover_color=C["cta_hover"],
            text_color="white", font=("Malgun Gothic", 12, "bold"),
            command=self._on_generate_click,
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.gen_progress = ctk.CTkProgressBar(
            gen_card, mode="indeterminate",
            fg_color=C["surface"], progress_color=C["cta"], corner_radius=4,
        )
        self.gen_progress.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        self.gen_progress.grid_remove()

        # ── 생성 로그 ──
        log_card = _card(scroll)
        log_card.grid(row=6, column=0, sticky="nsew", padx=6, pady=(4, 6))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        scroll.rowconfigure(6, weight=1)
        _section_label(log_card, "생성 로그").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        self.draft_log_text = ctk.CTkTextbox(
            log_card, state="disabled", font=FONT_LOG,
            fg_color=C["surface"], text_color=C["text"],
            corner_radius=8, border_width=1, border_color=C["border"],
            wrap="word", height=160,
        )
        self.draft_log_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))

    # ── 탭: 블로그 자동 발행 ──────────────────────

    def _build_publish_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # ── 설정 카드 ──
        settings_card = _card(parent)
        settings_card.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        settings_card.columnconfigure(1, weight=1)
        _section_label(settings_card, "계정 설정").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 6))

        for i, (label, attr, kw) in enumerate([
            ("네이버 ID",  "id_entry",      {}),
            ("비밀번호",   "pw_entry",      {"show": "*"}),
            ("블로그 ID",  "blog_id_entry", {}),
        ], start=1):
            ctk.CTkLabel(settings_card, text=label, font=FONT_LABEL,
                         text_color=C["muted"]).grid(
                row=i, column=0, sticky="w", padx=(14, 8), pady=(0, 6))
            entry = ctk.CTkEntry(
                settings_card, corner_radius=8,
                fg_color=C["surface"], border_color=C["border"],
                text_color=C["text"], **kw,
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 14), pady=(0, 6))
            setattr(self, attr, entry)

        # 마지막 행 하단 패딩
        ctk.CTkLabel(settings_card, text="").grid(row=4, column=0)

        # ── 버튼 행 ──
        btn_card = _card(parent)
        btn_card.grid(row=1, column=0, sticky="ew", padx=6, pady=4)
        btn_card.columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=10)
        btn_row.columnconfigure(0, weight=1)

        self.upload_btn = ctk.CTkButton(
            btn_row, text="디렉토리 선택 및 업로드 시작",
            height=40, corner_radius=10,
            fg_color=C["cta"], hover_color=C["cta_hover"],
            text_color="white", font=("Malgun Gothic", 12, "bold"),
            command=self._on_upload_click,
        )
        self.upload_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            btn_row, text="중단", width=80, height=40,
            corner_radius=10,
            fg_color=C["danger"], hover_color=C["danger_hover"],
            text_color="white", font=FONT_BOLD,
            state="disabled",
            command=self._on_stop_click,
        )
        self.stop_btn.grid(row=0, column=1)

        self.pub_progress = ctk.CTkProgressBar(
            btn_card, mode="indeterminate",
            fg_color=C["surface"], progress_color=C["cta"], corner_radius=4,
        )
        self.pub_progress.pack(fill="x", padx=14, pady=(0, 4))
        self.pub_progress.pack_forget()

        # ── 발행 로그 ──
        log_card = _card(parent)
        log_card.grid(row=2, column=0, sticky="nsew", padx=6, pady=(4, 6))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        _section_label(log_card, "진행 로그").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        self.log_text = ctk.CTkTextbox(
            log_card, state="disabled", font=FONT_LOG,
            fg_color=C["surface"], text_color=C["text"],
            corner_radius=8, border_width=1, border_color=C["border"],
            wrap="word",
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))

    # ──────────────────────────────────────────────
    #  데이터 로드
    # ──────────────────────────────────────────────

    def _load_account(self):
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
        try:
            with open(API_KEY_FILE, "w", encoding="utf-8") as f:
                f.write(key)
        except Exception:
            pass

    # ──────────────────────────────────────────────
    #  로그 출력 (컬러 태그)
    # ──────────────────────────────────────────────

    def _log(self, message):
        self._append_log(self.log_text, message)

    def _draft_log(self, message):
        self._append_log(self.draft_log_text, message)

    def _append_log(self, widget, message):
        def _append():
            tb = widget._textbox  # 내부 tk.Text 접근
            tb.configure(state="normal")

            # 컬러 태그 적용
            matched_color = None
            for prefix, color in TAG_COLORS.items():
                if message.startswith(prefix) or f"\n{prefix}" in message:
                    matched_color = color
                    break

            if matched_color:
                tag = f"tag_{matched_color.replace('#', '')}"
                tb.tag_config(tag, foreground=matched_color)
                tb.insert("end", message + "\n", tag)
            else:
                tb.insert("end", message + "\n")

            tb.see("end")
            tb.configure(state="disabled")

        self.root.after(0, _append)

    # ──────────────────────────────────────────────
    #  탭 발행: 이벤트
    # ──────────────────────────────────────────────

    def _on_upload_click(self):
        naver_id  = self.id_entry.get().strip()
        naver_pw  = self.pw_entry.get().strip()
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
        self.upload_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.pub_progress.pack(fill="x", padx=14, pady=(0, 4))
        self.pub_progress.start()

        threading.Thread(
            target=self._run_automation,
            args=(naver_id, naver_pw, blog_id, directory),
            daemon=True,
        ).start()

    def _on_stop_click(self):
        self.is_running = False
        self._log("[중단] 사용자가 중단을 요청했습니다. 현재 글 작성 완료 후 중단됩니다.")

    def _run_automation(self, naver_id, naver_pw, blog_id, directory):
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
            self.root.after(0, self._pub_done)

    def _pub_done(self):
        self.upload_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.pub_progress.stop()
        self.pub_progress.pack_forget()

    # ──────────────────────────────────────────────
    #  탭 초안: 이미지 선택
    # ──────────────────────────────────────────────

    def _on_select_images(self):
        filetypes = [
            ("이미지 파일", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"),
            ("모든 파일", "*.*"),
        ]
        files = filedialog.askopenfilenames(title="제품 이미지를 선택하세요", filetypes=filetypes)
        if files:
            self.selected_images.extend(files)
            self._refresh_image_list()

    def _on_clear_images(self):
        self.selected_images.clear()
        self._refresh_image_list()

    def _refresh_image_list(self):
        for w in self.img_scroll_frame.winfo_children():
            w.destroy()
        for path in self.selected_images:
            ctk.CTkLabel(
                self.img_scroll_frame,
                text=f"  {os.path.basename(path)}",
                font=FONT_LOG, text_color=C["muted"],
                anchor="w",
            ).pack(fill="x", padx=4, pady=1)
        n = len(self.selected_images)
        self.img_count_label.configure(
            text=f"({n}개 선택됨)" if n else "",
        )

    # ──────────────────────────────────────────────
    #  탭 초안: 톤 클론
    # ──────────────────────────────────────────────

    def _load_saved_tone(self):
        from tone_cloner import load_tone
        tone = load_tone()
        if tone and tone.get("전체 톤 요약"):
            summary = tone["전체 톤 요약"][:45]
            self.tone_badge.configure(
                text=f"  ✓ 적용 중: {summary}...  ",
                fg_color=C["success"], text_color="white",
            )

    def _on_analyze_tone(self):
        api_key = self.api_key_entry.get().strip()
        blog_id = self.tone_blog_entry.get().strip()

        if not api_key:
            self._draft_log("[오류] Gemini API Key를 입력해주세요.")
            return
        if not blog_id:
            self._draft_log("[오류] 톤을 복사할 블로그 ID를 입력해주세요.")
            return

        if "blog.naver.com/" in blog_id:
            blog_id = blog_id.rstrip("/").split("blog.naver.com/")[-1]
            blog_id = blog_id.split("/")[0].split("?")[0]

        self.tone_analyze_btn.configure(state="disabled")
        self.tone_badge.configure(
            text="  분석 중...  ",
            fg_color=C["warning"], text_color="white",
        )

        threading.Thread(
            target=self._run_tone_analysis,
            args=(api_key, blog_id),
            daemon=True,
        ).start()

    def _run_tone_analysis(self, api_key, blog_id):
        from tone_cloner import crawl_blog_posts, analyze_tone, save_tone
        try:
            self._draft_log(f"\n[톤 분석] 블로그 '{blog_id}'의 최근 글 수집 중...")
            posts = crawl_blog_posts(blog_id, num=5)

            if not posts:
                self._draft_log("[오류] 블로그 글을 가져올 수 없습니다.")
                self.root.after(0, lambda: self.tone_badge.configure(
                    text=" 톤 미설정 ", fg_color=C["border"], text_color=C["muted"]))
                return

            self._draft_log(f"  {len(posts)}개의 글 수집 완료")
            for p in posts:
                self._draft_log(f"    - {p['title'][:40]}")

            self._draft_log("[톤 분석] Gemini가 톤을 분석 중...")
            tone_data = analyze_tone(api_key, posts)

            if not tone_data:
                self._draft_log("[오류] 톤 분석 실패.")
                return

            save_tone(tone_data)

            summary = tone_data.get("전체 톤 요약", "분석 완료")
            self._draft_log("\n[톤 분석 완료]")
            for key, value in tone_data.items():
                if key != "raw":
                    self._draft_log(f"  {key}: {value}")

            self.root.after(0, lambda: self.tone_badge.configure(
                text=f"  ✓ 적용 중: {summary[:45]}...  ",
                fg_color=C["success"], text_color="white",
            ))

        except Exception as e:
            self._draft_log(f"[오류] 톤 분석 실패: {e}")
            self.root.after(0, lambda: self.tone_badge.configure(
                text=" 톤 미설정 ", fg_color=C["border"], text_color=C["muted"]))
        finally:
            self.root.after(0, lambda: self.tone_analyze_btn.configure(state="normal"))

    def _on_clear_tone(self):
        import os as _os
        from tone_cloner import TONE_FILE
        if _os.path.exists(TONE_FILE):
            _os.remove(TONE_FILE)
        self.tone_badge.configure(
            text=" 톤 미설정 ", fg_color=C["border"], text_color=C["muted"])
        self._draft_log("[톤] 클론된 톤이 해제되었습니다. 기본 프로필을 사용합니다.")

    # ──────────────────────────────────────────────
    #  탭 초안: 커스텀 템플릿
    # ──────────────────────────────────────────────

    def _refresh_template_list(self):
        from templates import get_all_template_names
        self.template_combo.configure(values=get_all_template_names())

    def _on_add_template(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("커스텀 템플릿 추가")
        dialog.geometry("560x460")
        dialog.configure(fg_color=C["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="템플릿 이름", font=FONT_BOLD,
                     text_color=C["text"]).pack(anchor="w", padx=16, pady=(16, 4))
        name_entry = ctk.CTkEntry(
            dialog, corner_radius=8,
            fg_color=C["surface"], border_color=C["border"], text_color=C["text"],
        )
        name_entry.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(dialog, text="템플릿 구조", font=FONT_BOLD,
                     text_color=C["text"]).pack(anchor="w", padx=16)
        text_area = ctk.CTkTextbox(
            dialog, corner_radius=8,
            fg_color=C["surface"], border_color=C["border"],
            text_color=C["text"], font=FONT_BODY,
        )
        text_area.pack(fill="both", expand=True, padx=16, pady=(4, 10))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        def _save():
            name = name_entry.get().strip()
            structure = text_area.get("1.0", "end").strip()
            if not name:
                self._draft_log("[오류] 템플릿 이름을 입력해주세요.")
                return
            if not structure:
                self._draft_log("[오류] 템플릿 내용을 입력해주세요.")
                return
            from templates import add_custom_template
            add_custom_template(name, structure)
            self._refresh_template_list()
            self.template_var.set(f"[커스텀] {name}")
            self._draft_log(f"[템플릿] '{name}' 커스텀 템플릿이 추가되었습니다.")
            dialog.destroy()

        ctk.CTkButton(
            btn_row, text="저장", width=90, height=34,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            corner_radius=8, command=_save,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="취소", width=80, height=34,
            fg_color="transparent", border_width=1, border_color=C["border"],
            hover_color=C["outline_hover"], text_color=C["muted"],
            corner_radius=8, command=dialog.destroy,
        ).pack(side="left")

    def _on_manage_templates(self):
        from templates import load_custom_templates, delete_custom_template

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("커스텀 템플릿 관리")
        dialog.geometry("400x320")
        dialog.configure(fg_color=C["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        custom = load_custom_templates()
        if not custom:
            ctk.CTkLabel(dialog, text="저장된 커스텀 템플릿이 없습니다.",
                         text_color=C["muted"]).pack(pady=30)
            ctk.CTkButton(dialog, text="닫기", width=80,
                          fg_color=C["primary"], command=dialog.destroy).pack()
            return

        ctk.CTkLabel(dialog, text="커스텀 템플릿 (선택 후 삭제)",
                     font=FONT_BOLD, text_color=C["text"]).pack(anchor="w", padx=16, pady=(16, 6))

        list_frame = ctk.CTkScrollableFrame(
            dialog, fg_color=C["surface"],
            corner_radius=8, border_width=1, border_color=C["border"],
        )
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        selected_name = ctk.StringVar(value="")
        btns = []

        def _select(name, btn):
            selected_name.set(name)
            for b in btns:
                b.configure(fg_color=C["surface"])
            btn.configure(fg_color=C["primary"])

        for name in custom:
            b = ctk.CTkButton(
                list_frame, text=name, anchor="w",
                fg_color=C["surface"], hover_color=C["outline_hover"],
                text_color=C["text"], corner_radius=6, height=32,
            )
            b.configure(command=lambda n=name, btn=b: _select(n, btn))
            b.pack(fill="x", padx=4, pady=2)
            btns.append(b)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        def _delete():
            name = selected_name.get()
            if not name:
                return
            delete_custom_template(name)
            self._refresh_template_list()
            if self.template_var.get() == f"[커스텀] {name}":
                self.template_var.set("자유형")
            self._draft_log(f"[템플릿] '{name}' 커스텀 템플릿이 삭제되었습니다.")
            dialog.destroy()

        ctk.CTkButton(
            btn_row, text="선택 삭제", width=90, height=34,
            fg_color=C["danger"], hover_color=C["danger_hover"],
            corner_radius=8, command=_delete,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="닫기", width=80, height=34,
            fg_color="transparent", border_width=1, border_color=C["border"],
            hover_color=C["outline_hover"], text_color=C["muted"],
            corner_radius=8, command=dialog.destroy,
        ).pack(side="left")

    # ──────────────────────────────────────────────
    #  탭 초안: 초안 생성
    # ──────────────────────────────────────────────

    def _on_generate_click(self):
        api_key      = self.api_key_entry.get().strip()
        product_name = self.product_name_entry.get().strip()

        if not api_key:
            self._draft_log("[오류] Gemini API Key를 입력해주세요.")
            return
        if not product_name:
            self._draft_log("[오류] 제품명을 입력해주세요.")
            return
        if not self.selected_images:
            self._draft_log("[오류] 이미지를 1개 이상 선택해주세요.")
            return

        output_dir = filedialog.askdirectory(title="초안 TXT를 저장할 디렉토리를 선택하세요")
        if not output_dir:
            return

        self._save_api_key(api_key)
        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="생성 중...")
        self.gen_progress.grid()
        self.gen_progress.start()

        threading.Thread(
            target=self._run_draft_generation,
            args=(api_key, product_name, list(self.selected_images), output_dir,
                  self.gender_var.get(), self.age_var.get(), self.template_var.get()),
            daemon=True,
        ).start()

    def _run_draft_generation(self, api_key, product_name, image_paths,
                               output_dir, gender, age, template="자유형"):
        from naver_crawler import crawl_product_info
        from draft_generator import generate_draft
        try:
            self._draft_log(f"[1/2] 제품 정보 확인: {product_name}")
            product_info = {"제품명": product_name, "검색키워드": product_name}

            self._draft_log(f"\n[2/2] 네이버 검색 크롤링 중: '{product_name}'")
            crawled_data = crawl_product_info(product_name)

            blog_count = len(crawled_data.get("blog", []))
            shop_count = len(crawled_data.get("shopping", []))
            self._draft_log(f"  블로그 결과: {blog_count}건")
            self._draft_log(f"  쇼핑 결과: {shop_count}건")

            template_label = f", 템플릿: {template}" if template != "자유형" else ""
            self._draft_log(f"\n[3/3] 블로그 초안 생성 중... (작성자: {age} {gender}{template_label})")
            author_profile = {"gender": gender, "age": age}
            filepath = generate_draft(
                api_key, product_info, crawled_data, image_paths, output_dir,
                author_profile=author_profile, template_name=template,
            )

            if filepath:
                self._draft_log(f"\n{'='*50}")
                self._draft_log(f"[완료] 초안이 생성되었습니다!")
                self._draft_log(f"  파일: {filepath}")
                self._draft_log(f"  이미지 {len(image_paths)}장 포함")
                self._draft_log(f"{'='*50}")
                self._draft_log(f"\n[안내] '블로그 자동 발행' 탭에서 이 디렉토리를 선택하면 바로 발행할 수 있습니다.")
                self._show_preview(filepath)
            else:
                self._draft_log("[오류] 초안 생성 실패.")

        except Exception as e:
            self._draft_log(f"[오류] {e}")
        finally:
            self.is_generating = False
            self.root.after(0, self._gen_done)

    def _gen_done(self):
        self.generate_btn.configure(state="normal", text="초안 생성 시작")
        self.gen_progress.stop()
        self.gen_progress.grid_remove()

    def _show_preview(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        def _open():
            preview = ctk.CTkToplevel(self.root)
            preview.title(f"초안 편집 — {os.path.basename(filepath)}")
            preview.geometry("640x520")
            preview.configure(fg_color=C["bg"])

            text = ctk.CTkTextbox(
                preview, wrap="word", font=FONT_BODY,
                fg_color=C["surface"], text_color=C["text"],
                corner_radius=8, border_width=1, border_color=C["border"],
            )
            text.pack(fill="both", expand=True, padx=16, pady=(16, 8))
            text.insert("end", content)

            btn_row = ctk.CTkFrame(preview, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=(0, 16))

            def _save():
                new_content = text.get("1.0", "end").rstrip("\n")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self._draft_log(f"[저장] 초안이 저장되었습니다: {filepath}")
                preview.title(f"초안 편집 — {os.path.basename(filepath)} (저장됨)")

            ctk.CTkButton(
                btn_row, text="저장", width=80, height=32,
                fg_color=C["primary"], hover_color=C["primary_hover"],
                corner_radius=8, command=_save,
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                btn_row, text="파일 위치 열기", width=110, height=32,
                fg_color="transparent", border_width=1, border_color=C["border"],
                hover_color=C["outline_hover"], text_color=C["muted"],
                corner_radius=8,
                command=lambda: os.startfile(os.path.dirname(filepath)),
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                btn_row, text="닫기", width=70, height=32,
                fg_color="transparent", border_width=1, border_color=C["border"],
                hover_color=C["outline_hover"], text_color=C["muted"],
                corner_radius=8, command=preview.destroy,
            ).pack(side="right")

        self.root.after(0, _open)
