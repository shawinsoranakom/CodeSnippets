async def on_SendKeysEvent(self, event: SendKeysEvent) -> None:
		"""Handle send keys request with CDP."""
		cdp_session = await self.browser_session.get_or_create_cdp_session(focus=True)
		try:
			# Normalize key names from common aliases
			key_aliases = {
				'ctrl': 'Control',
				'control': 'Control',
				'alt': 'Alt',
				'option': 'Alt',
				'meta': 'Meta',
				'cmd': 'Meta',
				'command': 'Meta',
				'shift': 'Shift',
				'enter': 'Enter',
				'return': 'Enter',
				'tab': 'Tab',
				'delete': 'Delete',
				'backspace': 'Backspace',
				'escape': 'Escape',
				'esc': 'Escape',
				'space': ' ',
				'up': 'ArrowUp',
				'down': 'ArrowDown',
				'left': 'ArrowLeft',
				'right': 'ArrowRight',
				'pageup': 'PageUp',
				'pagedown': 'PageDown',
				'home': 'Home',
				'end': 'End',
			}

			# Parse and normalize the key string
			keys = event.keys
			if '+' in keys:
				# Handle key combinations like "ctrl+a"
				parts = keys.split('+')
				normalized_parts = []
				for part in parts:
					part_lower = part.strip().lower()
					normalized = key_aliases.get(part_lower, part)
					normalized_parts.append(normalized)
				normalized_keys = '+'.join(normalized_parts)
			else:
				# Single key
				keys_lower = keys.strip().lower()
				normalized_keys = key_aliases.get(keys_lower, keys)

			# Handle key combinations like "Control+A"
			if '+' in normalized_keys:
				parts = normalized_keys.split('+')
				modifiers = parts[:-1]
				main_key = parts[-1]

				# Calculate modifier bitmask
				modifier_value = 0
				modifier_map = {'Alt': 1, 'Control': 2, 'Meta': 4, 'Shift': 8}
				for mod in modifiers:
					modifier_value |= modifier_map.get(mod, 0)

				# Press modifier keys
				for mod in modifiers:
					await self._dispatch_key_event(cdp_session, 'keyDown', mod)

				# Press main key with modifiers bitmask
				await self._dispatch_key_event(cdp_session, 'keyDown', main_key, modifier_value)

				await self._dispatch_key_event(cdp_session, 'keyUp', main_key, modifier_value)

				# Release modifier keys
				for mod in reversed(modifiers):
					await self._dispatch_key_event(cdp_session, 'keyUp', mod)
			else:
				# Check if this is a text string or special key
				special_keys = {
					'Enter',
					'Tab',
					'Delete',
					'Backspace',
					'Escape',
					'ArrowUp',
					'ArrowDown',
					'ArrowLeft',
					'ArrowRight',
					'PageUp',
					'PageDown',
					'Home',
					'End',
					'Control',
					'Alt',
					'Meta',
					'Shift',
					'F1',
					'F2',
					'F3',
					'F4',
					'F5',
					'F6',
					'F7',
					'F8',
					'F9',
					'F10',
					'F11',
					'F12',
				}

				# If it's a special key, use original logic
				if normalized_keys in special_keys:
					await self._dispatch_key_event(cdp_session, 'keyDown', normalized_keys)
					# For Enter key, also dispatch a char event to trigger keypress listeners
					if normalized_keys == 'Enter':
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': 'char',
								'text': '\r',
								'key': 'Enter',
							},
							session_id=cdp_session.session_id,
						)
					await self._dispatch_key_event(cdp_session, 'keyUp', normalized_keys)
				else:
					# It's text (single character or string) - send each character as text input
					# This is crucial for text to appear in focused input fields
					for char in normalized_keys:
						# Special-case newline characters to dispatch as Enter
						if char in ('\n', '\r'):
							await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
								params={
									'type': 'rawKeyDown',
									'windowsVirtualKeyCode': 13,
									'unmodifiedText': '\r',
									'text': '\r',
								},
								session_id=cdp_session.session_id,
							)
							await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
								params={
									'type': 'char',
									'windowsVirtualKeyCode': 13,
									'unmodifiedText': '\r',
									'text': '\r',
								},
								session_id=cdp_session.session_id,
							)
							await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
								params={
									'type': 'keyUp',
									'windowsVirtualKeyCode': 13,
									'unmodifiedText': '\r',
									'text': '\r',
								},
								session_id=cdp_session.session_id,
							)
							continue

						# Get proper modifiers and key info for the character
						modifiers, vk_code, base_key = self._get_char_modifiers_and_vk(char)
						key_code = self._get_key_code_for_char(base_key)

						# Send keyDown
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

						# Send char event with text - this is what makes text appear in input fields
						await cdp_session.cdp_client.send.Input.dispatchKeyEvent(
							params={
								'type': 'char',
								'text': char,
								'key': char,
							},
							session_id=cdp_session.session_id,
						)

						# Send keyUp
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

						# Small delay between characters (10ms)
						await asyncio.sleep(0.010)

			self.logger.info(f'⌨️ Sent keys: {event.keys}')

			# Note: We don't clear cached state on Enter; multi_act will detect DOM changes
			# and rebuild explicitly. We still wait briefly for potential navigation.
			if 'enter' in event.keys.lower() or 'return' in event.keys.lower():
				await asyncio.sleep(0.1)
		except Exception as e:
			raise