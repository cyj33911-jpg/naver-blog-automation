# browser.py - Selenium 브라우저 제어 모듈

import time
import random
import os
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    NAVER_LOGIN_URL, BLOG_WRITE_URL, SELECTORS, PAGE_LOAD_TIMEOUT,
    MANUAL_LOGIN_WAIT, POST_MIN_DELAY, POST_MAX_DELAY,
)
from typer import type_like_human, random_pause


class NaverBlogBrowser:
    """네이버 블로그 자동 글쓰기 브라우저 컨트롤러"""

    def __init__(self, log_callback=None):
        self.driver = None
        self.log = log_callback or print

    def start_browser(self):
        """크롬 드라이버 자동 업데이트 및 브라우저 시작 (프로필 유지)"""
        self.log("[시작] 크롬 드라이버 업데이트 중...")
        try:
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-notifications")

            # 크롬 프로필 저장 (로그인 세션 유지)
            profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
            options.add_argument(f"--user-data-dir={profile_dir}")

            # 비밀번호 저장 팝업 비활성화
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            }
            options.add_experimental_option("prefs", prefs)

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(5)
            self.driver.maximize_window()

            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

            self.log("[완료] 브라우저가 시작되었습니다.")
            return True
        except Exception as e:
            self.log(f"[오류] 브라우저 시작 실패: {e}")
            return False

    def login(self, naver_id, naver_pw):
        """네이버 로그인 (프로필에 세션이 있으면 자동 통과)"""
        try:
            # 네이버에 접속해서 이미 로그인되어 있는지 확인
            self.log("[로그인] 로그인 상태 확인 중...")
            self.driver.get("https://www.naver.com")
            time.sleep(2)

            # 로그인 여부 확인 (네이버 메인에서 로그인 버튼이 없으면 이미 로그인됨)
            if self._is_logged_in():
                self.log("[완료] 이미 로그인되어 있습니다! (저장된 세션 사용)")
                return True

            # 로그인 안 되어 있으면 로그인 페이지로 이동
            self.log("[로그인] 로그인이 필요합니다. 로그인 페이지로 이동...")
            self.driver.get(NAVER_LOGIN_URL)
            time.sleep(2)

            # 수동 로그인 대기 (캡차 문제 없이 사용자가 직접 로그인)
            self.log("=" * 50)
            self.log("[안내] 브라우저에서 직접 로그인해주세요!")
            self.log("[안내] 로그인 완료 후 자동으로 진행됩니다.")
            self.log(f"[안내] 대기 시간: {MANUAL_LOGIN_WAIT}초")
            self.log("=" * 50)

            try:
                WebDriverWait(self.driver, MANUAL_LOGIN_WAIT).until(
                    lambda d: "nid.naver.com" not in d.current_url
                )
                self.log("[완료] 로그인 성공! (다음부터는 자동 로그인됩니다)")
                return True
            except TimeoutException:
                self.log("[오류] 로그인 시간 초과.")
                return False

        except Exception as e:
            self.log(f"[오류] 로그인 실패: {e}")
            return False

    def _is_logged_in(self):
        """네이버에 이미 로그인되어 있는지 확인"""
        try:
            # 네이버 메인에서 로그인 상태 확인
            login_btn = self.driver.find_elements(By.CSS_SELECTOR, ".MyView-module__link_login___HpHMW")
            if login_btn:
                return False  # 로그인 버튼이 보이면 미로그인

            # 프로필 영역이 보이면 로그인 상태
            profile = self.driver.find_elements(By.CSS_SELECTOR, ".MyView-module__link_name___mcrnV, .MyView-module__thumb___bEbS2")
            if profile:
                return True

            # JavaScript로 쿠키 확인
            cookies = self.driver.get_cookies()
            naver_cookies = [c for c in cookies if 'NID' in c.get('name', '') or 'nid' in c.get('name', '')]
            return len(naver_cookies) > 0
        except Exception:
            return False

    def write_post(self, blog_id, title, blocks):
        """블로그 글 작성 및 발행 (텍스트 + 이미지/영상 업로드)

        Args:
            blog_id: 네이버 블로그 ID
            title: 글 제목
            blocks: 콘텐츠 블록 리스트 [{"type": "text"/"image"/"video", ...}, ...]
        """
        try:
            # blog_id 정리
            clean_id = blog_id
            if "blog.naver.com/" in clean_id:
                clean_id = clean_id.rstrip("/").split("blog.naver.com/")[-1]
                clean_id = clean_id.split("/")[0].split("?")[0]
            if "://" in clean_id:
                clean_id = clean_id.split("/")[-1]

            # 글쓰기 페이지 이동
            write_url = f"https://blog.naver.com/{clean_id}/postwrite"
            self.log(f"[글쓰기] 글쓰기 페이지로 이동: {write_url}")
            self.driver.get(write_url)
            time.sleep(5)

            # postwrite URL 실패 시 구형 URL 시도
            if "error" in self.driver.current_url.lower() or "페이지" in (self.driver.title or ""):
                alt_url = f"https://blog.naver.com/PostWriteForm.naver?blogId={clean_id}"
                self.log(f"[글쓰기] 대체 URL로 재시도: {alt_url}")
                self.driver.get(alt_url)
                time.sleep(5)

            # 도움말 사이드바 닫기
            self._close_help_popup()

            # iframe 전환
            self.log("[글쓰기] 에디터 iframe 탐색 중...")
            self._switch_to_editor_iframe()
            time.sleep(2)

            # 제목 입력 전 오버레이 제거
            self._remove_overlays()
            self.log(f"[글쓰기] 제목 입력 중: {title[:30]}...")
            title_elem = self._find_element_multi(SELECTORS["title_areas"], "제목")
            if title_elem:
                self._safe_click(title_elem, "제목 영역")
                type_like_human(self.driver, title_elem, title, click=False)
                time.sleep(random.uniform(0.5, 1.5))
            else:
                self.log("[오류] 제목 입력 영역을 찾을 수 없습니다.")
                self.driver.switch_to.default_content()
                return False

            # 본문 영역 클릭
            self._remove_overlays()
            body_elem = self._find_element_multi(SELECTORS["body_areas"], "본문")
            if not body_elem:
                self.log("[오류] 본문 입력 영역을 찾을 수 없습니다.")
                self.driver.switch_to.default_content()
                return False
            self._safe_click(body_elem, "본문 영역")
            time.sleep(0.5)

            # 콘텐츠 블록 순차 처리
            from selenium.webdriver.common.keys import Keys
            first_text = True

            for i, block in enumerate(blocks):
                block_type = block["type"]

                if block_type == "text":
                    self.log(f"[글쓰기] 텍스트 블록 입력 중... ({i+1}/{len(blocks)})")
                    self._remove_overlays()
                    if first_text:
                        # 첫 텍스트: 본문 영역 JS 클릭하여 포커스
                        self._safe_click(body_elem, "본문 영역 (첫 텍스트)")
                        time.sleep(0.5)
                        type_like_human(self.driver, body_elem, block["content"], click=False)
                        first_text = False
                    else:
                        # 이후 텍스트: 현재 커서 위치에서 이어서 타이핑
                        active = self.driver.switch_to.active_element
                        type_like_human(self.driver, active, block["content"], click=False)
                    time.sleep(random.uniform(0.5, 1.0))

                elif block_type == "image":
                    self.log(f"[업로드] 이미지 업로드: {block['filename']}")
                    self._remove_overlays()
                    # 업로드 전 Enter로 새 줄 생성
                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.3)
                    self._upload_image(block["filepath"])
                    time.sleep(random.uniform(2.0, 3.0))

                elif block_type == "video":
                    self.log(f"[업로드] 영상 업로드: {block['filename']}")
                    self._remove_overlays()
                    ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.3)
                    self._upload_video(block["filepath"])
                    time.sleep(random.uniform(3.0, 5.0))

                # 매 블록 처리 후 커서를 문서 끝으로 이동
                self._move_cursor_to_end()
                time.sleep(0.3)

            # 메인 프레임으로 복귀 후 발행
            self.driver.switch_to.default_content()
            time.sleep(0.5)

            self.log("[글쓰기] 발행 중...")
            return self._publish_post()

        except Exception as e:
            self.log(f"[오류] 글 작성 실패: {e}")
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            return False

    def _close_help_popup(self):
        """네이버 에디터 도움말 사이드바 및 팝업 닫기"""
        self._remove_overlays()

    def _remove_overlays(self):
        """알림 팝업 닫기 + 오버레이 딤 비활성화"""
        try:
            self.driver.execute_script("""
                // 1. 알림/확인 팝업 버튼 클릭하여 닫기
                document.querySelectorAll('.se-popup-alert, .se-popup-alert-confirm').forEach(popup => {
                    var btns = popup.querySelectorAll('button');
                    btns.forEach(btn => { try { btn.click(); } catch(e) {} });
                    popup.style.display = 'none';
                });

                // 2. 오버레이 딤: 클릭 통과 + 숨기기 (제거X → 재생성 방지)
                document.querySelectorAll(
                    '.se-popup-dim, .se-popup-dim-transparent, [class*="popup-dim"]'
                ).forEach(el => {
                    el.style.pointerEvents = 'none';
                    el.style.display = 'none';
                });

                // 3. 도움말 패널 숨기기
                document.querySelectorAll(
                    '[class*="help-panel"], [class*="guide-panel"]'
                ).forEach(el => { el.style.display = 'none'; });
            """)
        except Exception:
            pass

    def _safe_click(self, element, description="요소"):
        """오버레이를 제거하고 JS 클릭으로 안전하게 클릭"""
        for attempt in range(3):
            try:
                self._remove_overlays()
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception as e:
                self.log(f"[재시도] {description} 클릭 실패 ({attempt+1}/3): {str(e)[:50]}")
                self._remove_overlays()
                time.sleep(1)
        return False

    def _move_cursor_to_end(self):
        """커서를 문서(에디터) 끝으로 이동"""
        try:
            from selenium.webdriver.common.keys import Keys
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(
                Keys.END
            ).key_up(Keys.CONTROL).perform()
            time.sleep(0.2)
            # Enter로 새 줄 시작 (다음 블록을 위해)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception:
            pass

    def close(self):
        """브라우저 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.log("[종료] 브라우저가 종료되었습니다.")
            except Exception:
                pass
            self.driver = None

    # --- 미디어 업로드 ---

    def _intercept_file_input_clicks(self):
        """file input의 click()을 가로채고 MutationObserver로 감시"""
        self.driver.execute_script("""
            // 캡처된 file input 저장소
            window.__capturedFileInputs = [];
            window.__lastFileInput = null;

            // 1. click() 메서드 오버라이드
            window.__originalFileInputClick = HTMLInputElement.prototype.click;
            HTMLInputElement.prototype.click = function() {
                if (this.type === 'file') {
                    window.__lastFileInput = this;
                    window.__capturedFileInputs.push(this);
                    return;
                }
                return window.__originalFileInputClick.call(this);
            };

            // 2. MutationObserver로 새 file input 감시
            window.__fileInputObserver = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) {
                            if (node.tagName === 'INPUT' && node.type === 'file') {
                                window.__capturedFileInputs.push(node);
                                window.__lastFileInput = node;
                            }
                            if (node.querySelectorAll) {
                                node.querySelectorAll('input[type="file"]').forEach(inp => {
                                    window.__capturedFileInputs.push(inp);
                                    window.__lastFileInput = inp;
                                });
                            }
                        }
                    });
                });
            });
            window.__fileInputObserver.observe(document.documentElement, {
                childList: true, subtree: true
            });

            // 3. createElement 오버라이드 (동적 생성 감지)
            window.__originalCreateElement = document.createElement.bind(document);
            document.createElement = function(tag) {
                var el = window.__originalCreateElement(tag);
                if (tag.toLowerCase() === 'input') {
                    var origSetAttr = el.setAttribute.bind(el);
                    el.setAttribute = function(name, value) {
                        origSetAttr(name, value);
                        if (name === 'type' && value === 'file') {
                            window.__capturedFileInputs.push(el);
                            window.__lastFileInput = el;
                        }
                    };
                    // type 프로퍼티 감시
                    var origType = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'type');
                    if (origType && origType.set) {
                        Object.defineProperty(el, 'type', {
                            set: function(v) {
                                origType.set.call(this, v);
                                if (v === 'file') {
                                    window.__capturedFileInputs.push(this);
                                    window.__lastFileInput = this;
                                }
                            },
                            get: function() { return origType.get.call(this); }
                        });
                    }
                }
                return el;
            };
        """)

    def _restore_file_input_clicks(self):
        """file input click 원래대로 복원"""
        self.driver.execute_script("""
            if (window.__originalFileInputClick) {
                HTMLInputElement.prototype.click = window.__originalFileInputClick;
            }
            if (window.__fileInputObserver) {
                window.__fileInputObserver.disconnect();
            }
            if (window.__originalCreateElement) {
                document.createElement = window.__originalCreateElement;
            }
        """)

    def _get_intercepted_file_input(self):
        """가로챈 file input 요소 반환"""
        try:
            result = self.driver.execute_script("""
                // 마지막으로 캡처된 file input 반환
                if (window.__lastFileInput) return window.__lastFileInput;
                if (window.__capturedFileInputs && window.__capturedFileInputs.length > 0) {
                    return window.__capturedFileInputs[window.__capturedFileInputs.length - 1];
                }
                return null;
            """)
            return result
        except Exception:
            return None

    def _upload_media(self, filepath, toolbar_name, panel_btn_text, wait_sec=5):
        """통합 미디어 업로드 (이미지/영상 공통)

        1. JS로 file input click 차단
        2. 툴바 버튼 클릭 -> 패널 열림
        3. 패널 내 업로드 버튼 클릭 -> file input click이 차단됨
        4. 차단된 file input에 send_keys로 파일 경로 전송
        """
        abs_path = os.path.abspath(filepath)
        if not os.path.exists(abs_path):
            self.log(f"[오류] 파일 없음: {abs_path}")
            return False

        try:
            # 먼저 이미 존재하는 file input 시도
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for inp in inputs:
                accept = (inp.get_attribute("accept") or "").lower()
                if toolbar_name == "사진" and "image" in accept:
                    self.driver.execute_script(
                        "arguments[0].style.display='block'; arguments[0].style.visibility='visible';", inp)
                    inp.send_keys(abs_path)
                    self.log(f"[성공] 기존 input으로 업로드: {os.path.basename(filepath)}")
                    time.sleep(wait_sec)
                    return True
                elif toolbar_name == "동영상" and "video" in accept:
                    self.driver.execute_script(
                        "arguments[0].style.display='block'; arguments[0].style.visibility='visible';", inp)
                    inp.send_keys(abs_path)
                    self.log(f"[성공] 기존 input으로 업로드: {os.path.basename(filepath)}")
                    time.sleep(wait_sec)
                    return True

            # file input click 차단 시작
            self._intercept_file_input_clicks()

            # 팝업 오버레이 제거 (클릭 차단 방지)
            self._remove_overlays()

            # 1. 툴바 버튼 클릭 (JS 클릭 - 오버레이 무시)
            self.log(f"[업로드] '{toolbar_name}' 툴바 버튼 클릭...")
            toolbar_btn = self._find_toolbar_button(toolbar_name)
            if not toolbar_btn:
                self._restore_file_input_clicks()
                self.log(f"[오류] '{toolbar_name}' 툴바 버튼을 찾을 수 없습니다.")
                return False
            self._safe_click(toolbar_btn, f"'{toolbar_name}' 툴바 버튼")
            time.sleep(2)

            # 2. 패널 내 업로드 버튼 클릭 (예: "동영상 추가", "사진 올리기" 등)
            upload_btn = None
            try:
                upload_btn = self.driver.find_element(
                    By.XPATH, f"//button[contains(., '{panel_btn_text}')]")
            except NoSuchElementException:
                try:
                    upload_btn = self.driver.find_element(
                        By.XPATH, f"//a[contains(., '{panel_btn_text}')]")
                except NoSuchElementException:
                    pass

            if upload_btn:
                self.log(f"[업로드] '{panel_btn_text}' 버튼 클릭...")
                self._safe_click(upload_btn, f"'{panel_btn_text}' 버튼")
                time.sleep(1)

            # 3. 차단된 file input 찾기 (여러 번 재시도)
            file_input = None
            for attempt in range(5):
                file_input = self._get_intercepted_file_input()
                if file_input:
                    self.log("[성공] 인터셉트된 file input 발견")
                    break
                # DOM에서 직접 찾기
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                captured_count = self.driver.execute_script(
                    "return (window.__capturedFileInputs || []).length;")
                self.log(f"[대기] file input 탐색 중... ({attempt+1}/5) DOM: {len(inputs)}, 캡처: {captured_count}")
                if inputs:
                    file_input = inputs[-1]
                    break
                time.sleep(1)

            if file_input:
                self.driver.execute_script(
                    "arguments[0].style.display='block'; arguments[0].style.visibility='visible';"
                    "arguments[0].style.height='1px'; arguments[0].style.width='1px';"
                    "arguments[0].style.opacity='1'; arguments[0].style.position='absolute';",
                    file_input)
                file_input.send_keys(abs_path)
                self.log(f"[성공] 업로드 시작: {os.path.basename(filepath)}")
                self._restore_file_input_clicks()
                time.sleep(wait_sec)
                return True

            # 최후 수단: 동영상 패널이 열려있으면 닫고, 패널 내 file input 찾기
            self._restore_file_input_clicks()
            self.log("[경고] file input을 찾지 못함 - 미디어 건너뜀")
            return False

        except Exception as e:
            self._restore_file_input_clicks()
            self.log(f"[오류] 업로드 실패: {e}")
            return False

    def _upload_via_drop(self, filepath, drop_zone_selector, wait_sec=5):
        """드래그&드롭 시뮬레이션으로 파일 업로드

        1. 임시 <input type="file"> 생성 -> send_keys로 파일 설정
        2. File 객체 추출 -> DataTransfer에 담기
        3. drop 이벤트를 드롭존에 디스패치
        """
        abs_path = os.path.abspath(filepath)
        try:
            # 1. 임시 file input 생성
            self.driver.execute_script("""
                var input = document.createElement('input');
                input.type = 'file';
                input.id = '__temp_file_drop__';
                input.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;';
                document.body.appendChild(input);
            """)

            temp_input = self.driver.find_element(By.ID, "__temp_file_drop__")
            temp_input.send_keys(abs_path)
            time.sleep(0.5)

            # 2. 드롭존에 드래그&드롭 이벤트 시뮬레이션
            result = self.driver.execute_script(f"""
                var input = document.getElementById('__temp_file_drop__');
                if (!input || !input.files || input.files.length === 0) {{
                    input && input.remove();
                    return 'NO_FILE';
                }}

                var file = input.files[0];
                var dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);

                // 드롭존 찾기 (여러 후보)
                var selectors = '{drop_zone_selector}'.split(',');
                var dropZone = null;
                for (var i = 0; i < selectors.length; i++) {{
                    dropZone = document.querySelector(selectors[i].trim());
                    if (dropZone) break;
                }}

                if (!dropZone) {{
                    input.remove();
                    return 'NO_DROPZONE';
                }}

                // 드래그&드롭 이벤트 순차 발생
                ['dragenter', 'dragover', 'drop'].forEach(function(eventName) {{
                    var event = new DragEvent(eventName, {{
                        bubbles: true,
                        cancelable: true,
                        dataTransfer: dataTransfer
                    }});
                    dropZone.dispatchEvent(event);
                }});

                input.remove();
                return 'OK';
            """)

            if result == 'OK':
                self.log(f"[성공] 드래그&드롭 업로드: {os.path.basename(filepath)}")
                time.sleep(wait_sec)
                return True
            elif result == 'NO_DROPZONE':
                self.log("[오류] 드롭존을 찾을 수 없습니다.")
            else:
                self.log(f"[오류] 드래그&드롭 실패: {result}")

            return False

        except Exception as e:
            self.log(f"[오류] 드래그&드롭 오류: {e}")
            # 임시 input 정리
            try:
                self.driver.execute_script(
                    "var el = document.getElementById('__temp_file_drop__'); if(el) el.remove();")
            except Exception:
                pass
            return False

    def _upload_image(self, filepath):
        """이미지 업로드"""
        self._remove_overlays()
        # 먼저 file input 방식 시도
        result = self._upload_media(filepath, "사진", "사진 올리기", wait_sec=3)
        if result:
            return True
        # 실패하면 드래그&드롭 시도
        self.log("[업로드] 이미지 드래그&드롭으로 재시도...")
        return self._upload_via_drop(filepath,
            ".se-body, .__se-body, .se-component.se-text", wait_sec=3)

    def _upload_video(self, filepath):
        """영상 업로드 (네이티브 파일 다이얼로그에 pyautogui로 경로 입력)"""
        abs_path = os.path.abspath(filepath).replace('/', '\\')
        if not os.path.exists(abs_path):
            self.log(f"[오류] 영상 파일 없음: {abs_path}")
            return False

        try:
            # 1. 동영상 패널이 열려있는지 확인, 없으면 열기
            upload_btn = None
            try:
                # 정확한 CSS 셀렉터로 패널 내 "동영상 추가" 버튼 찾기
                upload_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button.nvu_btn_append.nvu_local")
            except NoSuchElementException:
                # 패널이 없으면 열기
                self.driver.execute_script("""
                    document.querySelectorAll('.se-popup-dim, .se-popup-dim-transparent, .se-popup-alert').forEach(el => {
                        el.style.pointerEvents = 'none'; el.style.display = 'none';
                    });
                    document.querySelectorAll('.se-popup-video-upload').forEach(el => el.remove());
                """)
                time.sleep(0.5)
                toolbar_btn = self._find_toolbar_button("동영상")
                if toolbar_btn:
                    self.driver.execute_script("arguments[0].click();", toolbar_btn)
                    time.sleep(3)
                    try:
                        upload_btn = self.driver.find_element(
                            By.CSS_SELECTOR, "button.nvu_btn_append.nvu_local")
                    except NoSuchElementException:
                        pass

            if not upload_btn:
                self.log("[오류] '동영상 추가' 버튼을 찾을 수 없습니다. 드롭 방식으로 우회 시도합니다.")
                drop_result = self._upload_via_drop(abs_path, ".se-popup-video-upload, .se-popup-alert, body", wait_sec=10)
                if drop_result:
                    return True
                return False

            # 2. "동영상 추가" 버튼 클릭 (블로킹 방지를 위해 별도 스레드에서 실행)
            self.log("[업로드] '동영상 추가' 버튼 클릭 (백그라운드 스레드)...")
            import threading
            from selenium.webdriver.common.action_chains import ActionChains

            def click_upload():
                try:
                    # JS click으로 안 열리는 경우를 대비해 물리적 ActionChains 사용
                    ActionChains(self.driver).move_to_element(upload_btn).click().perform()
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", upload_btn)
                    except:
                        pass

            t = threading.Thread(target=click_upload, daemon=True)
            t.start()
            
            # 다이얼로그 창 뜰 때까지 대기
            time.sleep(4)

            # 다이얼로그 확인
            import pygetwindow as gw
            dialog_win = None
            for win in gw.getAllWindows():
                if '열기' in win.title or 'Open' in win.title:
                    dialog_win = win
                    break

            if not dialog_win:
                self.log("[오류] 파일 다이얼로그를 열 수 없습니다. 동영상 건너뜀.")
                pyautogui.press('escape')
                time.sleep(1)
                return False

            # 3. 다이얼로그에 경로 입력
            dialog_win.activate()
            time.sleep(0.5)
            self.log(f"[확인] 다이얼로그 활성: {dialog_win.title}")
            self.log(f"[업로드] 파일 경로 입력: {abs_path}")

            import pyperclip
            pyperclip.copy(abs_path)
            time.sleep(0.3)
            # 한국어/영어 윈도우 상관없이 파일 경로 입력 (alt+n 대신 포커스가 이미 되어있음을 가정하고 바로 타입)
            # 만약 포커스가 안맞으면 클립보드 붙여넣기가 안먹힐 수 있으므로, 탭을 몇 번 누르거나 하는 방법 대신 안전하게 클립보드 전송
            pyautogui.write(abs_path) 
            time.sleep(0.5)
            # 확실히 하기 위해 클립보드 내용 직접 붙여넣기 (경로가 길 때를 대비)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)

            # 4. 업로드 대기
            self.log("[업로드] 동영상 업로드 대기 중...")
            time.sleep(10)

            # 5. 동영상 제목 입력 (pyautogui 물리 클릭 + 타이핑)
            self.log("[업로드] 동영상 제목 입력 중...")
            video_title = "추출영상"  # 간단한 제목

            title_input = None
            for selector in [
                "input[placeholder*='제목']",
                ".nvu_inp_title input",
                "input.nvu_inp",
            ]:
                try:
                    title_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if title_input:
                # 좌표 계산 후 물리 클릭
                t_rect = self.driver.execute_script("""
                    var r = arguments[0].getBoundingClientRect();
                    return {left: r.left, top: r.top, width: r.width, height: r.height};
                """, title_input)

                # 크롬 창 좌표 새로 가져오기
                c_win = None
                for w in gw.getAllWindows():
                    if '블로그' in w.title or 'blog' in w.title.lower() or '네이버' in w.title:
                        c_win = w
                        break
                if not c_win:
                    c_win = chrome_win

                vp_h = self.driver.execute_script("return window.innerHeight;")
                c_ui = c_win.height - vp_h

                tx = int(c_win.left + t_rect['left'] + t_rect['width'] / 2)
                ty = int(c_win.top + c_ui + t_rect['top'] + t_rect['height'] / 2)

                pyautogui.click(tx, ty)
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.press('delete')
                time.sleep(0.1)
                pyperclip.copy(video_title)
                pyautogui.hotkey('ctrl', 'v')
                self.log(f"[성공] 동영상 제목 입력: {video_title}")
                time.sleep(0.5)

            # 6. 완료 버튼: Tab으로 이동 후 Enter
            self.log("[업로드] Tab으로 '완료' 버튼 이동 후 Enter...")
            time.sleep(0.3)
            # 제목 필드에서 Tab으로 완료 버튼까지 이동
            # 순서: 제목 → 정보 → 태그편집 → 태그추가 → AI활용 → 완료
            for _ in range(6):
                pyautogui.press('tab')
                time.sleep(0.2)
            pyautogui.press('enter')
            time.sleep(3)

            # 패널이 닫혔는지 확인
            panel_closed = False
            try:
                self.driver.find_element(By.CSS_SELECTOR, ".se-popup-video-upload")
                # 패널이 아직 있으면 추가 시도
                self.log("[경고] 패널 아직 열려있음 - Tab+Enter 재시도")
                for _ in range(3):
                    pyautogui.press('tab')
                    time.sleep(0.1)
                pyautogui.press('enter')
                time.sleep(3)
            except NoSuchElementException:
                panel_closed = True

            if panel_closed:
                self.log("[성공] 동영상 패널 닫힘")
            else:
                self.log("[경고] 패널이 닫히지 않음 - ESC로 닫기 시도")
                pyautogui.press('escape')
                time.sleep(1)

            self.log(f"[성공] 동영상 업로드 완료: {os.path.basename(filepath)}")
            return True

        except Exception as e:
            self.log(f"[오류] 영상 업로드 실패: {e}")
            try:
                pyautogui.press('escape')
            except Exception:
                pass
            return False

    def _find_toolbar_button(self, button_text):
        """스마트에디터 툴바에서 버튼 찾기"""
        try:
            # aria-label 또는 title로 찾기
            for attr in ["aria-label", "title", "data-tooltip"]:
                try:
                    btn = self.driver.find_element(
                        By.CSS_SELECTOR, f"button[{attr}*='{button_text}']"
                    )
                    self.log(f"[성공] 툴바 버튼 발견: {button_text} ({attr})")
                    return btn
                except NoSuchElementException:
                    continue

            # 텍스트로 찾기
            try:
                btn = self.driver.find_element(
                    By.XPATH, f"//button[contains(., '{button_text}')]"
                )
                self.log(f"[성공] 툴바 버튼 발견: {button_text} (텍스트)")
                return btn
            except NoSuchElementException:
                pass

            # span 텍스트로 찾기
            try:
                btn = self.driver.find_element(
                    By.XPATH, f"//button[.//span[contains(text(), '{button_text}')]]"
                )
                self.log(f"[성공] 툴바 버튼 발견: {button_text} (span)")
                return btn
            except NoSuchElementException:
                pass

            self.log(f"[실패] 툴바 버튼을 찾지 못함: {button_text}")
        except Exception as e:
            self.log(f"[경고] 툴바 버튼 탐색 오류: {e}")

        return None

    # --- 내부 헬퍼 메서드 ---

    def _switch_to_editor_iframe(self):
        """여러 후보 셀렉터로 에디터 iframe 전환 시도"""
        for selector in SELECTORS["editor_iframes"]:
            try:
                iframe = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.driver.switch_to.frame(iframe)
                self.log(f"[성공] iframe 전환: {selector}")
                return True
            except (TimeoutException, NoSuchElementException):
                continue

        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.log(f"[탐색] 페이지 내 iframe 수: {len(iframes)}")
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute("src") or ""
                name = iframe.get_attribute("name") or ""
                if "post" in src.lower() or "editor" in src.lower() or name == "mainFrame":
                    self.driver.switch_to.frame(iframe)
                    self.log(f"[성공] iframe 전환: iframe[{i}]")
                    return True
        except Exception:
            pass

        self.log("[정보] 에디터 iframe 없음 - 현재 프레임에서 진행")
        return False

    def _find_element_multi(self, selectors, name="요소"):
        """여러 CSS 셀렉터를 순차 시도하여 첫 번째 매칭 요소 반환"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.log(f"[성공] {name} 요소 발견: {selector}")
                return element
            except (TimeoutException, NoSuchElementException):
                continue

        xpath_map = {
            "제목": ["//*[contains(@placeholder, '제목')]", "//*[contains(@class, 'title')]"],
            "본문": ["//*[@contenteditable='true']"],
        }
        for xpath in xpath_map.get(name, []):
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                self.log(f"[성공] {name} 요소 발견 (XPath): {xpath}")
                return element
            except NoSuchElementException:
                continue

        self.log(f"[실패] {name} 요소를 찾지 못했습니다.")
        return None

    def _publish_post(self):
        """발행 버튼 물리 클릭"""
        import pygetwindow as gw

        try:
            self._remove_overlays()
            time.sleep(0.5)

            # 발행 버튼 찾기
            publish_btn = self._find_element_multi(SELECTORS["publish_btns"], "발행 버튼")
            if not publish_btn:
                try:
                    publish_btn = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), '발행')]")
                except NoSuchElementException:
                    self.log("[오류] 발행 버튼을 찾을 수 없습니다.")
                    return False

            # 물리 클릭
            self._physical_click(publish_btn, "발행 버튼")
            time.sleep(3)

            # 발행 확인 버튼
            self._remove_overlays()
            confirm_btn = self._find_element_multi(SELECTORS["publish_confirm_btns"], "확인 버튼")
            if not confirm_btn:
                try:
                    confirm_btn = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), '확인')]")
                except NoSuchElementException:
                    pass

            if confirm_btn:
                time.sleep(1)
                self._physical_click(confirm_btn, "발행 확인 버튼")
                time.sleep(3)

            self.log("[완료] 글이 발행되었습니다.")
            return True

        except Exception as e:
            self.log(f"[오류] 발행 실패: {e}")
            return False

    def _physical_click(self, element, description="요소"):
        """pygetwindow 좌표로 pyautogui 물리 클릭"""
        import pygetwindow as gw

        try:
            # 크롬 창 찾기
            chrome_win = None
            for w in gw.getAllWindows():
                if '블로그' in w.title or 'blog' in w.title.lower() or '네이버' in w.title:
                    chrome_win = w
                    break

            if not chrome_win:
                self.log(f"[경고] 크롬 창 못 찾음 - JS 클릭으로 대체: {description}")
                self.driver.execute_script("arguments[0].click();", element)
                return

            # 좌표 계산
            vp_h = self.driver.execute_script("return window.innerHeight;")
            chrome_ui = chrome_win.height - vp_h

            rect = self.driver.execute_script("""
                var r = arguments[0].getBoundingClientRect();
                return {left: r.left, top: r.top, width: r.width, height: r.height};
            """, element)

            sx = int(chrome_win.left + rect['left'] + rect['width'] / 2)
            sy = int(chrome_win.top + chrome_ui + rect['top'] + rect['height'] / 2)
            self.log(f"[클릭] {description} 좌표: ({sx},{sy})")

            pyautogui.click(sx, sy)
        except Exception as e:
            self.log(f"[경고] 물리 클릭 실패, JS 클릭 대체: {description} - {e}")
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception:
                pass
