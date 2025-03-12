#!/usr/bin/env python
"""
폼 작성 자동화 예제
"""

import asyncio
import os
import sys

# 로컬 모듈 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_openai import ChatOpenAI

# 로컬 모듈 import
from browser_use import Agent, Browser
from browser_use.playwright_logger import get_playwright_logger

# 로그 디렉토리 설정
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

async def main():
    # 로거 초기화
    logger = get_playwright_logger(log_dir=LOG_DIR, session_id="form_filling")
    
    # 브라우저 설정
    browser = Browser()
    
    # LLM 설정
    llm = ChatOpenAI(model="gpt-4o")
    
    # 에이전트 설정
    agent = Agent(
        task="""
        1. Go to https://httpbin.org/forms/post
        2. Fill out the form with the following information:
           - Customer name: John Doe
           - Size: Large
           - Topping: Bacon
           - Check the 'Cheese' option
           - Write "Extra crispy please" in the comments
        3. Submit the form
        4. Extract the response data
        """,
        llm=llm,
        browser=browser,
        use_vision=True,
    )
    
    # 작업 실행
    result = await agent.run()
    
    # 결과 출력
    print("\n=== 작업 결과 ===")
    for i, history_item in enumerate(result.history):
        if history_item.result:
            for res in history_item.result:
                if res.extracted_content:
                    print(f"Step {i+1}: {res.extracted_content}")
    
    # Playwright 코드 생성
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "form_filling_automation.js")
    playwright_code = logger.generate_playwright_code(output_file=output_file)
    print(f"\n자동화 코드가 생성되었습니다: {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 