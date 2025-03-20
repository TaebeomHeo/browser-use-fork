import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from browser_use.browser.context import BrowserContext  # BrowserContext 클래스 임포트
from browser_use.dom.views import DOMElementNode  # DOMElementNode 클래스 임포트

# 로거 설정
logger = logging.getLogger("playwright_automation")
logger.setLevel(logging.INFO)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(console_handler)

# 기본 로그 디렉토리 설정
DEFAULT_LOG_DIR = os.environ.get("PLAYWRIGHT_LOG_DIR", os.path.expanduser("~/playwright_logs"))
# 결과 텍스트 최대 출력 길이 설정 (기본값: 200자)
MAX_RESULT_LENGTH = int(os.environ.get("PLAYWRIGHT_MAX_RESULT_LENGTH", "200"))


class PlaywrightLogger:
    """
    Playwright 자동화 코드 생성을 위한 로깅 클래스
    """

    def __init__(self, log_dir: Optional[str] = None, session_id: Optional[str] = None, browser_context: Optional[BrowserContext] = None):
        """
        로거 초기화
        
        Args:
            log_dir: 로그 파일을 저장할 디렉토리 경로
            session_id: 사용하지 않음 (호환성을 위해 유지)
            browser_context: BrowserContext 인스턴스
        """
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.session_id = "current"  # 항상 "current"를 사용
        self.browser_context = browser_context  # BrowserContext 인스턴스 저장
        
        # 로그 디렉토리 생성
        try:
            self.session_dir = self.log_dir  # session_dir을 log_dir과 동일하게 설정
            os.makedirs(self.session_dir, exist_ok=True)
            
            # 로그 디렉토리 전체 경로 출력
            abs_log_dir = os.path.abspath(self.session_dir)
            logger.info(f"Log directory created/verified: {abs_log_dir}")
            print(f"\n===> Log directory: {abs_log_dir}")
        except Exception as e:
            logger.error(f"Failed to create log directory: {str(e)}")
            print(f"\n===> ERROR: Failed to create log directory: {str(e)}")
            # 기본 디렉토리로 폴백
            self.session_dir = os.path.expanduser("~/playwright_logs")
            os.makedirs(self.session_dir, exist_ok=True)
            print(f"\n===> Using fallback log directory: {os.path.abspath(self.session_dir)}")
        
        # 로그 파일 경로 - 통합 로그 파일 사용
        self.log_file = os.path.join(self.session_dir, "automation_log.log")
        self.json_log_file = os.path.join(self.session_dir, "automation_log.json")
        
        # 로그 파일 전체 경로 출력
        abs_log_file = os.path.abspath(self.log_file)
        abs_json_log_file = os.path.abspath(self.json_log_file)
        print(f"\n===> Log files will be saved to:")
        print(f"     Text log: {abs_log_file}")
        print(f"     JSON log: {abs_json_log_file}\n")
        
        # 현재 시간을 포함한 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 기존 로그 파일 백업
        try:
            self._backup_existing_logs(timestamp)
        except Exception as e:
            logger.error(f"Error during log file backup: {str(e)}")
            print(f"===> ERROR: Could not backup existing log files: {str(e)}")
        
        # 새 로그 파일 초기화
        try:
            self._initialize_log_files()
        except Exception as e:
            logger.error(f"Error initializing log files: {str(e)}")
            print(f"===> ERROR: Could not initialize log files: {str(e)}")
        
        # 액션 로그 초기화
        self.actions = []
        
        # 초기화 완료 메시지
        print(f"===> PlaywrightLogger initialized successfully")
    
    def _backup_existing_logs(self, timestamp: str) -> None:
        """
        기존 로그 파일을 백업합니다.
        
        Args:
            timestamp: 백업 파일에 포함할 타임스탬프
        """
        # 텍스트 로그 파일 백업
        if os.path.exists(self.log_file):
            try:
                backup_log_path = os.path.join(self.session_dir, f"automation_log_{timestamp}.log")
                shutil.copy2(self.log_file, backup_log_path)
                abs_backup_path = os.path.abspath(backup_log_path)
                logger.info(f"Backed up log file to: {abs_backup_path}")
                print(f"===> Backed up text log to: {abs_backup_path}")
            except Exception as e:
                logger.warning(f"Failed to backup log file: {str(e)}")
                print(f"===> WARNING: Failed to backup text log: {str(e)}")
        
        # JSON 로그 파일 백업
        if os.path.exists(self.json_log_file):
            try:
                backup_json_path = os.path.join(self.session_dir, f"automation_log_{timestamp}.json")
                shutil.copy2(self.json_log_file, backup_json_path)
                abs_backup_json_path = os.path.abspath(backup_json_path)
                logger.info(f"Backed up JSON log file to: {abs_backup_json_path}")
                print(f"===> Backed up JSON log to: {abs_backup_json_path}")
            except Exception as e:
                logger.warning(f"Failed to backup JSON log file: {str(e)}")
                print(f"===> WARNING: Failed to backup JSON log: {str(e)}")
    
    def _initialize_log_files(self) -> None:
        """
        로그 파일을 초기화합니다. 기존 파일이 있다면 내용을 지우고 새로 시작합니다.
        """
        # 텍스트 로그 파일 초기화
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                start_time = datetime.now().isoformat()
                f.write(f"=== Playwright Automation Log - Started at {start_time} ===\n")
                f.write(f"로그 디렉토리: {self.session_dir}\n\n")
            abs_log_file = os.path.abspath(self.log_file)
            logger.info(f"Initialized text log file: {abs_log_file}")
            print(f"===> Initialized new text log file at {start_time}")
        except Exception as e:
            logger.error(f"Failed to initialize text log file: {str(e)}")
            print(f"===> ERROR: Failed to initialize text log file: {str(e)}")
        
        # JSON 로그 파일 초기화 - 빈 actions 리스트로 시작
        try:
            initial_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "actions": [],
                "formatted_actions": []
            }
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            abs_json_log_file = os.path.abspath(self.json_log_file)
            logger.info(f"Initialized JSON log file: {abs_json_log_file}")
            print(f"===> Initialized new JSON log file")
        except Exception as e:
            logger.error(f"Failed to initialize JSON log file: {str(e)}")
            print(f"===> ERROR: Failed to initialize JSON log file: {str(e)}")
    
    async def store_element_info(self, element_index: int) -> Optional[Dict[str, Any]]:
        """
        특정 인덱스의 DOM 요소에 대한 상세 정보를 수집하고 저장합니다.
        
        Args:
            element_index: 요소의 인덱스
            
        Returns:
            요소 정보를 담은 딕셔너리 또는 None (요소를 찾지 못한 경우)
        """
        if not self.browser_context:
            logger.warning("BrowserContext not available, cannot store element info")
            return None
        
        try:
            # 현재 세션 및 상태 가져오기
            session = await self.browser_context.get_session()
            state = session.cached_state
            
            # 요소 맵에서 해당 인덱스의 요소 찾기
            if element_index not in state.selector_map:
                logger.warning(f"Element with index {element_index} not found in selector map")
                return None
            
            element_node = state.selector_map[element_index]
            
            # 요소 정보 수집
            element_info = {
                "index": element_index,
                "tag_name": element_node.tag_name,
                "xpath": element_node.xpath,
                "is_visible": element_node.is_visible,
                "is_interactive": element_node.is_interactive,
                "is_top_element": element_node.is_top_element,
                "attributes": element_node.attributes,
                "text_content": element_node.get_text_content(),
                "timestamp": datetime.now().isoformat()
            }
            
            # 중요 속성 추출
            for attr in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'placeholder', 'aria-label', 'role', 'title', 'alt', 'data-testid']:
                if attr in element_node.attributes:
                    element_info[attr] = element_node.attributes[attr]
            
            # 요소의 CSS 선택자 생성 시도
            try:
                css_selector = self._generate_css_selector(element_node)
                if css_selector:
                    element_info["css_selector"] = css_selector
            except Exception as e:
                logger.debug(f"Failed to generate CSS selector: {str(e)}")
            
            # 요소의 텍스트 콘텐츠 추출
            try:
                element_info["inner_text"] = element_node.get_all_text()
            except Exception as e:
                logger.debug(f"Failed to get inner text: {str(e)}")
            
            # 부모 요소 존재 여부 확인
            try:
                element_info["has_parent"] = element_node.parent is not None
            except Exception as e:
                logger.debug(f"Failed to check parent: {str(e)}")
            
            # 자식 요소 정보 추출
            try:
                child_count = 0
                child_tags = []
                
                for child in element_node.children:
                    # 안전하게 자식 요소가 DOMElementNode인지 확인
                    if isinstance(child, DOMElementNode):
                        child_count += 1
                        child_tags.append(child.tag_name)
                
                if child_count > 0:
                    element_info["children_count"] = child_count
                    element_info["children_tags"] = child_tags
            except Exception as e:
                logger.debug(f"Failed to get children info: {str(e)}")
            
            return element_info
            
        except Exception as e:
            logger.error(f"Error storing element info: {str(e)}")
            return None
    
    def _generate_css_selector(self, element_node) -> Optional[str]:
        """
        DOM 요소에 대한 CSS 선택자를 생성합니다.
        
        Args:
            element_node: DOM 요소 노드
            
        Returns:
            CSS 선택자 문자열 또는 None
        """
        try:
            # ID가 있으면 ID 선택자 사용
            if 'id' in element_node.attributes and element_node.attributes['id']:
                return f"#{element_node.attributes['id']}"
            
            # 클래스가 있으면 태그와 클래스 조합 사용
            if 'class' in element_node.attributes and element_node.attributes['class']:
                classes = element_node.attributes['class'].split()
                if classes:
                    return f"{element_node.tag_name}.{classes[0]}"
            
            # name 속성이 있으면 사용
            if 'name' in element_node.attributes and element_node.attributes['name']:
                return f"{element_node.tag_name}[name='{element_node.attributes['name']}']"
            
            # data-testid 속성이 있으면 사용
            if 'data-testid' in element_node.attributes and element_node.attributes['data-testid']:
                return f"{element_node.tag_name}[data-testid='{element_node.attributes['data-testid']}']"
            
            # aria-label 속성이 있으면 사용
            if 'aria-label' in element_node.attributes and element_node.attributes['aria-label']:
                return f"{element_node.tag_name}[aria-label='{element_node.attributes['aria-label']}']"
            
            # 기본적으로 XPath 반환
            return None
        except Exception as e:
            logger.debug(f"Error generating CSS selector: {str(e)}")
            return None

    async def log_action_before_execute(self, 
                                      action_type: str, 
                                      element_index: Optional[int] = None,
                                      selector: Optional[str] = None,
                                      xpath: Optional[str] = None,
                                      text: Optional[str] = None,
                                      url: Optional[str] = None):
        """
        액션 실행 전에 호출되어 element 상태를 로깅하는 함수
        
        Args:
            action_type: 액션 유형 (예: click_element, input_text)
            element_index: 요소 인덱스 (있는 경우)
            selector: CSS 선택자 (있는 경우)
            xpath: XPath (있는 경우)
            text: 텍스트 내용 (있는 경우)
            url: URL (있는 경우)
            
        Returns:
            요소 정보 딕셔너리 (나중에 비교를 위해)
        """
        timestamp = datetime.now().isoformat()
        logger.debug(f"[log_action_before_execute] Action: {action_type}, Index: {element_index}")
        
        # 콘솔에 중요 정보 출력
        print(f"\n===> PRE-ACTION: {action_type}")
        if element_index is not None:
            print(f"     Element Index: {element_index}")
        if text:
            print(f"     Text: {text}")
        if url:
            print(f"     URL: {url}")
        
        # 현재 페이지 URL 가져오기
        current_url = None
        if self.browser_context:
            try:
                page = await self.browser_context.get_current_page()
                current_url = page.url
                print(f"     Current URL: {current_url}")
            except Exception as e:
                logger.debug(f"Failed to get current URL: {str(e)}")
        
        # 실행 전 element 정보 수집
        element_info = None
        if element_index is not None:
            try:
                element_info = await self.store_element_info(element_index)
                if element_info:
                    print(f"     Element Tag: {element_info.get('tag_name', 'unknown')}")
                    if 'text_content' in element_info and element_info['text_content']:
                        text_preview = element_info['text_content']
                        if len(text_preview) > 50:
                            text_preview = text_preview[:47] + "..."
                        print(f"     Content: {text_preview}")
            except Exception as e:
                logger.error(f"Error storing element info: {str(e)}")
                print(f"     ERROR: Could not get element info: {str(e)}")
        
        # 통합 로그 파일에 기록 - 예외 처리 추가
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== PRE-ACTION: {action_type} - {timestamp} ===\n")
                if current_url:
                    f.write(f"Current URL: {current_url}\n")
                if element_index is not None:
                    f.write(f"Element Index: {element_index}\n")
                if selector:
                    f.write(f"CSS Selector: {selector}\n")
                if xpath:
                    f.write(f"XPath: {xpath}\n")
                if text:
                    f.write(f"Text: {text}\n")
                if url:
                    f.write(f"URL: {url}\n")
                
                # 요소 정보가 있으면 상세 정보 기록 (한 번만 기록)
                if element_info:
                    f.write(f"\n=== ELEMENT DETAILS: {action_type} - {timestamp} ===\n")
                    f.write(f"Element Index: {element_index}\n")
                    f.write(f"Tag: {element_info.get('tag_name', 'unknown')}\n")
                    
                    # 텍스트 콘텐츠 (있는 경우)
                    if "text_content" in element_info and element_info["text_content"]:
                        text_content = element_info["text_content"]
                        if len(text_content) > 200:
                            text_content = text_content[:197] + "..."
                        f.write(f"Text Content: {text_content}\n")
                    
                    # 가시성 및 상호작용 정보
                    f.write(f"Is Visible: {element_info.get('is_visible', False)}\n")
                    f.write(f"Is Enabled: {element_info.get('is_interactive', False)}\n")
                    
                    # 중요 속성 정보
                    if "attributes" in element_info:
                        f.write("Attributes:\n")
                        important_attrs = ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'aria-label', 'role', 'title']
                        for attr in important_attrs:
                            if attr in element_info["attributes"]:
                                f.write(f"  {attr}: {element_info['attributes'][attr]}\n")
                    
                    # 위치 및 크기 정보 (있는 경우)
                    if "position" in element_info and "size" in element_info:
                        pos = element_info["position"]
                        size = element_info["size"]
                        f.write(f"Position: x={pos['x']}, y={pos['y']}\n")
                        f.write(f"Size: width={size['width']}, height={size['height']}\n")
                    
                    # XPath 및 CSS 선택자
                    f.write(f"XPath: {element_info.get('xpath', '')}\n")
                    if "css_selector" in element_info:
                        f.write(f"CSS Selector: {element_info['css_selector']}\n")
                    
                    # 부모 요소 정보
                    if "has_parent" in element_info and element_info["has_parent"]:
                        f.write("Parent Element:\n")
                        f.write(f"  tag_name: {element_info.get('parent_tag_name', 'unknown')}\n")
                        f.write(f"  id: {element_info.get('parent_id', 'None')}\n")
                        f.write(f"  class_name: {element_info.get('parent_class', 'None')}\n")
                        f.write(f"  has_parent: {element_info['has_parent']}\n")
                    
                    # 자식 요소 정보
                    if "children_count" in element_info:
                        f.write(f"Children Count: {element_info['children_count']}\n")
                        if "children_tags" in element_info:
                            f.write(f"Children Tags: {', '.join(element_info['children_tags'])}\n")
                    
                    f.write("-" * 80 + "\n")
                else:
                    f.write("-" * 80 + "\n")
            
            logger.debug(f"Successfully wrote pre-action log for {action_type}")
        except Exception as e:
            logger.error(f"Error writing pre-action log: {str(e)}")
            print(f"     ERROR: Failed to write to log file: {str(e)}")
        
        # JSON 로그를 위한 정보 구성
        pre_action_info = {
            "timestamp": timestamp,
            "action_type": action_type,
            "phase": "pre-action",
            "element_index": element_index,
            "selector": selector,
            "xpath": xpath,
            "text": text,
            "url": url,
            "current_url": current_url,
            "element_info": element_info
        }
        
        # JSON 로그에 pre-action 정보 추가
        try:
            self.actions.append(pre_action_info)
            self._save_json()
            logger.debug(f"Successfully saved pre-action JSON for {action_type}")
        except Exception as e:
            logger.error(f"Error saving pre-action JSON: {str(e)}")
            print(f"     ERROR: Failed to save JSON log: {str(e)}")
        
        return element_info  # 나중에 비교를 위해 반환

    async def log_action_after_execute(self,
                                     action_type: str,
                                     pre_action_element_info: Optional[Dict] = None,
                                     element_index: Optional[int] = None,
                                     selector: Optional[str] = None,
                                     xpath: Optional[str] = None,
                                     text: Optional[str] = None,
                                     url: Optional[str] = None,
                                     result: Optional[str] = None,
                                     error: Optional[str] = None,
                                     additional_data: Optional[Dict[str, Any]] = None):
        """
        액션 실행 후에 호출되어 결과와 변경된 상태를 로깅하는 함수
        
        Args:
            action_type: 액션 유형
            pre_action_element_info: 액션 실행 전 요소 정보
            element_index: 요소 인덱스 (있는 경우)
            selector: CSS 선택자 (있는 경우)
            xpath: XPath (있는 경우)
            text: 텍스트 내용 (있는 경우)
            url: URL (있는 경우)
            result: 액션 실행 결과
            error: 오류 메시지 (있는 경우)
            additional_data: 추가 데이터 (있는 경우)
        """
        timestamp = datetime.now().isoformat()
        logger.debug(f"[log_action_after_execute] Action: {action_type}, Index: {element_index}")
        
        # 콘솔에 중요 정보 출력
        status = "ERROR" if error else "SUCCESS"
        print(f"\n===> POST-ACTION: {action_type} - {status}")
        if element_index is not None:
            tag = pre_action_element_info.get('tag_name', '') if pre_action_element_info else ''
            print(f"     Element: {tag} (index: {element_index})")
        if text:
            print(f"     Text: {text}")
        if result:
            # 결과가 너무 길면 잘라서 출력
            if len(result) > MAX_RESULT_LENGTH:
                truncated_result = result[:MAX_RESULT_LENGTH] + "... (중략됨, 전체 길이: " + str(len(result)) + "자)"
                print(f"     Result: {truncated_result}")
            else:
                print(f"     Result: {result}")
        if error:
            print(f"     Error: {error}")
        
        # 현재 페이지 URL 가져오기
        current_url = None
        if self.browser_context:
            try:
                page = await self.browser_context.get_current_page()
                current_url = page.url
                print(f"     Current URL: {current_url}")
            except Exception as e:
                logger.debug(f"Failed to get current URL: {str(e)}")
        
        # 액션 실행 후 요소 정보 수집 (가능한 경우)
        post_action_element_info = None
        if element_index is not None:
            try:
                post_action_element_info = await self.store_element_info(element_index)
            except Exception as e:
                logger.debug(f"Failed to get post-action element info: {str(e)}")
        
        # 요소 변경 사항 확인
        changes = {}
        if pre_action_element_info and post_action_element_info:
            # 텍스트 내용 변경 확인
            if pre_action_element_info.get('text_content') != post_action_element_info.get('text_content'):
                changes['text_content'] = {
                    'before': pre_action_element_info.get('text_content'),
                    'after': post_action_element_info.get('text_content')
                }
            
            # 가시성 변경 확인
            if pre_action_element_info.get('is_visible') != post_action_element_info.get('is_visible'):
                changes['is_visible'] = {
                    'before': pre_action_element_info.get('is_visible'),
                    'after': post_action_element_info.get('is_visible')
                }
            
            # 활성화 상태 변경 확인
            if pre_action_element_info.get('is_interactive') != post_action_element_info.get('is_interactive'):
                changes['is_enabled'] = {
                    'before': pre_action_element_info.get('is_interactive'),
                    'after': post_action_element_info.get('is_interactive')
                }
            
            # 속성 변경 확인
            pre_attrs = pre_action_element_info.get('attributes', {})
            post_attrs = post_action_element_info.get('attributes', {})
            
            for key in set(list(pre_attrs.keys()) + list(post_attrs.keys())):
                if pre_attrs.get(key) != post_attrs.get(key):
                    if 'attributes' not in changes:
                        changes['attributes'] = {}
                    changes['attributes'][key] = {
                        'before': pre_attrs.get(key),
                        'after': post_attrs.get(key)
                    }
        
        # 변경 사항이 있으면 콘솔에 출력
        if changes:
            print(f"     Changes detected in element properties")
            for key, value in changes.items():
                if key == 'attributes':
                    for attr_key, attr_value in value.items():
                        print(f"       {attr_key}: {attr_value['before']} -> {attr_value['after']}")
                else:
                    print(f"       {key}: {value['before']} -> {value['after']}")
        
        # 통합 로그 파일에 기록 (POST-ACTION) - 예외 처리 추가
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== POST-ACTION: {action_type} - {timestamp} ===\n")
                if current_url:
                    f.write(f"Current URL: {current_url}\n")
                if element_index is not None:
                    f.write(f"Element Index: {element_index}\n")
                if selector:
                    f.write(f"CSS Selector: {selector}\n")
                if xpath:
                    f.write(f"XPath: {xpath}\n")
                if text:
                    f.write(f"Text: {text}\n")
                if url:
                    f.write(f"URL: {url}\n")
                
                # 결과 또는 오류 기록
                if result:
                    # 결과가 너무 길면 잘라서 기록
                    if len(result) > MAX_RESULT_LENGTH:
                        truncated_result = result[:MAX_RESULT_LENGTH] + "... (중략됨)"
                        f.write(f"\nResult: {truncated_result}\n")
                    else:
                        f.write(f"\nResult: {result}\n")
                if error:
                    f.write(f"\nError: {error}\n")
                
                # 추가 데이터 기록 (간소화)
                if additional_data:
                    f.write("\n--- Additional Data ---\n")
                    for key, value in additional_data.items():
                        if key != "element_details" and key != "post_action_element_details":
                            f.write(f"{key}: {value}\n")
                
                # 요소 변경 사항 기록 (중요한 변경 사항만)
                if changes:
                    f.write("\n--- Element Changes ---\n")
                    for key, value in changes.items():
                        if key == 'attributes':
                            f.write("Attributes Changes:\n")
                            for attr_key, attr_value in value.items():
                                f.write(f"  {attr_key}: {attr_value['before']} -> {attr_value['after']}\n")
                        else:
                            f.write(f"{key}: {value['before']} -> {value['after']}\n")
                
                f.write("-" * 80 + "\n")
            
            logger.debug(f"Successfully wrote post-action detail log for {action_type}")
        except Exception as e:
            logger.error(f"Error writing post-action detail log: {str(e)}")
            print(f"     ERROR: Failed to write post-action log: {str(e)}")
        
        # 액션 실행 결과를 간결하게 로그 파일에 기록 - 예외 처리 추가
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                status = "ERROR" if error else "SUCCESS"
                f.write(f"{timestamp} - {action_type} - {status}\n")
                if element_index is not None:
                    tag = pre_action_element_info.get('tag_name', '') if pre_action_element_info else ''
                    f.write(f"  Element: {tag} (index: {element_index})\n")
                if text:
                    f.write(f"  Text: {text}\n")
                if url:
                    f.write(f"  URL: {url}\n")
                if current_url:
                    f.write(f"  Current URL: {current_url}\n")
                if result:
                    # 결과가 너무 길면 잘라서 기록
                    if len(result) > MAX_RESULT_LENGTH:
                        truncated_result = result[:MAX_RESULT_LENGTH] + "... (중략됨)"
                        f.write(f"  Result: {truncated_result}\n")
                    else:
                        f.write(f"  Result: {result}\n")
                if error:
                    f.write(f"  Error: {error}\n")
                
                # 변경 사항이 있으면 간략하게 기록
                if changes:
                    f.write("  Changes detected in element properties\n")
                
                f.write("\n")
            
            logger.debug(f"Successfully wrote post-action summary log for {action_type}")
        except Exception as e:
            logger.error(f"Error writing post-action summary log: {str(e)}")
            print(f"     ERROR: Failed to write post-action summary: {str(e)}")
        
        # 속성 정보 정리 및 보강
        formatted_attributes = {}
        if pre_action_element_info:
            # 중요 속성 먼저 정렬
            important_attrs = ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'tag_name', 'text_content']
            for attr in important_attrs:
                if attr in pre_action_element_info:
                    formatted_attributes[attr] = pre_action_element_info[attr]
            
            # 나머지 속성 추가
            for key, value in pre_action_element_info.items():
                if key not in formatted_attributes and key not in ['index', 'timestamp', 'attributes']:
                    formatted_attributes[key] = value
        
        # 변경 사항 감지 (액션 전후 요소 비교)
        changes = {}
        if pre_action_element_info and post_action_element_info:
            for key in pre_action_element_info:
                if key in post_action_element_info and pre_action_element_info[key] != post_action_element_info[key]:
                    changes[key] = {
                        "before": pre_action_element_info[key],
                        "after": post_action_element_info[key]
                    }
        
        action_data = {
            "timestamp": timestamp,
            "phase": "post_action",
            "action_type": action_type,
            "selector": selector,
            "xpath": xpath,
            "element_index": element_index,
            "text": text,
            "url": url,
            "current_url": current_url,
            "attributes": formatted_attributes,
            "result": result,
            "error": error,
            "changes": changes,
            "additional_data": additional_data or {}
        }
        
        # JSON 로그에 post-action 정보 추가 - 예외 처리 추가
        try:
            self.actions.append(action_data)
            self._save_json()
            logger.debug(f"Successfully saved post-action JSON for {action_type}")
        except Exception as e:
            logger.error(f"Error saving post-action JSON: {str(e)}")
            print(f"     ERROR: Failed to save post-action JSON: {str(e)}")
        
        return action_data
    
    def _save_json(self):
        """JSON 파일에 액션 로그 저장 - 예외 처리 추가"""
        try:
            # 각 액션에 타임스탬프 추가
            for action in self.actions:
                if "timestamp" not in action:
                    action["timestamp"] = datetime.now().isoformat()
            
            # 액션 데이터를 더 읽기 쉬운 형식으로 변환
            formatted_actions = []
            for action in self.actions:
                formatted_action = {
                    "timestamp": action.get("timestamp", ""),
                    "action_type": action.get("action_type", ""),
                    "phase": action.get("phase", ""),
                    "element_info": {}
                }
                
                # 요소 정보 추가
                if "element_index" in action and action["element_index"] is not None:
                    formatted_action["element_info"]["index"] = action["element_index"]
                
                if "selector" in action and action["selector"]:
                    formatted_action["element_info"]["selector"] = action["selector"]
                
                if "xpath" in action and action["xpath"]:
                    formatted_action["element_info"]["xpath"] = action["xpath"]
                
                # 요소 상세 정보 추가
                if "element_info" in action and action["element_info"]:
                    element_info = action["element_info"]
                    
                    # 기본 요소 정보
                    formatted_action["element_info"]["tag_name"] = element_info.get("tag_name", "")
                    formatted_action["element_info"]["is_visible"] = element_info.get("is_visible", False)
                    formatted_action["element_info"]["is_interactive"] = element_info.get("is_interactive", False)
                    
                    # CSS 선택자 정보
                    if "css_selector" in element_info:
                        formatted_action["element_info"]["css_selector"] = element_info["css_selector"]
                    
                    # 중요 속성 정보
                    attributes = {}
                    for attr in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'placeholder', 'aria-label', 'role', 'title', 'alt', 'data-testid']:
                        if attr in element_info:
                            attributes[attr] = element_info[attr]
                    
                    if attributes:
                        formatted_action["element_info"]["attributes"] = attributes
                    
                    # 텍스트 콘텐츠
                    if "text_content" in element_info:
                        formatted_action["element_info"]["text_content"] = element_info["text_content"]
                    
                    if "inner_text" in element_info:
                        formatted_action["element_info"]["inner_text"] = element_info["inner_text"]
                    
                    # 부모 요소 정보
                    if "has_parent" in element_info:
                        formatted_action["element_info"]["has_parent"] = element_info["has_parent"]
                    
                    # 자식 요소 정보
                    if "children_count" in element_info:
                        formatted_action["element_info"]["children_count"] = element_info["children_count"]
                        if "children_tags" in element_info:
                            formatted_action["element_info"]["children_tags"] = element_info["children_tags"]
                
                # 텍스트 및 URL 정보 추가
                if "text" in action and action["text"]:
                    formatted_action["text"] = action["text"]
                
                if "url" in action and action["url"]:
                    formatted_action["url"] = action["url"]
                
                if "current_url" in action and action["current_url"]:
                    formatted_action["current_url"] = action["current_url"]
                
                # 결과 및 오류 정보 추가
                if "result" in action and action["result"]:
                    # 포맷팅된 결과에는 길이 제한 적용
                    result = action["result"]
                    if len(result) > MAX_RESULT_LENGTH:
                        formatted_action["result"] = result[:MAX_RESULT_LENGTH] + "... (중략됨)"
                        formatted_action["result_truncated"] = True
                        formatted_action["result_full_length"] = len(result)
                    else:
                        formatted_action["result"] = result
                
                if "error" in action and action["error"]:
                    formatted_action["error"] = action["error"]
                
                # 변경 사항 정보 추가
                if "changes" in action and action["changes"]:
                    formatted_action["changes"] = action["changes"]
                
                # 추가 데이터 정보 추가
                if "additional_data" in action and action["additional_data"]:
                    formatted_action["additional_data"] = action["additional_data"]
                
                formatted_actions.append(formatted_action)
            
            # 원본 액션 데이터와 포맷팅된 액션 데이터 모두 저장
            output_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "actions": self.actions,
                "formatted_actions": formatted_actions
            }
            
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Successfully saved JSON log with {len(self.actions)} actions")
        except Exception as e:
            logger.error(f"Error saving JSON log: {str(e)}")
            print(f"     ERROR: Failed to save JSON log: {str(e)}")

    def generate_playwright_code(self, output_file: Optional[str] = None) -> str:
        """
        로그 파일 경로 반환 (JavaScript 코드 생성 기능은 삭제)
        
        Args:
            output_file: 사용하지 않음 (호환성을 위해 유지)
            
        Returns:
            로그 파일 경로
        """
        return f"로그 파일: {self.log_file}, JSON 파일: {self.json_log_file}"

    async def _get_basic_attributes(self, element_handle) -> Dict[str, Any]:
        """기본 element 속성 수집"""
        attrs = {}
        try:
            attrs['tag'] = await element_handle.evaluate("el => el.tagName.toLowerCase()")
            attrs['text'] = await element_handle.text_content()
            
            # 기본 속성들 수집
            for attr in ['id', 'class', 'name', 'href', 'value']:
                val = await element_handle.get_attribute(attr)
                if val:
                    attrs[attr] = val
        except Exception as e:
            logger.error(f"기본 속성 수집 중 에러: {e}")
        return attrs

    async def _get_element_geometry(self, element_handle) -> Dict[str, Any]:
        """element의 위치와 크기 정보 수집"""
        geometry = {}
        try:
            bbox = await element_handle.bounding_box()
            if bbox:
                geometry['position'] = {'x': bbox['x'], 'y': bbox['y']}
                geometry['size'] = {'width': bbox['width'], 'height': bbox['height']}
        except Exception as e:
            logger.error(f"위치 정보 수집 중 에러: {e}")
        return geometry

    async def _get_visibility_info(self, element_handle) -> Dict[str, Any]:
        """element의 가시성 정보 수집"""
        visibility = {}
        try:
            visibility['visible'] = await element_handle.is_visible()
            visibility['enabled'] = await element_handle.is_enabled()
        except Exception as e:
            logger.error(f"가시성 정보 수집 중 에러: {e}")
        return visibility

    async def _collect_element_details(self, element_handle) -> Dict[str, Any]:
        """element의 상세 정보 수집"""
        details = {}
        try:
            details.update(await self._get_basic_attributes(element_handle))
            details.update(await self._get_element_geometry(element_handle))
            details.update(await self._get_visibility_info(element_handle))
        except Exception as e:
            logger.error(f"Element 정보 수집 중 에러: {e}")
        return details


# 싱글톤 인스턴스
_instance = None

def get_playwright_logger(log_dir: Optional[str] = None, session_id: Optional[str] = None) -> PlaywrightLogger:
    """
    PlaywrightLogger의 싱글톤 인스턴스 반환
    
    Args:
        log_dir: 로그 디렉토리 경로
        session_id: 사용하지 않음 (호환성을 위해 유지)
        
    Returns:
        PlaywrightLogger 인스턴스
    """
    global _instance
    
    # log_dir이 제공되었거나 인스턴스가 없으면 새 인스턴스 생성
    if _instance is None or (log_dir is not None and log_dir != _instance.log_dir):
        _instance = PlaywrightLogger(log_dir)
        
    return _instance 