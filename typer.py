# typer.py - 타이핑 시뮬레이션 모듈

import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from config import (
    TYPING_MIN_DELAY, TYPING_MAX_DELAY,
    PARAGRAPH_MIN_DELAY, PARAGRAPH_MAX_DELAY,
)


def type_like_human(driver, element, text, click=True):
    """사람처럼 한 글자씩 타이핑하는 함수

    네이버 스마트에디터는 contenteditable 기반이므로
    ActionChains.send_keys()를 사용하여 실제 키보드 입력을 시뮬레이션한다.

    Args:
        driver: Selenium WebDriver 인스턴스
        element: 입력 대상 웹 요소
        text: 입력할 텍스트
        click: True면 요소를 클릭하여 포커스, False면 현재 포커스 유지
    """
    if click:
        element.click()
        time.sleep(0.5)

    for char in text:
        if char == '\n':
            ActionChains(driver).send_keys(Keys.ENTER).perform()
        else:
            ActionChains(driver).send_keys(char).perform()

        # 글자마다 랜덤 딜레이
        time.sleep(random.uniform(TYPING_MIN_DELAY, TYPING_MAX_DELAY))

    # 입력 완료 후 잠시 대기
    time.sleep(random.uniform(PARAGRAPH_MIN_DELAY, PARAGRAPH_MAX_DELAY))


def random_pause(min_sec, max_sec):
    """랜덤한 시간 동안 대기"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay
