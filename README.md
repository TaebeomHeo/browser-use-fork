<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./static/browser-use-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="./static/browser-use.png">
  <img alt="Shows a black Browser Use Logo in light color mode and a white one in dark color mode." src="./static/browser-use.png"  width="full">
</picture>

<h1 align="center">Enable AI to control your browser 🤖</h1>

[![GitHub stars](https://img.shields.io/github/stars/gregpr07/browser-use?style=social)](https://github.com/gregpr07/browser-use/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![Cloud](https://img.shields.io/badge/Cloud-☁️-blue)](https://cloud.browser-use.com)
[![Twitter Follow](https://img.shields.io/twitter/follow/Gregor?style=social)](https://x.com/gregpr07)
[![Twitter Follow](https://img.shields.io/twitter/follow/Magnus?style=social)](https://x.com/mamagnus00)

🌐 Browser-use is the easiest way to connect your AI agents with the browser.

💡 See what others are building and share your projects in our [Discord](https://link.browser-use.com/discord) - we'd love to see what you create!

🌩️ Skip the setup - try our hosted version for instant browser automation! [Try it now](https://cloud.browser-use.com).

# Quick start

With pip:

```bash
pip install browser-use
```

install playwright:

```bash
playwright install
```

Spin up your agent:

```python
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
load_dotenv()

async def main():
    agent = Agent(
        task="Go to Reddit, search for 'browser-use', click on the first post and return the first comment.",
        llm=ChatOpenAI(model="gpt-4o"),
    )
    result = await agent.run()
    print(result)

asyncio.run(main())
```

Add your API keys for the provider you want to use to your `.env` file.

```bash
OPENAI_API_KEY=
```

For other settings, models, and more, check out the [documentation 📕](https://docs.browser-use.com).

### Test with UI

You can test [browser-use with a UI repository](https://github.com/browser-use/web-ui)

Or simply run the gradio example:

```
uv pip install gradio
```

```bash
python examples/ui/gradio_demo.py
```

# Demos

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/browser/real_browser.py): Write a letter in Google Docs to my Papa, thanking him for everything, and save the document as a PDF.

![Letter to Papa](https://github.com/user-attachments/assets/242ade3e-15bc-41c2-988f-cbc5415a66aa)

`<br/><br/>`

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/use-cases/find_and_apply_to_jobs.py): Read my CV & find ML jobs, save them to a file, and then start applying for them in new tabs, if you need help, ask me.'

https://github.com/user-attachments/assets/171fb4d6-0355-46f2-863e-edb04a828d04

`<br/><br/>`

Prompt: Find flights on kayak.com from Zurich to Beijing from 25.12.2024 to 02.02.2025.

![flight search 8x 10fps](https://github.com/user-attachments/assets/ea605d4a-90e6-481e-a569-f0e0db7e6390)

`<br/><br/>`

[Prompt](https://github.com/browser-use/browser-use/blob/main/examples/custom-functions/save_to_file_hugging_face.py): Look up models with a license of cc-by-sa-4.0 and sort by most likes on Hugging face, save top 5 to file.

https://github.com/user-attachments/assets/de73ee39-432c-4b97-b4e8-939fd7f323b3

## More examples

For more examples see the [examples](examples) folder or join the [Discord](https://link.browser-use.com/discord) and show off your project.

# Vision

Tell your computer what to do, and it gets it done.

## Roadmap

- [ ] Improve memory management
- [ ] Enhance planning capabilities
- [ ] Improve self-correction
- [ ] Fine-tune the model for better performance
- [ ] Create datasets for complex tasks
- [ ] Sandbox browser-use for specific websites
- [ ] Implement deterministic script rerun with LLM fallback
- [ ] Cloud-hosted version
- [ ] Add stop/pause functionality
- [ ] Improve authentication handling
- [ ] Reduce token consumption
- [ ] Implement long-term memory
- [ ] Handle repetitive tasks reliably
- [ ] Third-party integrations (Slack, etc.)
- [ ] Include more interactive elements
- [ ] Human-in-the-loop execution
- [ ] Benchmark various models against each other
- [ ] Let the user record a workflow and browser-use will execute it
- [ ] Improve the generated GIF quality
- [ ] Create various demos for tutorial execution, job application, QA testing, social media, etc.

## Contributing

We love contributions! Feel free to open issues for bugs or feature requests. To contribute to the docs, check out the `/docs` folder.

## Local Setup

To learn more about the library, check out the [local setup 📕](https://docs.browser-use.com/development/local-setup).

## Cooperations

We are forming a commission to define best practices for UI/UX design for browser agents.
Together, we're exploring how software redesign improves the performance of AI agents and gives these companies a competitive advantage by designing their existing software to be at the forefront of the agent age.

Email [Toby](mailto:tbiddle@loop11.com?subject=I%20want%20to%20join%20the%20UI/UX%20commission%20for%20AI%20agents&body=Hi%20Toby%2C%0A%0AI%20found%20you%20in%20the%20browser-use%20GitHub%20README.%0A%0A) to apply for a seat on the committee.

## Citation

If you use Browser Use in your research or project, please cite:

```bibtex
@software{browser_use2024,
  author = {Müller, Magnus and Žunič, Gregor},
  title = {Browser Use: Enable AI to control your browser},
  year = {2024},
  publisher = {GitHub},
  url = {https://github.com/browser-use/browser-use}
}
```

---

<div align="center">
  Made with ❤️ in Zurich and San Francisco
</div>

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

---

자세한 사용법이나 커스터마이징이 필요하면 언제든 문의하세요!
