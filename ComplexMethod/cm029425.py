async def fill(self, value: str, clear: bool = True) -> None:
		"""Fill the input element using proper CDP methods with improved focus handling."""
		try:
			# Use the existing CDP client and session
			cdp_client = self._client
			session_id = self._session_id
			backend_node_id = self._backend_node_id

			# Track coordinates for metadata
			input_coordinates = None

			# Scroll element into view
			try:
				await cdp_client.send.DOM.scrollIntoViewIfNeeded(params={'backendNodeId': backend_node_id}, session_id=session_id)
				await asyncio.sleep(0.01)
			except Exception as e:
				logger.warning(f'Failed to scroll element into view: {e}')

			# Get object ID for the element
			result = await cdp_client.send.DOM.resolveNode(
				params={'backendNodeId': backend_node_id},
				session_id=session_id,
			)
			if 'object' not in result or 'objectId' not in result['object']:
				raise RuntimeError('Failed to get object ID for element')
			object_id = result['object']['objectId']

			# Get element coordinates for focus
			try:
				bounds_result = await cdp_client.send.Runtime.callFunctionOn(
					params={
						'functionDeclaration': 'function() { return this.getBoundingClientRect(); }',
						'objectId': object_id,
						'returnByValue': True,
					},
					session_id=session_id,
				)
				if bounds_result.get('result', {}).get('value'):
					bounds = bounds_result['result']['value']  # type: ignore
					center_x = bounds['x'] + bounds['width'] / 2
					center_y = bounds['y'] + bounds['height'] / 2
					input_coordinates = {'input_x': center_x, 'input_y': center_y}
					logger.debug(f'Using element coordinates: x={center_x:.1f}, y={center_y:.1f}')
			except Exception as e:
				logger.debug(f'Could not get element coordinates: {e}')

			# Ensure session_id is not None
			if session_id is None:
				raise RuntimeError('Session ID is required for fill operation')

			# Step 1: Focus the element
			focused_successfully = await self._focus_element_simple(
				backend_node_id=backend_node_id,
				object_id=object_id,
				cdp_client=cdp_client,
				session_id=session_id,
				input_coordinates=input_coordinates,
			)

			# Step 2: Clear existing text if requested
			if clear:
				cleared_successfully = await self._clear_text_field(
					object_id=object_id, cdp_client=cdp_client, session_id=session_id
				)
				if not cleared_successfully:
					logger.warning('Text field clearing failed, typing may append to existing text')

			# Step 3: Type the text character by character using proper human-like key events
			logger.debug(f'Typing text character by character: "{value}"')

			for i, char in enumerate(value):
				# Handle newline characters as Enter key
				if char == '\n':
					# Send proper Enter key sequence
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=session_id,
					)

					# Small delay to emulate human typing speed
					await asyncio.sleep(0.001)

					# Send char event with carriage return
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': '\r',
							'key': 'Enter',
						},
						session_id=session_id,
					)

					# Send keyUp event
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': 'Enter',
							'code': 'Enter',
							'windowsVirtualKeyCode': 13,
						},
						session_id=session_id,
					)
				else:
					# Handle regular characters
					# Get proper modifiers, VK code, and base key for the character
					modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(char)
					key_code = self._get_key_code_for_char(base_key)

					# Step 1: Send keyDown event (NO text parameter)
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=session_id,
					)

					# Small delay to emulate human typing speed
					await asyncio.sleep(0.001)

					# Step 2: Send char event (WITH text parameter) - this is crucial for text input
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': char,
							'key': char,
						},
						session_id=session_id,
					)

					# Step 3: Send keyUp event (NO text parameter)
					await cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': base_key,
							'code': key_code,
							'modifiers': modifiers,
							'windowsVirtualKeyCode': vk_code,
						},
						session_id=session_id,
					)

				# Add 18ms delay between keystrokes
				await asyncio.sleep(0.018)

		except Exception as e:
			raise Exception(f'Failed to fill element: {str(e)}')