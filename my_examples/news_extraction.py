#!/usr/bin/env python
"""
뉴스 기사 추출 자동화 예제
"""

import asyncio
import json
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

# 출력 형식 정의 (JSON 스키마)
OUTPUT_SCHEMA = {
    "articles": [
        {
            "title": "str",
            "url": "str",
            "summary": "str",
            "source": "str"
        }
    ]
}

async def main():
    # 로거 초기화
    logger = get_playwright_logger(log_dir=LOG_DIR, session_id="news_extraction")
    
    # 브라우저 설정
    browser = Browser()
    
    # LLM 설정
    llm = ChatOpenAI(model="gpt-4o")
    
    # 에이전트 설정
    agent = Agent(
        task="""
        1. Go to https://news.ycombinator.com/
        2. Extract the top 5 news articles
        3. For each article, get the title, URL, and a brief summary
        4. Return the results as a JSON with the following structure:
           {
             "articles": [
               {
                 "title": "Article title",
                 "url": "Article URL",
                 "summary": "Brief summary",
                 "source": "Source website"
               }
             ]
           }
        """,
        llm=llm,
        browser=browser,
        use_vision=True
    )
    
    # 작업 실행
    result = await agent.run()
    
    # 결과 출력
    print("\n=== 작업 결과 ===")
    for i, history_item in enumerate(result.history):
        if history_item.result:
            for res in history_item.result:
                if res.extracted_content and res.is_done:
                    try:
                        # JSON 형식으로 파싱
                        articles_data = json.loads(res.extracted_content)
                        
                        # 결과 저장
                        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news_articles.json")
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(articles_data, f, ensure_ascii=False, indent=2)
                        
                        print(f"뉴스 기사가 {output_file}에 저장되었습니다.")
                        
                        # 간단한 요약 출력
                        if "articles" in articles_data:
                            for idx, article in enumerate(articles_data["articles"]):
                                print(f"\n기사 {idx+1}: {article['title']}")
                                print(f"출처: {article['source']}")
                                print(f"요약: {article['summary']}")
                    except json.JSONDecodeError:
                        print(res.extracted_content)
    
    # Playwright 코드 생성
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news_extraction_automation.js")
    playwright_code = logger.generate_playwright_code(output_file=output_file)
    print(f"\n자동화 코드가 생성되었습니다: {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 