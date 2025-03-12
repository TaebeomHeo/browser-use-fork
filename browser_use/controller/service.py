import asyncio
import json
import logging
from typing import Optional, Type
from datetime import datetime

from main_content_extractor import MainContentExtractor
from pydantic import BaseModel

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.registry.service import Registry
from browser_use.controller.views import (
	ClickElementAction,
	DoneAction,
	ExtractPageContentAction,
	GoToUrlAction,
	InputTextAction,
	NoParamsAction,
	OpenTabAction,
	ScrollAction,
	SearchGoogleAction,
	SendKeysAction,
	SwitchTabAction,
)
from browser_use.utils import time_execution_async, time_execution_sync
from browser_use.playwright_logger import PlaywrightLogger

logger = logging.getLogger(__name__)


class Controller:
	def __init__(
		self,
		exclude_actions: list[str] = [],
		output_model: Optional[Type[BaseModel]] = None,
		log_dir: Optional[str] = None,
	):
		self.exclude_actions = exclude_actions
		self.output_model = output_model
		self.registry = Registry(exclude_actions)
		self._register_default_actions()
		self.logger = PlaywrightLogger(log_dir=log_dir)

	def _register_default_actions(self):
		"""Register all default browser actions"""

		if self.output_model is not None:

			@self.registry.action('Complete task', param_model=self.output_model)
			async def done(params: BaseModel):
				return ActionResult(is_done=True, extracted_content=params.model_dump_json())
		else:

			@self.registry.action('Complete task', param_model=DoneAction)
			async def done(params: DoneAction):
				return ActionResult(is_done=True, extracted_content=params.text)

		# Basic Navigation Actions
		@self.registry.action(
			'Search Google in the current tab',
			param_model=SearchGoogleAction,
			requires_browser=True,
		)
		async def search_google(params: SearchGoogleAction, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.goto(f'https://www.google.com/search?q={params.query}&udm=14')
			await page.wait_for_load_state()
			msg = f'🔍  Searched for "{params.query}" in Google'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Navigate to URL in the current tab', param_model=GoToUrlAction, requires_browser=True)
		async def go_to_url(params: GoToUrlAction, browser: BrowserContext):
			page = await browser.get_current_page()
			await page.goto(params.url)
			await page.wait_for_load_state()
			msg = f'🔗  Navigated to {params.url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Go back', param_model=NoParamsAction, requires_browser=True)
		async def go_back(_: NoParamsAction, browser: BrowserContext):
			await browser.go_back()
			msg = '🔙  Navigated back'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Element Interaction Actions
		@self.registry.action('Click element', param_model=ClickElementAction, requires_browser=True)
		async def click_element(params: ClickElementAction, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if params.index not in state.selector_map:
				raise Exception(f'Element with index {params.index} does not exist - retry or use alternative actions')

			element_node = state.selector_map[params.index]
			initial_pages = len(session.context.pages)

			# if element has file uploader then dont click
			if await browser.is_file_uploader(element_node):
				msg = f'Index {params.index} - has an element which opens file upload dialog. To upload files please use a specific function to upload files '
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			msg = None

			try:
				await browser._click_element_node(element_node)
				msg = f'🖱️  Clicked button with index {params.index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}'

				logger.info(msg)
				logger.debug(f'Element xpath: {element_node.xpath}')
				if len(session.context.pages) > initial_pages:
					new_tab_msg = 'New tab opened - switching to it'
					msg += f' - {new_tab_msg}'
					logger.info(new_tab_msg)
					await browser.switch_to_tab(-1)
				return ActionResult(extracted_content=msg, include_in_memory=True)
			except Exception as e:
				logger.warning(f'Element not clickable with index {params.index} - most likely the page changed')
				return ActionResult(error=str(e))

		@self.registry.action(
			'Input text into a input interactive element',
			param_model=InputTextAction,
			requires_browser=True,
		)
		async def input_text(params: InputTextAction, browser: BrowserContext):
			session = await browser.get_session()
			state = session.cached_state

			if params.index not in state.selector_map:
				raise Exception(f'Element index {params.index} does not exist - retry or use alternative actions')

			element_node = state.selector_map[params.index]
			await browser._input_text_element_node(element_node, params.text)
			msg = f'⌨️  Input "{params.text}" into index {params.index}'
			logger.info(msg)
			logger.debug(f'Element xpath: {element_node.xpath}')
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Tab Management Actions
		@self.registry.action('Switch tab', param_model=SwitchTabAction, requires_browser=True)
		async def switch_tab(params: SwitchTabAction, browser: BrowserContext):
			await browser.switch_to_tab(params.page_id)
			# Wait for tab to be ready
			page = await browser.get_current_page()
			await page.wait_for_load_state()
			msg = f'🔄  Switched to tab {params.page_id}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action('Open url in new tab', param_model=OpenTabAction, requires_browser=True)
		async def open_tab(params: OpenTabAction, browser: BrowserContext):
			await browser.create_new_tab(params.url)
			msg = f'🔗  Opened new tab with {params.url}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		# Content Actions
		@self.registry.action(
			'Extract page content to get the pure text or markdown with links if include_links is set to true',
			param_model=ExtractPageContentAction,
			requires_browser=True,
		)
		async def extract_content(params: ExtractPageContentAction, browser: BrowserContext):
			page = await browser.get_current_page()
			output_format = 'markdown' if params.include_links else 'text'
			content = MainContentExtractor.extract(  # type: ignore
				html=await page.content(),
				output_format=output_format,
			)
			msg = f'📄  Extracted page as {output_format}\n: {content}\n'
			logger.info(msg)
			return ActionResult(extracted_content=msg)

		@self.registry.action(
			'Scroll down the page by pixel amount - if no amount is specified, scroll down one page',
			param_model=ScrollAction,
			requires_browser=True,
		)
		async def scroll_down(params: ScrollAction, browser: BrowserContext):
			page = await browser.get_current_page()
			if params.amount is not None:
				await page.evaluate(f'window.scrollBy(0, {params.amount});')
			else:
				await page.keyboard.press('PageDown')

			amount = f'{params.amount} pixels' if params.amount is not None else 'one page'
			msg = f'🔍  Scrolled down the page by {amount}'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# scroll up
		@self.registry.action(
			'Scroll up the page by pixel amount - if no amount is specified, scroll up one page',
			param_model=ScrollAction,
			requires_browser=True,
		)
		async def scroll_up(params: ScrollAction, browser: BrowserContext):
			page = await browser.get_current_page()
			if params.amount is not None:
				await page.evaluate(f'window.scrollBy(0, -{params.amount});')
			else:
				await page.keyboard.press('PageUp')

			amount = f'{params.amount} pixels' if params.amount is not None else 'one page'
			msg = f'🔍  Scrolled up the page by {amount}'
			logger.info(msg)
			return ActionResult(
				extracted_content=msg,
				include_in_memory=True,
			)

		# send keys
		@self.registry.action(
			'Send strings of special keys like Backspace, Insert, PageDown, Delete, Enter, Shortcuts such as `Control+o`, `Control+Shift+T` are supported as well. This gets used in keyboard.press. Be aware of different operating systems and their shortcuts',
			param_model=SendKeysAction,
			requires_browser=True,
		)
		async def send_keys(params: SendKeysAction, browser: BrowserContext):
			page = await browser.get_current_page()

			await page.keyboard.press(params.keys)
			msg = f'⌨️  Sent keys: {params.keys}'
			logger.info(msg)
			return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='If you dont find something which you want to interact with, scroll to it',
			requires_browser=True,
		)
		async def scroll_to_text(text: str, browser: BrowserContext):  # type: ignore
			page = await browser.get_current_page()
			try:
				# Try different locator strategies
				locators = [
					page.get_by_text(text, exact=False),
					page.locator(f'text={text}'),
					page.locator(f"//*[contains(text(), '{text}')]"),
				]

				for locator in locators:
					try:
						# First check if element exists and is visible
						if await locator.count() > 0 and await locator.first.is_visible():
							await locator.first.scroll_into_view_if_needed()
							await asyncio.sleep(0.5)  # Wait for scroll to complete
							msg = f'🔍  Scrolled to text: {text}'
							logger.info(msg)
							return ActionResult(extracted_content=msg, include_in_memory=True)
					except Exception as e:
						logger.debug(f'Locator attempt failed: {str(e)}')
						continue

				msg = f"Text '{text}' not found or not visible on page"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f"Failed to scroll to text '{text}': {str(e)}"
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

		@self.registry.action(
			description='Get all options from a native dropdown',
			requires_browser=True,
		)
		async def get_dropdown_options(index: int, browser: BrowserContext) -> ActionResult:
			"""Get all options from a native dropdown"""
			page = await browser.get_current_page()
			selector_map = await browser.get_selector_map()
			dom_element = selector_map[index]

			try:
				# Frame-aware approach since we know it works
				all_options = []
				frame_index = 0

				for frame in page.frames:
					try:
						options = await frame.evaluate(
							"""
							(xpath) => {
								const select = document.evaluate(xpath, document, null,
									XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
								if (!select) return null;

								return {
									options: Array.from(select.options).map(opt => ({
										text: opt.text, //do not trim, because we are doing exact match in select_dropdown_option
										value: opt.value,
										index: opt.index
									})),
									id: select.id,
									name: select.name
								};
							}
						""",
							dom_element.xpath,
						)

						if options:
							logger.debug(f'Found dropdown in frame {frame_index}')
							logger.debug(f'Dropdown ID: {options["id"]}, Name: {options["name"]}')

							formatted_options = []
							for opt in options['options']:
								# encoding ensures AI uses the exact string in select_dropdown_option
								encoded_text = json.dumps(opt['text'])
								formatted_options.append(f'{opt["index"]}: text={encoded_text}')

							all_options.extend(formatted_options)

					except Exception as frame_e:
						logger.debug(f'Frame {frame_index} evaluation failed: {str(frame_e)}')

					frame_index += 1

				if all_options:
					msg = '\n'.join(all_options)
					msg += '\nUse the exact text string in select_dropdown_option'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)
				else:
					msg = 'No options found in any frame for dropdown'
					logger.info(msg)
					return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				logger.error(f'Failed to get dropdown options: {str(e)}')
				msg = f'Error getting options: {str(e)}'
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

		@self.registry.action(
			description='Select dropdown option for interactive element index by the text of the option you want to select',
			requires_browser=True,
		)
		async def select_dropdown_option(
			index: int,
			text: str,
			browser: BrowserContext,
		) -> ActionResult:
			"""Select dropdown option by the text of the option you want to select"""
			page = await browser.get_current_page()
			selector_map = await browser.get_selector_map()
			dom_element = selector_map[index]

			# Validate that we're working with a select element
			if dom_element.tag_name != 'select':
				logger.error(f'Element is not a select! Tag: {dom_element.tag_name}, Attributes: {dom_element.attributes}')
				msg = f'Cannot select option: Element with index {index} is a {dom_element.tag_name}, not a select'
				return ActionResult(extracted_content=msg, include_in_memory=True)

			logger.debug(f"Attempting to select '{text}' using xpath: {dom_element.xpath}")
			logger.debug(f'Element attributes: {dom_element.attributes}')
			logger.debug(f'Element tag: {dom_element.tag_name}')

			xpath = '//' + dom_element.xpath

			try:
				frame_index = 0
				for frame in page.frames:
					try:
						logger.debug(f'Trying frame {frame_index} URL: {frame.url}')

						# First verify we can find the dropdown in this frame
						find_dropdown_js = """
							(xpath) => {
								try {
									const select = document.evaluate(xpath, document, null,
										XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
									if (!select) return null;
									if (select.tagName.toLowerCase() !== 'select') {
										return {
											error: `Found element but it's a ${select.tagName}, not a SELECT`,
											found: false
										};
									}
									return {
										id: select.id,
										name: select.name,
										found: true,
										tagName: select.tagName,
										optionCount: select.options.length,
										currentValue: select.value,
										availableOptions: Array.from(select.options).map(o => o.text.trim())
									};
								} catch (e) {
									return {error: e.toString(), found: false};
								}
							}
						"""

						dropdown_info = await frame.evaluate(find_dropdown_js, dom_element.xpath)

						if dropdown_info:
							if not dropdown_info.get('found'):
								logger.error(f'Frame {frame_index} error: {dropdown_info.get("error")}')
								continue

							logger.debug(f'Found dropdown in frame {frame_index}: {dropdown_info}')

							# "label" because we are selecting by text
							# nth(0) to disable error thrown by strict mode
							# timeout=1000 because we are already waiting for all network events, therefore ideally we don't need to wait a lot here (default 30s)
							selected_option_values = (
								await frame.locator('//' + dom_element.xpath).nth(0).select_option(label=text, timeout=1000)
							)

							msg = f'selected option {text} with value {selected_option_values}'
							logger.info(msg + f' in frame {frame_index}')

							return ActionResult(extracted_content=msg, include_in_memory=True)

					except Exception as frame_e:
						logger.error(f'Frame {frame_index} attempt failed: {str(frame_e)}')
						logger.error(f'Frame type: {type(frame)}')
						logger.error(f'Frame URL: {frame.url}')

					frame_index += 1

				msg = f"Could not select option '{text}' in any frame"
				logger.info(msg)
				return ActionResult(extracted_content=msg, include_in_memory=True)

			except Exception as e:
				msg = f'Selection failed: {str(e)}'
				logger.error(msg)
				return ActionResult(error=msg, include_in_memory=True)

	def action(self, description: str, **kwargs):
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		return self.registry.action(description, **kwargs)

	@time_execution_async('--multi-act')
	async def multi_act(
		self, actions: list[ActionModel], browser_context: BrowserContext, check_for_new_elements: bool = True
	) -> list[ActionResult]:
		"""Execute multiple actions"""
		results = []

		# PlaywrightLogger에 브라우저 컨텍스트 설정
		self.logger.browser_context = browser_context

		session = await browser_context.get_session()
		cached_selector_map = session.cached_state.selector_map
		cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())
		await browser_context.remove_highlights()

		for i, action in enumerate(actions):
			if action.get_index() is not None and i != 0:
				new_state = await browser_context.get_state()
				new_path_hashes = set(e.hash.branch_path_hash for e in new_state.selector_map.values())
				if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
					# next action requires index but there are new elements on the page
					logger.info(f'Something new appeared after action {i} / {len(actions)}')
					break

			results.append(await self.act(action, browser_context))

			logger.debug(f'Executed action {i + 1} / {len(actions)}')
			if results[-1].is_done or results[-1].error or i == len(actions) - 1:
				break

			await asyncio.sleep(browser_context.config.wait_between_actions)
			# hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

		return results

	@time_execution_sync('--act')
	async def act(self, action: ActionModel, browser_context: BrowserContext) -> ActionResult:
		"""Execute an action"""
		try:
			# 디버깅 정보 출력
			print("\n=== 디버깅: Controller.act 메서드 호출 ===")
			print(f"액션: {action}")
			print(f"액션 타입: {type(action)}")
			
			# 액션 정보 추출
			element_index = None
			text = None
			url = None
			xpath = None
			action_name = "unknown"  # 기본값 설정
			params = {}  # 기본값 설정
			
			# 액션 파라미터에서 필요한 정보 추출
			try:
				# 액션 타입과 파라미터 추출
				action_dict = action.model_dump(exclude_unset=True)
				for name, parameters in action_dict.items():
					if parameters is not None:
						action_name = name
						params = parameters
						break
				
				# 액션 타입에 따라 element_index 추출
				if action_name == 'click_element' and isinstance(params, dict) and 'index' in params:
					element_index = params['index']
					print(f"디버깅: element_index = {element_index} (click_element)")
				elif action_name == 'input_text' and isinstance(params, dict) and 'index' in params:
					element_index = params['index']
					print(f"디버깅: element_index = {element_index} (input_text)")
				else:
					print(f"디버깅: element_index = None (액션: {action_name})")
				
				# 기타 파라미터 추출
				if isinstance(params, dict):
					if 'text' in params:
						text = params['text']
					if 'url' in params:
						url = params['url']
					if 'xpath' in params:
						xpath = params['xpath']
			except Exception as e:
				print(f"디버깅: 액션 파라미터 추출 중 오류 발생: {str(e)}")
			print("=== 디버깅 정보 끝 ===\n")
			
			# PlaywrightLogger에 브라우저 컨텍스트 설정 (만약 설정되지 않았다면)
			if self.logger.browser_context is None:
				self.logger.browser_context = browser_context

			# 현재 페이지 URL 및 타이틀 가져오기
			current_url = None
			page_title = None
			try:
				page = await browser_context.get_current_page()
				current_url = page.url
				page_title = await page.title()
			except Exception as e:
				logger.debug(f"Failed to get page info: {str(e)}")
			
			# 요소 상세 정보 수집 (Playwright ElementHandle 사용)
			element_details = {}
			if element_index is not None:
				try:
					# 브라우저 컨텍스트를 통해 요소 핸들 가져오기
					element_handle = await browser_context.get_element_by_index(element_index)
					print(f"디버깅: element_handle = {element_handle}")
					
					if element_handle:
						# 요소의 상세 정보 수집
						element_details = {
							"index": element_index,
							"tag_name": await element_handle.evaluate("el => el.tagName.toLowerCase()"),
							"text_content": await element_handle.text_content(),
							"inner_text": await element_handle.evaluate("el => el.innerText || ''"),
							"is_visible": await element_handle.is_visible(),
							"is_enabled": await element_handle.is_enabled(),
							"attributes": {}
						}
						
						print(f"디버깅: element_details = {element_details}")
						
						# 중요 속성 수집
						for attr in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'placeholder', 'aria-label', 'role', 'title', 'alt', 'data-testid']:
							value = await element_handle.get_attribute(attr)
							if value:
								element_details["attributes"][attr] = value
								print(f"디버깅: 속성 {attr} = {value}")
						
						# 요소의 위치와 크기 정보 수집
						bbox = await element_handle.bounding_box()
						if bbox:
							element_details["position"] = {'x': bbox['x'], 'y': bbox['y']}
							element_details["size"] = {'width': bbox['width'], 'height': bbox['height']}
						
						# XPath 생성
						element_details["xpath"] = await element_handle.evaluate("""el => {
							const getXPath = function(element) {
								if (element.id !== '') return '//*[@id="' + element.id + '"]';
								if (element === document.body) return '/html/body';
								
								let ix = 0;
								const siblings = element.parentNode.childNodes;
								
								for (let i = 0; i < siblings.length; i++) {
									const sibling = siblings[i];
									if (sibling === element) return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
									if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
								}
							};
							return getXPath(el);
						}""")
						
						# CSS 선택자 생성
						element_details["css_selector"] = await element_handle.evaluate("""el => {
							const getCssSelector = function(el) {
								if (el.id) return '#' + el.id;
								if (el.classList && el.classList.length > 0) return el.tagName.toLowerCase() + '.' + Array.from(el.classList).join('.');
								
								// 기본 선택자
								let selector = el.tagName.toLowerCase();
								
								// 속성 추가
								if (el.id) selector += '#' + el.id;
								if (el.name) selector += '[name="' + el.name + '"]';
								
								return selector;
							};
							return getCssSelector(el);
						}""")
						
						print(f"디버깅: xpath = {element_details['xpath']}")
						print(f"디버깅: css_selector = {element_details['css_selector']}")
						
						# 부모 요소 정보 수집
						try:
							parent_info = await element_handle.evaluate("""el => {
								const parent = el.parentElement;
								if (!parent) return null;
								
								return {
									tag_name: parent.tagName.toLowerCase(),
									id: parent.id || null,
									class_name: parent.className || null,
									has_parent: !!parent.parentElement
								};
							}""")
							
							if parent_info:
								element_details["parent_info"] = parent_info
								print(f"디버깅: parent_info = {parent_info}")
						except Exception as e:
							logger.debug(f"Failed to get parent info: {str(e)}")
						
						# 자식 요소 정보 수집
						try:
							children_info = await element_handle.evaluate("""el => {
								const children = Array.from(el.children);
								return {
									count: children.length,
									tags: children.map(child => child.tagName.toLowerCase())
								};
							}""")
							
							if children_info:
								element_details["children_info"] = children_info
								print(f"디버깅: children_info = {children_info}")
						except Exception as e:
							logger.debug(f"Failed to get children info: {str(e)}")
						
						logger.debug(f"Collected detailed element info for index {element_index}")
				except Exception as e:
					logger.debug(f"Failed to collect element details: {str(e)}")
					print(f"디버깅 예외: {str(e)}")
			
			# 액션 실행 전 로깅 (상세 정보 포함)
			print(f"디버깅: log_action_before_execute 호출 전 - element_index={element_index}, selector={element_details.get('css_selector') if element_details else None}")
			pre_action_element_info = await self.logger.log_action_before_execute(
				action_type=action_name,
				element_index=element_index,
				selector=element_details.get("css_selector") if element_details else None,
				xpath=element_details.get("xpath") if element_details else xpath,
				text=text,
				url=url
			)
			print(f"디버깅: log_action_before_execute 호출 후 - pre_action_element_info={pre_action_element_info}")
			
			# 요소 상세 정보가 있으면 로그 파일에 추가 기록
			if element_details:
				with open(self.logger.element_details_log_file, 'a', encoding='utf-8') as f:
					f.write(f"=== PRE-ACTION ELEMENT DETAILS: {action_name} - {datetime.now().isoformat()} ===\n")
					f.write(f"Element Index: {element_index}\n")
					f.write(f"Tag: {element_details.get('tag_name', 'unknown')}\n")
					f.write(f"Text Content: {element_details.get('text_content', '')[:200]}\n")
					f.write(f"Is Visible: {element_details.get('is_visible', False)}\n")
					f.write(f"Is Enabled: {element_details.get('is_enabled', False)}\n")
					
					if "attributes" in element_details:
						f.write("Attributes:\n")
						for key, value in element_details["attributes"].items():
							f.write(f"  {key}: {value}\n")
					
					if "position" in element_details:
						f.write(f"Position: x={element_details['position']['x']}, y={element_details['position']['y']}\n")
					
					if "size" in element_details:
						f.write(f"Size: width={element_details['size']['width']}, height={element_details['size']['height']}\n")
					
					if "xpath" in element_details:
						f.write(f"XPath: {element_details['xpath']}\n")
					
					if "css_selector" in element_details:
						f.write(f"CSS Selector: {element_details['css_selector']}\n")
					
					if "parent_info" in element_details:
						f.write("Parent Element:\n")
						for key, value in element_details["parent_info"].items():
							f.write(f"  {key}: {value}\n")
					
					if "children_info" in element_details:
						f.write(f"Children Count: {element_details['children_info']['count']}\n")
						f.write(f"Children Tags: {', '.join(element_details['children_info']['tags'])}\n")
					
					f.write("-" * 80 + "\n\n")
			
			# 액션 실행 시작 시간 기록
			start_time = datetime.now()
			
			# 액션 실행
			result = None
			error = None
			action_result = None
			
			try:
				# 하이라이트 제거
				await browser_context.remove_highlights()
				
				# 액션 실행
				result = await self.registry.execute_action(action_name, params, browser=browser_context)
				
				# 결과 처리
				if isinstance(result, str):
					action_result = ActionResult(extracted_content=result)
				elif isinstance(result, ActionResult):
					action_result = result
				elif result is None:
					action_result = ActionResult()
				else:
					raise ValueError(f'Invalid action result type: {type(result)} of {result}')
				
				# 결과 문자열 추출
				result_str = action_result.extracted_content if action_result.extracted_content else "Success"
				
			except Exception as e:
				error = str(e)
				logger.error(f"Error executing action {action_name}: {error}")
				raise e
			
			finally:
				# 액션 실행 종료 시간 및 소요 시간 계산
				end_time = datetime.now()
				duration_ms = (end_time - start_time).total_seconds() * 1000
				
				# 페이지 변경 여부 확인
				page_changed = False
				new_url = None
				new_title = None
				try:
					page = await browser_context.get_current_page()
					new_url = page.url
					new_title = await page.title()
					page_changed = (current_url != new_url) or (page_title != new_title)
				except Exception as e:
					logger.debug(f"Failed to check page change: {str(e)}")
				
				# 액션 실행 후 요소 상태 확인 (가능한 경우)
				post_action_element_details = {}
				if element_index is not None and not page_changed:
					try:
						element_handle = await browser_context.get_element_by_index(element_index)
						if element_handle:
							# 요소의 상태 변화 확인
							post_action_element_details = {
								"is_visible": await element_handle.is_visible(),
								"is_enabled": await element_handle.is_enabled(),
								"text_content": await element_handle.text_content(),
								"attributes": {}
							}
							
							# 중요 속성 수집
							for attr in ['value', 'class', 'style']:
								value = await element_handle.get_attribute(attr)
								if value:
									post_action_element_details["attributes"][attr] = value
					except Exception as e:
						logger.debug(f"Failed to collect post-action element details: {str(e)}")
				
				# 액션 실행 후 로깅 (성공 또는 실패 여부와 관계없이)
				await self.logger.log_action_after_execute(
					action_type=action_name,
					pre_action_element_info=pre_action_element_info,
					element_index=element_index,
					selector=element_details.get("css_selector") if element_details else None,
					xpath=element_details.get("xpath") if element_details else xpath,
					text=text,
					url=url,
					result=result_str if 'result_str' in locals() else None,
					error=error,
					additional_data={
						"action_params": str(params),
						"duration_ms": duration_ms,
						"page_changed": page_changed,
						"previous_url": current_url,
						"previous_title": page_title,
						"new_url": new_url,
						"new_title": new_title,
						"element_details": element_details,
						"post_action_element_details": post_action_element_details
					}
				)
			
			return action_result
		except Exception as e:
			raise e
