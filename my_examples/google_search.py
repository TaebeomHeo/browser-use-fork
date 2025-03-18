#!/usr/bin/env python
"""
구글 검색 자동화 예제
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 로컬 모듈 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# .env 파일 로드
from dotenv import load_dotenv
# 프로젝트 루트 디렉토리의 .env 파일 로드
dotenv_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))).joinpath('.env')
load_dotenv(dotenv_path=dotenv_path)

from langchain_openai import ChatOpenAI

# 로컬 모듈 import
from browser_use import Agent, Browser
from browser_use.playwright_logger import get_playwright_logger, PlaywrightLogger
import logging

# 디버깅을 위한 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 현재 시간을 포함한 세션 ID 생성
SESSION_ID = f"google_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 로그 디렉토리 설정 - 환경 변수 또는 기본값 사용
# 타임스탬프가 포함된 세션별 디렉토리만 사용하여 중복 로그 생성 방지
LOG_DIR = os.environ.get('PLAYWRIGHT_LOG_DIR', 
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", SESSION_ID))

# 상대 경로를 절대 경로로 변환
if LOG_DIR.startswith('./'):
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', LOG_DIR[2:]))

# 싱글톤 인스턴스 초기화를 위해 모듈 변수 직접 접근 (새 세션 시작 시 초기화)
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
    
    # 로거 초기화 - 싱글톤 패턴이므로 이 초기화만으로 전체 시스템에서 사용됨
    logger = get_playwright_logger(log_dir=LOG_DIR, session_id=SESSION_ID)
    
    # 브라우저 설정
    browser = Browser()
    
    # LLM 설정
    llm = ChatOpenAI(model="gpt-4o")
    
    # 에이전트 설정
    agent = Agent(
        task="""
        1. Go to naver.com
        2. Search for "Python browser automation"
        3. Click on the first result
        4. Extract the main content of the page
        5. Return a summary of what you found
        """,
        llm=llm,
        browser=browser,
        use_vision=True,
    )
    
    # 작업 실행 시작 시간 기록
    start_time = datetime.now()
    print(f"작업 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 작업 실행
    result = await agent.run()
    
    # 작업 실행 종료 시간 기록
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    print(f"작업 종료: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"총 소요 시간: {duration:.2f}초")
    
    # 결과 출력
    print("\n=== 작업 결과 ===")
    for i, history_item in enumerate(result.history):
        if history_item.result:
            for res in history_item.result:
                if res.extracted_content:
                    print(f"Step {i+1}: {res.extracted_content}")
    
    # 로그 파일 정보 출력
    log_info = logger.generate_playwright_code()
    print(f"\n로그 정보: {log_info}")
    
    # 로그 요약 출력
    print_log_summary(LOG_DIR)

if __name__ == "__main__":
    asyncio.run(main()) 