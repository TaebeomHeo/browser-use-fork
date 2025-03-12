#!/usr/bin/env python
"""
기본적인 브라우저 자동화 예제
"""

import asyncio
import os
import sys
from pathlib import Path

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

# 환경 변수에서 로그 디렉토리 설정 (없으면 기본값 사용)
LOG_DIR = os.environ.get('PLAYWRIGHT_LOG_DIR', 
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))

# 상대 경로를 절대 경로로 변환
if LOG_DIR.startswith('./'):
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', LOG_DIR[2:]))

# 싱글톤 인스턴스 초기화를 위해 모듈 변수 직접 접근
import browser_use.playwright_logger
browser_use.playwright_logger._instance = None

async def main():
    # 로그 디렉토리 출력
    print(f"로그 디렉토리: {LOG_DIR}")
    
    # 로그 디렉토리가 존재하지 않으면 생성
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 로거 초기화 (로그 디렉토리 지정)
    logger = get_playwright_logger(log_dir=LOG_DIR)
    
    # 브라우저 설정
    browser = Browser()
    
    # LLM 설정 (OpenAI API 키가 환경 변수에 설정되어 있어야 함)
    llm = ChatOpenAI(model="gpt-4o")
    
    # 에이전트 설정
    agent = Agent(
        task="Visit example.com, click on the 'More information' link, and extract the main content",
        llm=llm,
        browser=browser,
        use_vision=True,  # 스크린샷 사용
    )
    
    # 작업 실행 (이 과정에서 모든 액션이 자동으로 로깅됨)
    result = await agent.run()
    
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

if __name__ == "__main__":
    asyncio.run(main()) 