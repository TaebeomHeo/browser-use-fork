# Browser Use 예제

이 디렉토리에는 Browser Use 라이브러리를 사용한 다양한 브라우저 자동화 예제가 포함되어 있습니다.

## 사전 요구 사항

1. Python 3.9 이상
2. Playwright 설치
3. OpenAI API 키 (환경 변수에 설정)

## 설치 방법

```bash
# 필요한 패키지 설치
pip install browser-use langchain-openai

# Playwright 브라우저 설치
playwright install
```

## 환경 변수 설정

`.env` 파일을 생성하고 다음과 같이 API 키를 설정하세요:

```
OPENAI_API_KEY=your_api_key_here
```

## 예제 실행 방법

### 1. 기본 자동화 예제

```bash
python basic_automation.py
```

이 예제는 example.com 웹사이트를 방문하고 'More information' 링크를 클릭한 후 콘텐츠를 추출합니다.

### 2. 구글 검색 예제

```bash
python google_search.py
```

이 예제는 Google에서 "Python browser automation"을 검색하고 첫 번째 결과를 클릭한 후 콘텐츠를 추출합니다.

### 3. 폼 작성 예제

```bash
python form_filling.py
```

이 예제는 httpbin.org의 폼을 작성하고 제출한 후 응답 데이터를 추출합니다.

### 4. 뉴스 기사 추출 예제

```bash
python news_extraction.py
```

이 예제는 Hacker News에서 상위 5개 뉴스 기사를 추출하고 JSON 형식으로 저장합니다.

## 생성된 파일

각 예제를 실행하면 다음과 같은 파일이 생성됩니다:

1. `logs/` 디렉토리: 모든 브라우저 액션의 로그 파일
2. `*.js` 파일: Playwright를 사용한 Node.js 자동화 스크립트
3. 기타 출력 파일 (예: `news_articles.json`)

## Playwright 스크립트 실행 방법

생성된 Playwright 스크립트를 실행하려면:

```bash
# Node.js와 Playwright 설치
npm install playwright

# 생성된 스크립트 실행
node automation.js
```

## 참고 사항

- 로그 파일은 `logs/[세션ID]/` 디렉토리에 저장됩니다.
- 각 예제는 브라우저 액션을 자세히 로깅하여 나중에 분석할 수 있게 합니다.
- 생성된 Playwright 코드는 Node.js 환경에서 실행할 수 있습니다.
