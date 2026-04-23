async def _input_text_element_node_impl(
		self, element_node: EnhancedDOMTreeNode, text: str, clear: bool = True, is_sensitive: bool = False
	) -> dict | None:
		"""
		Input text into an element using pure CDP with improved focus fallbacks.

		For date/time inputs, uses direct value assignment instead of typing.
		"""

		try:
			# Get CDP client
			cdp_client = self.browser_session.cdp_client

			# Get the correct session ID for the element's iframe
			# session_id = await self._get_session_id_for_element(element_node)

			# cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=element_node.target_id, focus=True)
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Get element info
			backend_node_id = element_node.backend_node_id

			# Track coordinates for metadata
			input_coordinates = None

			# Scroll element into view
			try:
				await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
					params={'backendNodeId': backend_node_id}, session_id=cdp_session.session_id
				)
				await asyncio.sleep(0.01)
			except Exception as e:
				# Node detached errors are common with shadow DOM and dynamic content
				# The element can still be interacted with even if scrolling fails
				error_str = str(e)
				if 'Node is detached from document' in error_str or 'detached from document' in error_str:
					self.logger.debug(
						f'Element node temporarily detached during scroll (common with shadow DOM), continuing: {element_node}'
					)
				else:
					self.logger.debug(f'Failed to scroll element {element_node} into view before typing: {type(e).__name__}: {e}')

			# Get object ID for the element
			result = await cdp_client.send.DOM.resolveNode(
				params={'backendNodeId': backend_node_id},
				session_id=cdp_session.session_id,
			)
			assert 'object' in result and 'objectId' in result['object'], (
				'Failed to find DOM element based on backendNodeId, maybe page content changed?'
			)
			object_id = result['object']['objectId']

			# Get current coordinates using unified method
			coords = await self.browser_session.get_element_coordinates(backend_node_id, cdp_session)
			if coords:
				center_x = coords.x + coords.width / 2
				center_y = coords.y + coords.height / 2

				# Check for occlusion before using coordinates for focus
				is_occluded = await self._check_element_occlusion(backend_node_id, center_x, center_y, cdp_session)

				if is_occluded:
					self.logger.debug('🚫 Input element is occluded, skipping coordinate-based focus')
					input_coordinates = None  # Force fallback to CDP-only focus
				else:
					input_coordinates = {'input_x': center_x, 'input_y': center_y}
					self.logger.debug(f'Using unified coordinates: x={center_x:.1f}, y={center_y:.1f}')
			else:
				input_coordinates = None
				self.logger.debug('No coordinates found for element')

			# Ensure we have a valid object_id before proceeding
			if not object_id:
				raise ValueError('Could not get object_id for element')

			# Step 1: Focus the element using simple strategy
			focused_successfully = await self._focus_element_simple(
				backend_node_id=backend_node_id, object_id=object_id, cdp_session=cdp_session, input_coordinates=input_coordinates
			)

			# Step 2: Check if this element requires direct value assignment (date/time inputs)
			requires_direct_assignment = self._requires_direct_value_assignment(element_node)

			if requires_direct_assignment:
				# Date/time inputs: use direct value assignment instead of typing
				self.logger.debug(
					f'🎯 Element type={element_node.attributes.get("type")} requires direct value assignment, setting value directly'
				)
				await self._set_value_directly(element_node, text, object_id, cdp_session)

				# Return input coordinates for metadata
				return input_coordinates

			# Step 3: Clear existing text if requested (only for regular inputs that support typing)
			if clear:
				cleared_successfully = await self._clear_text_field(object_id=object_id, cdp_session=cdp_session)
				if not cleared_successfully:
					self.logger.warning('⚠️ Text field clearing failed, typing may append to existing text')

			# Step 4: Type the text character by character using proper human-like key events
			# This emulates exactly how a human would type, which modern websites expect
			if is_sensitive:
				# Note: sensitive_key_name is not passed to this low-level method,
				# but we could extend the signature if needed for more granular logging
				self.logger.debug('🎯 Typing <sensitive> character by character')
			else:
				self.logger.debug(f'🎯 Typing text character by character: "{text}"')

			# Detect contenteditable elements (may have leaf-start bug where first char is dropped)
			_attrs = element_node.attributes or {}
			_is_contenteditable = _attrs.get('contenteditable') in ('true', '') or (
				_attrs.get('role') == 'textbox' and element_node.tag_name not in ('input', 'textarea')
			)

			# For contenteditable: after typing first char, check if dropped and retype if needed
			_check_first_char = _is_contenteditable and len(text) > 0 and clear
			_first_char = text[0] if _check_first_char else None

			for i, char in enumerate(text):
				# Handle newline characters as Enter key
				if char == '\n':
					# Send proper Enter key sequence
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)

					# Small delay to emulate human typing speed
					await asyncio.sleep(0.001)

					# Send char event with carriage return
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': '\r',
							'key': 'Enter',
						},
						session_id=cdp_session.session_id,
					)

					# Send keyUp event
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=cdp_session.session_id,
					)
				else:
					# Handle regular characters
					# Get proper modifiers, VK code, and base key for the character
					modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(char)
					key_code = self._get_key_code_for_char(base_key)

					# self.logger.debug(f'🎯 Typing character {i + 1}/{len(text)}: "{char}" (base_key: {base_key}, code: {key_code}, modifiers: {modifiers}, vk: {vk_code})')

					# Step 1: Send keyDown event (NO text parameter)
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=cdp_session.session_id,
					)

					# Small delay to emulate human typing speed
					await asyncio.sleep(0.005)

					# Step 2: Send char event (WITH text parameter) - this is crucial for text input
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': char,
							'key': char,
						},
						session_id=cdp_session.session_id,
					)

					# Step 3: Send keyUp event (NO text parameter)
					await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=cdp_session.session_id,
					)

				# After first char on contenteditable: check if dropped and retype if needed
				if i == 0 and _check_first_char and _first_char:
					check_result = await cdp_session.cdp_client.send.Runtime.evaluate(
						params={'expression': 'document.activeElement.textContent'},
						session_id=cdp_session.session_id,
					)
					content = check_result.get('result', {}).get('value', '')
					if _first_char not in content:
						self.logger.debug(f'🎯 First char "{_first_char}" was dropped (leaf-start bug), retyping')
						# Retype the first character - cursor now past leaf-start
						modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(_first_char)
						key_code = self._get_key_code_for_char(base_key)
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': 'keyDown',
								'key': base_key,
								'code': key_code,
								'modifiers': modifiers,
								'windowsVirtualKeyCode': vk_code,
							},
							session_id=cdp_session.session_id,
						)
						await asyncio.sleep(0.005)
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={'type': 'char', 'text': _first_char, 'key': _first_char},
							session_id=cdp_session.session_id,
						)
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': 'keyUp',
								'key': base_key,
								'code': key_code,
								'modifiers': modifiers,
								'windowsVirtualKeyCode': vk_code,
							},
							session_id=cdp_session.session_id,
						)

				# Small delay between characters to look human (realistic typing speed)
				await asyncio.sleep(0.001)

			# Step 4: Trigger framework-aware DOM events after typing completion
			# Modern JavaScript frameworks (React, Vue, Angular) rely on these events
			# to update their internal state and trigger re-renders
			await self._trigger_framework_events(object_id=object_id, cdp_session=cdp_session)

			# Step 5: Read back actual value for verification (skip for sensitive data)
			if not is_sensitive:
				try:
					await asyncio.sleep(0.05)  # let autocomplete/formatter JS settle
					readback_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'objectId': object_id,
							'functionDeclaration': 'function() { return this.value !== undefined ? this.value : this.textContent; }',
							'returnByValue': True,
						},
						session_id=cdp_session.session_id,
					)
					actual_value = readback_result.get('result', {}).get('value')
					if actual_value is not None:
						if input_coordinates is None:
							input_coordinates = {}
						input_coordinates['actual_value'] = actual_value
				except Exception as e:
					self.logger.debug(f'Value readback failed (non-critical): {e}')

			# Step 6: Auto-retry on concatenation mismatch (only when clear was requested)
			# If we asked to clear but the readback value contains the typed text as a substring
			# yet is longer, the field had pre-existing text that wasn't cleared. Set directly.
			if clear and not is_sensitive and input_coordinates and 'actual_value' in input_coordinates:
				actual_value = input_coordinates['actual_value']
				if (
					isinstance(actual_value, str)
					and actual_value != text
					and len(actual_value) > len(text)
					and (actual_value.endswith(text) or actual_value.startswith(text))
				):
					self.logger.info(f'🔄 Concatenation detected: got "{actual_value}", expected "{text}" — auto-retrying')
					try:
						# Clear + set value via native setter in one JS call (works with React/Vue)
						retry_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
							params={
								'objectId': object_id,
								'functionDeclaration': """
									function(newValue) {
										if (this.value !== undefined) {
											var desc = Object.getOwnPropertyDescriptor(
												HTMLInputElement.prototype, 'value'
											) || Object.getOwnPropertyDescriptor(
												HTMLTextAreaElement.prototype, 'value'
											);
											if (desc && desc.set) {
												desc.set.call(this, newValue);
											} else {
												this.value = newValue;
											}
										} else if (this.isContentEditable) {
											this.textContent = newValue;
										}
										this.dispatchEvent(new Event('input', { bubbles: true }));
										this.dispatchEvent(new Event('change', { bubbles: true }));
										return this.value !== undefined ? this.value : this.textContent;
									}
								""",
								'arguments': [{'value': text}],
								'returnByValue': True,
							},
							session_id=cdp_session.session_id,
						)
						retry_value = retry_result.get('result', {}).get('value')
						if retry_value is not None:
							input_coordinates['actual_value'] = retry_value
							if retry_value == text:
								self.logger.info('✅ Auto-retry fixed concatenation')
							else:
								self.logger.warning(f'⚠️ Auto-retry value still differs: "{retry_value}"')
					except Exception as e:
						self.logger.debug(f'Auto-retry failed (non-critical): {e}')

			# Return coordinates metadata if available
			return input_coordinates

		except Exception as e:
			self.logger.error(f'Failed to input text via CDP: {type(e).__name__}: {e}')
			raise BrowserError(f'Failed to input text into element: {repr(element_node)}')