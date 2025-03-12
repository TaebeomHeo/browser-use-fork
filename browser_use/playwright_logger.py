import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from browser_use.browser.context import BrowserContext  # BrowserContext 클래스 임포트
from browser_use.dom.views import DOMElementNode  # DOMElementNode 클래스 임포트

# 로거 설정
logger = logging.getLogger("playwright_automation")
logger.setLevel(logging.INFO)

# 기본 로그 디렉토리 설정
DEFAULT_LOG_DIR = os.environ.get("PLAYWRIGHT_LOG_DIR", os.path.expanduser("~/playwright_logs"))


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
        self.session_dir = self.log_dir  # session_dir을 log_dir과 동일하게 설정
        os.makedirs(self.session_dir, exist_ok=True)
        
        # 로그 파일 경로
        self.log_file = os.path.join(self.session_dir, "playwright_actions.log")
        self.json_log_file = os.path.join(self.session_dir, "playwright_actions.json")
        self.detailed_log_file = os.path.join(self.session_dir, "detailed_actions.log")
        self.element_details_log_file = os.path.join(self.session_dir, "element_details.log")
        
        # 기존 로그 파일 삭제 (덮어쓰기 모드)
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(self.json_log_file):
            os.remove(self.json_log_file)
        if os.path.exists(self.detailed_log_file):
            os.remove(self.detailed_log_file)
        if os.path.exists(self.element_details_log_file):
            os.remove(self.element_details_log_file)
        
        # 액션 로그 초기화
        self.actions = []
        
        # 로그 파일 헤더 작성
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"Playwright Automation Log - Session: {self.session_id}\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n")
            f.write("-" * 80 + "\n\n")
        
        with open(self.detailed_log_file, 'w', encoding='utf-8') as f:
            f.write(f"Detailed Playwright Automation Log - Session: {self.session_id}\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n")
            f.write("-" * 80 + "\n\n")
        
        with open(self.element_details_log_file, 'w', encoding='utf-8') as f:
            f.write(f"Element Details Log - Session: {self.session_id}\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n")
            f.write("-" * 80 + "\n\n")
        
        logger.info(f"PlaywrightLogger initialized. Logs will be saved to {self.session_dir}")
    
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
            
            # 요소 상세 정보를 로그 파일에 기록
            with open(self.element_details_log_file, 'a', encoding='utf-8') as f:
                f.write(f"=== Element Index: {element_index} - {datetime.now().isoformat()} ===\n")
                f.write(f"Tag: {element_info['tag_name']}\n")
                f.write(f"XPath: {element_info['xpath']}\n")
                
                if "css_selector" in element_info:
                    f.write(f"CSS Selector: {element_info['css_selector']}\n")
                
                f.write("Attributes:\n")
                for key, value in element_node.attributes.items():
                    f.write(f"  {key}: {value}\n")
                
                f.write(f"Visibility: {element_info['is_visible']}\n")
                f.write(f"Interactive: {element_info['is_interactive']}\n")
                
                if "text_content" in element_info and element_info["text_content"]:
                    text_content = element_info["text_content"]
                    if len(text_content) > 200:
                        text_content = text_content[:197] + "..."
                    f.write(f"Text Content: {text_content}\n")
                
                if "has_parent" in element_info:
                    f.write("Parent Element:\n")
                    f.write(f"  has_parent: {element_info['has_parent']}\n")
                
                if "children_count" in element_info:
                    f.write(f"Children Count: {element_info['children_count']}\n")
                    if "children_tags" in element_info:
                        f.write(f"Children Tags: {', '.join(element_info['children_tags'])}\n")
                
                f.write("-" * 80 + "\n\n")
            
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
        
        # 현재 페이지 URL 가져오기
        current_url = None
        if self.browser_context:
            try:
                page = await self.browser_context.get_current_page()
                current_url = page.url
            except Exception as e:
                logger.debug(f"Failed to get current URL: {str(e)}")
        
        # 실행 전 element 정보 수집
        element_info = None
        if element_index is not None:
            try:
                element_info = await self.store_element_info(element_index)
            except Exception as e:
                logger.error(f"Error storing element info: {str(e)}")
        
        # 로그 파일에 기록
        with open(self.detailed_log_file, 'a', encoding='utf-8') as f:
            f.write(f"=== PRE-ACTION: {action_type} - {timestamp} ===\n")
            if current_url:
                f.write(f"Current URL: {current_url}\n")
            if element_index is not None:
                f.write(f"Element Index: {element_index}\n")
                if element_info and "tag_name" in element_info:
                    f.write(f"Element Tag: {element_info['tag_name']}\n")
            if xpath:
                f.write(f"XPath: {xpath}\n")
            if selector:
                f.write(f"Selector: {selector}\n")
            if text:
                f.write(f"Text: {text}\n")
            if url:
                f.write(f"Target URL: {url}\n")
            
            # 요소 정보가 있으면 중요 속성 기록
            if element_info:
                f.write("Element Properties:\n")
                for key in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'placeholder', 'aria-label', 'role']:
                    if key in element_info:
                        f.write(f"  {key}: {element_info[key]}\n")
                
                if "text_content" in element_info and element_info["text_content"]:
                    text_content = element_info["text_content"]
                    if len(text_content) > 100:
                        text_content = text_content[:97] + "..."
                    f.write(f"  text_content: {text_content}\n")
            
            f.write("-" * 80 + "\n\n")
        
        pre_action_info = {
            "timestamp": timestamp,
            "phase": "pre_action",
            "action_type": action_type,
            "selector": selector,
            "xpath": xpath,
            "element_index": element_index,
            "text": text,
            "url": url,
            "current_url": current_url,
            "element_info": element_info or {}
        }
        
        # JSON 로그에 pre-action 정보 추가
        self.actions.append(pre_action_info)
        self._save_json()
        
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
        
        # 현재 페이지 URL 가져오기
        current_url = None
        if self.browser_context:
            try:
                page = await self.browser_context.get_current_page()
                current_url = page.url
            except Exception as e:
                logger.debug(f"Failed to get current URL: {str(e)}")
        
        # 액션 실행 후 요소 정보 수집 (가능한 경우)
        post_action_element_info = None
        if element_index is not None:
            try:
                post_action_element_info = await self.store_element_info(element_index)
            except Exception as e:
                logger.error(f"Error storing post-action element info: {str(e)}")
        
        # 로그 파일에 기록
        with open(self.detailed_log_file, 'a', encoding='utf-8') as f:
            f.write(f"=== POST-ACTION: {action_type} - {timestamp} ===\n")
            if current_url:
                f.write(f"Current URL: {current_url}\n")
            if element_index is not None:
                f.write(f"Element Index: {element_index}\n")
                if post_action_element_info and "tag_name" in post_action_element_info:
                    f.write(f"Element Tag: {post_action_element_info['tag_name']}\n")
            if xpath:
                f.write(f"XPath: {xpath}\n")
            if selector:
                f.write(f"Selector: {selector}\n")
            if text:
                f.write(f"Text: {text}\n")
            if url:
                f.write(f"Target URL: {url}\n")
            if result:
                f.write(f"Result: {result}\n")
            if error:
                f.write(f"Error: {error}\n")
            
            # 요소 정보가 있으면 중요 속성 기록
            if post_action_element_info:
                f.write("Element Properties After Action:\n")
                for key in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'placeholder', 'aria-label', 'role']:
                    if key in post_action_element_info:
                        f.write(f"  {key}: {post_action_element_info[key]}\n")
                
                if "text_content" in post_action_element_info and post_action_element_info["text_content"]:
                    text_content = post_action_element_info["text_content"]
                    if len(text_content) > 100:
                        text_content = text_content[:97] + "..."
                    f.write(f"  text_content: {text_content}\n")
            
            # 변경 사항 감지 및 기록
            if pre_action_element_info and post_action_element_info:
                changes = []
                for key in pre_action_element_info:
                    if key in post_action_element_info and pre_action_element_info[key] != post_action_element_info[key]:
                        changes.append((key, pre_action_element_info[key], post_action_element_info[key]))
                
                if changes:
                    f.write("Changes Detected:\n")
                    for key, before, after in changes:
                        # 텍스트가 너무 길면 잘라내기
                        if isinstance(before, str) and len(before) > 50:
                            before = before[:47] + "..."
                        if isinstance(after, str) and len(after) > 50:
                            after = after[:47] + "..."
                        
                        f.write(f"  {key}: {before} -> {after}\n")
            
            f.write("-" * 80 + "\n\n")
        
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
        
        # JSON 로그에 post-action 정보 추가
        self.actions.append(action_data)
        self._save_json()
        
        # 액션 실행 결과를 로그 파일에 기록
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
                f.write(f"  Result: {result}\n")
            if error:
                f.write(f"  Error: {error}\n")
            
            # 변경 사항이 있으면 간략하게 기록
            if changes:
                f.write("  Changes detected in element properties\n")
            
            f.write("\n")
        
        return action_data
    
    def _save_json(self):
        """JSON 파일에 액션 로그 저장"""
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
                formatted_action["result"] = action["result"]
            
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