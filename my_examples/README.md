## test_remote_browser_use.py 사용법

이 스크립트는 browser-use 기반의 브라우저 자동화 테스트를 독립적으로 실행할 수 있는 예제입니다.

### 주요 특징

- **이 프로그램의 자체 로그**는 항상 절대 경로 `/Users/bombbie/Developer/browser-use-fork/my_examples/logs/test_remote_browser_use.log`에 남습니다.
- **browser-use의 자동화 로그**는 환경변수 `PLAYWRIGHT_LOG_DIR`에 지정된 경로의 `automation_log.log`에 남습니다.
- task(명령)는 환경변수 `TASK_FILE_PATH`에 지정된 파일의 내용을 읽어 사용합니다.

### 환경 변수

- `PLAYWRIGHT_LOG_DIR`: browser-use 로그가 저장될 디렉토리 (예: `/Users/bombbie/Developer/browser-use-fork/my_examples/logs`)
- `TASK_FILE_PATH`: 실행할 task(명령)가 들어있는 텍스트 파일 경로

### 실행 전 준비

1. 필요한 패키지 설치:
   ```sh
   pip install python-dotenv langchain-openai requests
   # browser-use 및 playwright 관련 패키지도 설치 필요
   ```
2. 로그 디렉토리 생성 (자동 생성됨)
3. task 파일 준비 (예: `/Users/bombbie/Developer/browser-use-fork/my_examples/task.txt`)

### 실행 방법

```sh
export PLAYWRIGHT_LOG_DIR=/Users/bombbie/Developer/browser-use-fork/my_examples/logs
export TASK_FILE_PATH=/Users/bombbie/Developer/browser-use-fork/my_examples/task.txt
python my_examples/test_remote_browser_use.py
```

### 실행 결과

- 프로그램 실행 후 아래 두 로그 파일이 생성됩니다:
  - `/Users/bombbie/Developer/browser-use-fork/my_examples/logs/test_remote_browser_use.log` : 이 프로그램의 상세 실행 로그
  - `${PLAYWRIGHT_LOG_DIR}/automation_log.log` : browser-use의 자동화/액션 로그
- 실행이 끝나면 로그 파일 경로와 로그 내용이 stdout에 출력됩니다.

### 코드 주요 구조

- **이 프로그램의 로그**: 절대 경로로 고정, 환경변수와 무관
- **browser-use의 로그**: 환경변수로만 경로 지정, 코드에서 직접 지정하지 않음
- **task 입력**: 환경변수 `TASK_FILE_PATH`에 지정된 파일의 텍스트를 읽어 사용

### 예시 task 파일

```
https://www.naver.com 방문 후, 검색창에 '파이썬' 입력하고 검색 결과 첫 번째 링크 클릭
```

### 기타

- 크롬 디버깅 포트(9222)가 열려 있어야 하며, 필요시 자동으로 크롬을 디버깅 모드로 실행합니다.
- 실행 중 발생하는 모든 에러/상태/결과는 로그 파일에 기록됩니다.

# Google 검색 자동화 예제

이 예제는 Browser Use 라이브러리를 사용하여 Google 검색을 자동화하고 검색 결과를 분석하는 방법을 보여줍니다.

## 사전 요구 사항

1. Python 3.9 이상
2. Playwright 설치
3. OpenAI API 키 (환경 변수에 설정)

## 설치 방법

```bash
# 필요한 패키지 설치
pip install browser-use langchain-openai python-dotenv

# Playwright 브라우저 설치
playwright install
```

## 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 필요한 환경 변수들을 설정하세요:

```
# 필수 환경 변수
OPENAI_API_KEY=your_api_key_here

# 로깅 관련 설정
PLAYWRIGHT_LOG_DIR=custom/log/directory  # 기본값: my_examples/logs
BROWSER_USE_LOGGING_LEVEL=info           # 로깅 레벨 설정 (debug, info, warning, error)

# 브라우저 설정
PLAYWRIGHT_HEADLESS=false                # 브라우저 표시 여부 (기본값: true)

# 기타 설정 (선택 사항)
ANONYMIZED_TELEMETRY=false               # 익명 사용 데이터 수집 비활성화
```

## 예제 실행 방법

```bash
python google_search.py
```

## 기능 설명

이 예제는 다음과 같은 작업을 수행합니다:

1. Google.com 웹사이트 방문
2. "Python browser automation" 검색어 입력
3. 첫 번째 검색 결과 클릭
4. 페이지 콘텐츠 추출
5. 추출된 내용 요약

## 로깅 기능

이 예제는 향상된 로깅 기능을 포함하고 있습니다:

1. 로그 디렉토리 자동 생성
2. 브라우저 액션 전/후 상태 기록
3. 요소 정보 상세 로깅 (태그, 속성, 위치 등)
4. 액션 실행 시간 및 페이지 변경 정보 기록
5. JSON 형식의 로그 파일 생성

## 로그 파일

실행 시 다음과 같은 로그 파일이 생성됩니다:

1. `logs/automation_log.log`: 모든 브라우저 액션의 텍스트 로그
2. `logs/automation_log.json`: JSON 형식의 구조화된 로그

## 로그 요약 기능

실행이 완료되면 콘솔에 로그 요약이 출력됩니다:

1. 각 액션의 실행 시간
2. 요소 정보 (태그, 인덱스, 속성)
3. 페이지 변경 정보
4. 액션 실행 시간

## 디버깅 기능

이 예제는 디버깅을 위한 추가 기능을 포함하고 있습니다:

1. 액션 실행 전 파라미터 로깅
2. 요소 인덱스 및 텍스트 정보 출력
3. 상세한 요소 정보 수집 및 기록

## PlaywrightLogger 클래스

PlaywrightLogger는 Browser Use 라이브러리의 핵심 로깅 컴포넌트로, 브라우저 자동화 과정에서 발생하는 모든 액션과 상태 변화를 기록합니다.

### 주요 기능

1. 액션 실행 전/후 상태 로깅 (`log_action_before_execute`, `log_action_after_execute`)
2. 요소 정보 수집 및 저장 (`store_element_info`)
3. JSON 형식의 구조화된 로그 생성
4. 텍스트 기반 로그 파일 생성

### 호출 위치

PlaywrightLogger는 다음과 같은 위치에서 초기화되고 사용됩니다:

1. **Controller 클래스**: `__init__` 메서드에서 초기화되며, `act` 메서드에서 액션 실행 전/후에 호출됩니다.

   ```python
   self.logger = PlaywrightLogger(log_dir=log_dir)
   ```

2. **Agent 클래스**: Controller를 통해 간접적으로 사용됩니다. Agent가 브라우저 액션을 실행할 때마다 Controller의 `act` 메서드가 호출되고, 이 과정에서 PlaywrightLogger가 사용됩니다.
3. **예제 스크립트**: `google_search.py`와 같은 예제 스크립트에서는 로그 디렉토리를 설정하고 PlaywrightLogger의 싱글톤 인스턴스를 초기화합니다.

   ```python
   import browser_use.playwright_logger
   browser_use.playwright_logger._instance = None
   ```

### 로깅 흐름

1. 액션 실행 전: `log_action_before_execute` 메서드가 호출되어 액션 타입, 요소 인덱스, 선택자 등의 정보를 로깅합니다.
2. 액션 실행: Controller가 액션을 실행합니다.
3. 액션 실행 후: `log_action_after_execute` 메서드가 호출되어 액션 결과, 오류, 페이지 변경 사항 등을 로깅합니다.

## 참고 사항

- 로그 파일은 `my_examples/logs/` 디렉토리에 저장됩니다.
- 기본적으로 로그 디렉토리는 스크립트 실행 디렉토리의 `logs` 폴더입니다.
- 환경 변수 `PLAYWRIGHT_LOG_DIR`를 설정하여 로그 디렉토리를 변경할 수 있습니다.
- 브라우저를 시각적으로 확인하려면 `.env` 파일에 `PLAYWRIGHT_HEADLESS=false`를 추가하세요.

---

# Google Search Automation Example

This example demonstrates how to automate Google searches and analyze search results using the Browser Use library.

## Prerequisites

1. Python 3.9 or higher
2. Playwright installation
3. OpenAI API key (set in environment variables)

## Installation

```bash
# Install required packages
pip install browser-use langchain-openai python-dotenv

# Install Playwright browsers
playwright install
```

## Environment Variables Setup

Create a `.env` file in the project root directory and set the following environment variables:

```
# Required environment variables
OPENAI_API_KEY=your_api_key_here

# Logging settings
PLAYWRIGHT_LOG_DIR=custom/log/directory  # Default: my_examples/logs
BROWSER_USE_LOGGING_LEVEL=info           # Logging level (debug, info, warning, error)

# Browser settings
PLAYWRIGHT_HEADLESS=false                # Show browser UI (default: true)

# Other settings (optional)
ANONYMIZED_TELEMETRY=false               # Disable anonymous usage data collection
```

## Running the Example

```bash
python google_search.py
```

## Functionality

This example performs the following tasks:

1. Visit Google.com website
2. Enter "Python browser automation" search query
3. Click on the first search result
4. Extract page content
5. Summarize the extracted content

## Logging Features

This example includes enhanced logging capabilities:

1. Automatic log directory creation
2. Browser action pre/post state recording
3. Detailed element information logging (tags, attributes, positions, etc.)
4. Action execution time and page change information recording
5. JSON format log file generation

## Log Files

The following log files are generated during execution:

1. `logs/automation_log.log`: Text log of all browser actions
2. `logs/automation_log.json`: Structured log in JSON format

## Log Summary Features

When execution is complete, a log summary is displayed in the console:

1. Execution time for each action
2. Element information (tags, indices, attributes)
3. Page change information
4. Action execution time

## Debugging Features

This example includes additional features for debugging:

1. Action parameter logging before execution
2. Element index and text information output
3. Detailed element information collection and recording

## PlaywrightLogger Class

PlaywrightLogger is a core logging component of the Browser Use library that records all actions and state changes during browser automation.

### Key Features

1. Pre/post action state logging (`log_action_before_execute`, `log_action_after_execute`)
2. Element information collection and storage (`store_element_info`)
3. Structured JSON log generation
4. Text-based log file creation

### Usage Locations

PlaywrightLogger is initialized and used in the following locations:

1. **Controller Class**: Initialized in the `__init__` method and called in the `act` method before and after action execution.

   ```python
   self.logger = PlaywrightLogger(log_dir=log_dir)
   ```

2. **Agent Class**: Used indirectly through the Controller. Whenever the Agent executes a browser action, the Controller's `act` method is called, which uses PlaywrightLogger.
3. **Example Scripts**: In example scripts like `google_search.py`, the log directory is set and the singleton instance of PlaywrightLogger is initialized.

   ```python
   import browser_use.playwright_logger
   browser_use.playwright_logger._instance = None
   ```

### Logging Flow

1. Before action execution: The `log_action_before_execute` method is called to log action type, element index, selector, etc.
2. Action execution: The Controller executes the action.
3. After action execution: The `log_action_after_execute` method is called to log action results, errors, page changes, etc.

## Notes

- Log files are stored in the `my_examples/logs/` directory.
- By default, the log directory is the `logs` folder in the script execution directory.
- You can change the log directory by setting the `PLAYWRIGHT_LOG_DIR` environment variable.
- To visually check the browser, add `PLAYWRIGHT_HEADLESS=false` to your `.env` file.
