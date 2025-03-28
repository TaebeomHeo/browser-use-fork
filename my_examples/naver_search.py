#!/usr/bin/env python
"""
네이버 검색 자동화 예제
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from pydantic import SecretStr

# 로컬 모듈 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# .env 파일 로드
dotenv_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))).joinpath('.env')
load_dotenv(dotenv_path=dotenv_path)

from langchain_openai import ChatOpenAI

# 로컬 모듈 import
from browser_use import Agent, Browser, BrowserConfig
from browser_use.playwright_logger import get_playwright_logger, PlaywrightLogger
import logging

# 디버깅을 위한 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 현재 시간을 포함한 세션 ID 생성
SESSION_ID = f"naver_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 로그 디렉토리 설정
LOG_DIR = os.environ.get('PLAYWRIGHT_LOG_DIR', 
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", SESSION_ID))

# 상대 경로를 절대 경로로 변환
if LOG_DIR.startswith('./'):
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', LOG_DIR[2:]))

# 싱글톤 인스턴스 초기화를 위해 모듈 변수 직접 접근
import browser_use.playwright_logger
browser_use.playwright_logger._instance = None

# Controller 클래스의 act 메서드를 몽키패치하여 디버깅 정보 추가
from browser_use.controller.service import Controller
original_act = Controller.act

async def debug_act(self, action, browser_context):
    """액션 실행 전에 디버깅 정보를 출력하는 래퍼 함수"""
    logger.debug(f"실행 액션: {action}")
    
    # 액션 파라미터 출력
    for action_name, params in action.model_dump(exclude_unset=True).items():
        logger.debug(f"액션 이름: {action_name}")
        logger.debug(f"액션 파라미터: {params}")
        
        # 인덱스 정보 확인
        if hasattr(params, 'index'):
            logger.debug(f"요소 인덱스: {params.index}")
        
        # 텍스트 정보 확인
        if hasattr(params, 'text'):
            logger.debug(f"텍스트: {params.text}")
    
    # 원래 메서드 호출
    return await original_act(self, action, browser_context)

# 몽키패치 적용
Controller.act = debug_act

def print_log_summary(log_dir):
    """로그 파일의 요약 정보를 출력합니다."""
    json_log_file = os.path.join(log_dir, "automation_log.json")
    
    if not os.path.exists(json_log_file):
        print(f"로그 파일을 찾을 수 없습니다: {json_log_file}")
        return
    
    try:
        with open(json_log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        formatted_actions = log_data.get("formatted_actions", [])
        
        print("\n=== 액션 로그 요약 ===")
        for i, action in enumerate(formatted_actions):
            phase = action.get("phase", "")
            if phase == "pre_action":
                continue  # pre_action은 건너뛰고 post_action만 표시
            
            action_type = action.get("action_type", "")
            timestamp = action.get("timestamp", "")
            
            # 타임스탬프를 읽기 쉬운 형식으로 변환
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%H:%M:%S")
            except:
                pass
            
            print(f"{i+1}. [{timestamp}] {action_type}")
            
            # 요소 정보 출력
            element_info = action.get("element_info", {})
            if element_info:
                tag_name = element_info.get("tag_name", "")
                index = element_info.get("index", "")
                if tag_name and index:
                    print(f"   요소: {tag_name} (인덱스: {index})")
                
                # 중요 속성 출력
                attributes = element_info.get("attributes", {})
                if attributes:
                    for attr in ['id', 'class', 'name', 'type', 'value']:
                        if attr in attributes:
                            print(f"   {attr}: {attributes[attr]}")
            
            # 텍스트 내용 출력
            text = action.get("text", "")
            if text:
                print(f"   텍스트: {text}")
            
            # URL 정보 출력
            url = action.get("url", "")
            if url:
                print(f"   URL: {url}")
            
            current_url = action.get("current_url", "")
            if current_url:
                print(f"   현재 URL: {current_url}")
            
            # 변경 사항 출력
            changes = action.get("changes", {})
            if changes:
                print("   변경 사항:")
                for key, change in changes.items():
                    before = change.get("before", "")
                    after = change.get("after", "")
                    print(f"     {key}: {before} -> {after}")
            
            # 추가 데이터 출력
            additional_data = action.get("additional_data", {})
            if additional_data:
                duration = additional_data.get("duration_ms", "")
                if duration:
                    print(f"   소요 시간: {duration:.2f}ms")
                
                page_changed = additional_data.get("page_changed", False)
                if page_changed:
                    print(f"   페이지 변경됨: {page_changed}")
                    new_url = additional_data.get("new_url", "")
                    if new_url:
                        print(f"   새 URL: {new_url}")
            
            print()
        
        print(f"총 {len(formatted_actions)//2}개의 액션이 실행되었습니다.")
        print(f"상세 로그는 {log_dir} 디렉토리에서 확인할 수 있습니다.")
        
    except Exception as e:
        print(f"로그 파일 읽기 오류: {str(e)}")

async def main():
    # 로그 디렉토리 생성 및 초기화
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"로그 디렉토리: {LOG_DIR}")
    
    # 로거 초기화
    logger = get_playwright_logger(log_dir=LOG_DIR, session_id=SESSION_ID)
    
    # LLM 설정
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7,
        api_key=SecretStr(os.getenv("OPENAI_API_KEY", ""))
    )
    
    # 브라우저 설정
    browser_config = BrowserConfig(
        headless=False,  # 브라우저 UI 표시
        cdp_url="http://localhost:9222"  # Chrome DevTools Protocol URL
    )
    
    # 브라우저 인스턴스 생성
    browser = Browser(config=browser_config)
    
    # Agent 생성
    agent = Agent(
        task="네이버 검색 자동화",
        llm=llm,
        browser=browser
    )
    
    # 현재 페이지 URL 출력
    browser_context = await browser.new_context()
    page = await browser_context.get_current_page()
    print(f"\n현재 페이지 URL: {page.url}")
    
    # 사용자 입력 받기
    print("\n=== 자동화 작업 시작 ===")
    print("1. 검색어 입력")
    print("2. 검색 결과 클릭")
    print("3. 페이지 스크롤")
    print("4. 종료")
    
    while True:
        action = input("\n실행할 작업을 선택하세요 (1-4): ")
        
        if action == "1":
            search_query = input("검색어를 입력하세요: ")
            agent.task = f"Go to naver.com and search for '{search_query}'"
            await agent.run(max_steps=5)
        elif action == "2":
            result_index = input("클릭할 검색 결과의 번호를 입력하세요 (1-10): ")
            agent.task = f"Click on the {result_index}th search result"
            await agent.run(max_steps=3)
        elif action == "3":
            scroll_count = input("스크롤할 횟수를 입력하세요: ")
            for _ in range(int(scroll_count)):
                agent.task = "Scroll down the page"
                await agent.run(max_steps=2)
                await asyncio.sleep(1)
        elif action == "4":
            break
        else:
            print("잘못된 선택입니다. 다시 선택해주세요.")
    
    # 브라우저 종료
    await browser.close()
    
    # 로그 요약 출력
    print_log_summary(LOG_DIR)

if __name__ == "__main__":
    asyncio.run(main()) 