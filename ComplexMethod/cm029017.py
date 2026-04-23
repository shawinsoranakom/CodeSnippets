async def test_dom_serializer_with_shadow_dom_and_iframes(self, browser_session, base_url):
		"""Test DOM serializer extracts elements from shadow DOM, same-origin iframes, and cross-origin iframes.

		This test verifies:
		1. Elements are in the serializer (selector_map)
		2. We can click elements using click(index)

		Expected interactive elements:
		- Regular DOM: 3 elements (button, input, link on main page)
		- Shadow DOM: 3 elements (2 buttons, 1 input inside shadow root)
		- Same-origin iframe: 2 elements (button, input inside iframe)
		- Cross-origin iframe placeholder: about:blank (no interactive elements)
		- Iframe tags: 2 elements (the iframe elements themselves)
		Total: ~10 interactive elements
		"""
		from browser_use.tools.service import Tools

		tools = Tools()

		# Create mock LLM actions that will click elements from each category
		# We'll generate actions dynamically after we know the indices
		actions = [
			f"""
			{{
				"thinking": "I'll navigate to the DOM test page",
				"evaluation_previous_goal": "Starting task",
				"memory": "Navigating to test page",
				"next_goal": "Navigate to test page",
				"action": [
					{{
						"navigate": {{
							"url": "{base_url}/dom-test-main",
							"new_tab": false
						}}
					}}
				]
			}}
			"""
		]
		await tools.navigate(url=f'{base_url}/dom-test-main', new_tab=False, browser_session=browser_session)

		import asyncio

		await asyncio.sleep(1)

		# Get the browser state to access selector_map
		browser_state_summary = await browser_session.get_browser_state_summary(
			include_screenshot=False,
			include_recent_events=False,
		)

		assert browser_state_summary is not None, 'Browser state summary should not be None'
		assert browser_state_summary.dom_state is not None, 'DOM state should not be None'

		selector_map = browser_state_summary.dom_state.selector_map
		print(f'   Selector map: {selector_map.keys()}')

		print('\n📊 DOM Serializer Analysis:')
		print(f'   Total interactive elements found: {len(selector_map)}')
		serilized_text = browser_state_summary.dom_state.llm_representation()
		print(f'   Serialized text: {serilized_text}')
		# assume all selector map keys are as text in the serialized text
		# for idx, element in selector_map.items():
		# 	assert str(idx) in serilized_text, f'Element {idx} should be in serialized text'
		# 	print(f'   ✓ Element {idx} found in serialized text')

		# assume at least 10 interactive elements are in the selector map
		assert len(selector_map) >= 10, f'Should find at least 10 interactive elements, found {len(selector_map)}'

		# assert all interactive elements marked with [123] from serialized text are in selector map
		# find all [index] from serialized text with regex
		import re

		indices = re.findall(r'\[(\d+)\]', serilized_text)
		for idx in indices:
			assert int(idx) in selector_map.keys(), f'Element {idx} should be in selector map'
			print(f'   ✓ Element {idx} found in selector map')

		regular_elements = []
		shadow_elements = []
		iframe_content_elements = []
		iframe_tags = []

		# Categorize elements by their IDs (more stable than hardcoded indices)
		# Check element attributes to identify their location
		for idx, element in selector_map.items():
			# Check if this is an iframe tag (not content inside iframe)
			if element.tag_name == 'iframe':
				iframe_tags.append((idx, element))
			# Check if element has an ID attribute
			elif hasattr(element, 'attributes') and 'id' in element.attributes:
				elem_id = element.attributes['id'].lower()
				# Shadow DOM elements have IDs starting with "shadow-"
				if elem_id.startswith('shadow-'):
					shadow_elements.append((idx, element))
				# Iframe content elements have IDs starting with "iframe-"
				elif elem_id.startswith('iframe-'):
					iframe_content_elements.append((idx, element))
				# Everything else is regular DOM
				else:
					regular_elements.append((idx, element))
			# Elements without IDs are regular DOM
			else:
				regular_elements.append((idx, element))

		# Verify element counts based on our test page structure:
		# - Regular DOM: 3-4 elements (button, input, link on main page + possible cross-origin content)
		# - Shadow DOM: 3 elements (2 buttons, 1 input inside shadow root)
		# - Iframe content: 2 elements (button, input from same-origin iframe)
		# - Iframe tags: 2 elements (the iframe elements themselves)
		# Total: ~10-11 interactive elements depending on cross-origin iframe extraction

		print('\n✅ DOM Serializer Test Summary:')
		print(f'   • Regular DOM: {len(regular_elements)} elements {"✓" if len(regular_elements) >= 3 else "✗"}')
		print(f'   • Shadow DOM: {len(shadow_elements)} elements {"✓" if len(shadow_elements) >= 3 else "✗"}')
		print(
			f'   • Same-origin iframe content: {len(iframe_content_elements)} elements {"✓" if len(iframe_content_elements) >= 2 else "✗"}'
		)
		print(f'   • Iframe tags: {len(iframe_tags)} elements {"✓" if len(iframe_tags) >= 2 else "✗"}')
		print(f'   • Total elements: {len(selector_map)}')

		# Verify we found elements from all sources
		assert len(selector_map) >= 8, f'Should find at least 8 interactive elements, found {len(selector_map)}'
		assert len(regular_elements) >= 1, f'Should find at least 1 regular DOM element, found {len(regular_elements)}'
		assert len(shadow_elements) >= 1, f'Should find at least 1 shadow DOM element, found {len(shadow_elements)}'
		assert len(iframe_content_elements) >= 1, (
			f'Should find at least 1 iframe content element, found {len(iframe_content_elements)}'
		)

		# Now test clicking elements from each category using tools.click(index)
		print('\n🖱️  Testing Click Functionality:')

		# Helper to call tools.click(index) and verify it worked
		async def click(index: int, element_description: str, browser_session: BrowserSession):
			result = await tools.click(index=index, browser_session=browser_session)
			# Check both error field and extracted_content for failure messages
			if result.error:
				raise AssertionError(f'Click on {element_description} [{index}] failed: {result.error}')
			if result.extracted_content and (
				'not available' in result.extracted_content.lower() or 'failed' in result.extracted_content.lower()
			):
				raise AssertionError(f'Click on {element_description} [{index}] failed: {result.extracted_content}')
			print(f'   ✓ {element_description} [{index}] clicked successfully')
			return result

		# Test clicking a regular DOM element (button)
		if regular_elements:
			regular_button_idx = next((idx for idx, el in regular_elements if 'regular-btn' in el.attributes.get('id', '')), None)
			if regular_button_idx:
				await click(regular_button_idx, 'Regular DOM button', browser_session)

		# Test clicking a shadow DOM element (button)
		if shadow_elements:
			shadow_button_idx = next((idx for idx, el in shadow_elements if 'btn' in el.attributes.get('id', '')), None)
			if shadow_button_idx:
				await click(shadow_button_idx, 'Shadow DOM button', browser_session)

		# Test clicking a same-origin iframe element (button)
		if iframe_content_elements:
			iframe_button_idx = next((idx for idx, el in iframe_content_elements if 'btn' in el.attributes.get('id', '')), None)
			if iframe_button_idx:
				await click(iframe_button_idx, 'Same-origin iframe button', browser_session)

		# Validate click counter - verify all 3 clicks actually executed JavaScript
		print('\n✅ Validating click counter...')

		# Get the CDP session for the main page (use target from a regular DOM element)
		# Note: browser_session.agent_focus_target_id may point to a different target than the page
		if regular_elements and regular_elements[0][1].target_id:
			cdp_session = await browser_session.get_or_create_cdp_session(target_id=regular_elements[0][1].target_id)
		else:
			cdp_session = await browser_session.get_or_create_cdp_session()

		result = await cdp_session.cdp_client.send.Runtime.evaluate(
			params={
				'expression': 'window.getClickCount()',
				'returnByValue': True,
			},
			session_id=cdp_session.session_id,
		)

		click_count = result.get('result', {}).get('value', 0)
		print(f'   Click counter value: {click_count}')

		assert click_count == 3, (
			f'Expected 3 clicks (Regular DOM + Shadow DOM + Iframe), but counter shows {click_count}. '
			f'This means some clicks did not execute JavaScript properly.'
		)

		print('\n🎉 DOM Serializer test completed successfully!')