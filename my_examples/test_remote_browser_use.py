import sys
import os
import requests
import asyncio
import subprocess
import logging
import json
import time
import platform
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# 1. 이 프로그램의 로그는 항상 고정 경로 (절대 경로로 직접 지정)
my_program_log_dir = "/Users/bombbie/Developer/browser-use-fork/my_examples/logs"
os.makedirs(my_program_log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(my_program_log_dir, "test_remote_browser_use.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("standalone_browser_agent")

# 2. browser-use의 로그는 환경변수만 사용
browser_use_log_dir = os.environ.get("PLAYWRIGHT_LOG_DIR", "/tmp/browser_agent_logs")
os.makedirs(browser_use_log_dir, exist_ok=True)

# 환경변수 로드
load_dotenv()


def is_chrome_debugging_available(port=9222, retries=3, retry_interval=2):
    url = f"http://127.0.0.1:{port}/json/version"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"기존 Chrome 디버깅 세션 발견 (포트: {port})")
                return True
        except requests.exceptions.RequestException as e:
            print(f"연결 시도 {attempt + 1}/{retries} 실패: {e}")
        if attempt < retries - 1:
            time.sleep(retry_interval)
    return False


def kill_existing_chrome():
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["pkill", "-f", "Google Chrome"], check=False)
        elif system == "Windows":
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], check=False)
        else:
            subprocess.run(["pkill", "-f", "chrome"], check=False)
        print("기존 Chrome 프로세스를 종료했습니다.")
        time.sleep(2)
    except Exception as e:
        print(f"Chrome 프로세스 종료 중 오류: {e}")


def start_chrome_debugging(port=9222, kill_existing=True):
    system = platform.system()
    if kill_existing:
        kill_existing_chrome()
    temp_dir = os.path.join(os.path.expanduser("~"), ".chrome-debug-data")
    os.makedirs(temp_dir, exist_ok=True)
    if system == "Darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Windows":
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        if not chrome_path:
            raise Exception("Chrome 실행 파일을 찾을 수 없습니다.")
    else:
        chrome_path = "google-chrome"
    if system == "Darwin" and not os.path.exists(chrome_path):
        raise Exception(f"Chrome 실행 파일을 찾을 수 없습니다: {chrome_path}")
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={temp_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--remote-allow-origins=*",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
    ]
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if system != "Windows" else None,
        )
        print(f"Chrome 디버깅 모드로 시작됨 (PID: {process.pid}, 포트: {port})")
        for i in range(10):
            if is_chrome_debugging_available(port):
                print(f"Chrome 디버깅 세션 준비 완료 (시도: {i+1})")
                return process
            print(f"Chrome 시작 대기 중... ({i+1}/10)")
            time.sleep(1)
        print("Chrome 디버깅 세션이 시작되었지만 연결할 수 없습니다.")
        return process
    except Exception as e:
        print(f"Chrome 시작 중 오류 발생: {e}")
        return None


async def run_agent(task, save_conversation_path="/tmp/conversation.json", use_vision=False):
    browser = None
    context = None
    chrome_process = None
    print("initializing config...")
    load_dotenv()
    try:
        import browser_use.playwright_logger
        from browser_use.playwright_logger import get_playwright_logger
        browser_use.playwright_logger._instance = None
        logger = get_playwright_logger(log_dir=browser_use_log_dir)
    except Exception as e:
        print(f"PlaywrightLogger 초기화 오류: {e}")
    config = BrowserContextConfig(
        cookies_file="/tmp/cookies.json",
        wait_for_network_idle_page_load_time=3.0,
        browser_window_size={"width": 1280, "height": 1100},
        locale="en-US",
        highlight_elements=True,
        viewport_expansion=500,
        save_recording_path=browser_use_log_dir,
    )
    print(f"BrowserContextConfig 생성 완료 => {config}")
    debugging_port = 9222
    browser_created = False
    try:
        if is_chrome_debugging_available(port=debugging_port):
            print("기존 Chrome 디버깅 세션에 연결 시도...")
            try:
                browser = Browser(
                    config=BrowserConfig(
                        headless=False,
                        cdp_url=f"http://127.0.0.1:{debugging_port}",
                    )
                )
                browser_created = True
                print("기존 Chrome 세션에 연결 성공")
            except Exception as e:
                print(f"기존 Chrome 세션 연결 실패: {e}")
        if not browser_created:
            print("새 Chrome 디버깅 세션 시작...")
            chrome_process = start_chrome_debugging(port=debugging_port)
            if chrome_process and is_chrome_debugging_available(port=debugging_port):
                try:
                    browser = Browser(
                        config=BrowserConfig(
                            headless=False,
                            cdp_url=f"http://127.0.0.1:{debugging_port}",
                        )
                    )
                    browser_created = True
                    print("새 Chrome 디버깅 세션에 연결 성공")
                except Exception as e:
                    print(f"새 Chrome 디버깅 세션 연결 실패: {e}")
        if not browser_created:
            print("직접 Chrome 인스턴스 생성...")
            browser = Browser(
                config=BrowserConfig(
                    headless=False,
                    chrome_instance_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                )
            )
            browser_created = True
            print("직접 Chrome 인스턴스 생성 성공")
    except Exception as e:
        error_msg = f"Browser 초기화 최종 실패: {str(e)}"
        print(error_msg)
        return error_msg
    if not browser_created or browser is None:
        error_msg = "모든 브라우저 연결 방법이 실패했습니다."
        print(error_msg)
        return error_msg
    print(f"Browser 생성 완료 => {browser}")
    try:
        context = BrowserContext(config=config, browser=browser)
        print("BrowserContext 생성 완료")
    except Exception as e:
        error_msg = f"BrowserContext 초기화 오류: {str(e)}"
        print(error_msg)
        return error_msg
    try:
        llm = ChatOpenAI(model="gpt-4o")
        print("LLM 생성 완료")
        print("Agent 생성 중...")
        agent = Agent(
            browser_context=context,
            task=task,
            llm=llm,
            save_conversation_path=save_conversation_path,
            use_vision=use_vision,
        )
        print("Agent 생성 완료")
        print(f"실행할 작업: {task}")
        result = await agent.run()
        try:
            final_result = (
                result.final_result()
                if hasattr(result, "final_result")
                else str(result)
            )
            is_done = result.is_done() if hasattr(result, "is_done") else True
            errors = result.errors() if hasattr(result, "errors") else []
            print("=== 실행 결과 ===")
            print(f"완료 여부: {is_done}")
            print(f"최종 결과: {final_result}")
            print(f"오류: {errors}")
        except Exception as e:
            print(f"결과 처리 중 오류: {e}")
            final_result = "결과 처리 중 오류가 발생했습니다."
    except Exception as e:
        error_msg = f"Agent 실행 오류: {str(e)}"
        print(error_msg)
        return error_msg
    log_file_path = os.path.join(browser_use_log_dir, "automation_log.log")
    log_content = ""
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            print(f"로그 파일 읽기 성공: {log_file_path}")
        else:
            log_content = "로그 파일을 찾을 수 없습니다."
            print(f"로그 파일 없음: {log_file_path}")
    except Exception as e:
        log_content = f"로그 파일 읽기 오류: {str(e)}"
        print(f"로그 파일 읽기 오류: {e}")
    if not isinstance(final_result, str):
        try:
            final_result = json.dumps(final_result, ensure_ascii=False, indent=2)
        except:
            final_result = str(final_result)
    combined_result = f"{final_result}\n\n--- AUTOMATION LOG ---\n\n{log_content}"
    print("Agent 실행 완료")
    print(combined_result)
    return combined_result


def main():
    task_file = os.environ.get("TASK_FILE_PATH")
    if not task_file or not os.path.exists(task_file):
        print("환경변수 TASK_FILE_PATH에 유효한 파일 경로를 지정하세요.")
        sys.exit(1)
    with open(task_file, "r", encoding="utf-8") as f:
        task = f.read().strip()
    print(f"TASK: {task}")
    asyncio.run(run_agent(task))

    # 로그 파일 경로 및 내용 출력
    log_file_path = os.path.join(browser_use_log_dir, "automation_log.log")
    print(f"로그 파일 경로: {log_file_path}")
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        print("--- 로그 파일 내용 ---")
        print(log_content)
    else:
        print("로그 파일이 존재하지 않습니다.")
    print(f"로그 파일 경로: {log_file_path}")

if __name__ == "__main__":
    main() 