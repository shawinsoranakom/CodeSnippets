async def press(self, key: str) -> None:
		"""Press a key on the page (sends keyboard input to the focused element or page)."""
		session_id = await self._ensure_session()

		# Handle key combinations like "Control+A"
		if '+' in key:
			parts = key.split('+')
			modifiers = parts[:-1]
			main_key = parts[-1]

			# Calculate modifier bitmask
			modifier_value = 0
			modifier_map = {'Alt': 1, 'Control': 2, 'Meta': 4, 'Shift': 8}
			for mod in modifiers:
				modifier_value |= modifier_map.get(mod, 0)

			# Press modifier keys
			for mod in modifiers:
				code, vk_code = get_key_info(mod)
				params: 'DispatchKeyEventParameters' = {'type': 'keyDown', 'key': mod, 'code': code}
				if vk_code is not None:
					params['windowsVirtualKeyCode'] = vk_code
				await self._client.send.Input.dispatchKeyEvent(params, session_id=session_id)

			# Press main key with modifiers bitmask
			main_code, main_vk_code = get_key_info(main_key)
			main_down_params: 'DispatchKeyEventParameters' = {
				'type': 'keyDown',
				'key': main_key,
				'code': main_code,
				'modifiers': modifier_value,
			}
			if main_vk_code is not None:
				main_down_params['windowsVirtualKeyCode'] = main_vk_code
			await self._client.send.Input.dispatchKeyEvent(main_down_params, session_id=session_id)

			main_up_params: 'DispatchKeyEventParameters' = {
				'type': 'keyUp',
				'key': main_key,
				'code': main_code,
				'modifiers': modifier_value,
			}
			if main_vk_code is not None:
				main_up_params['windowsVirtualKeyCode'] = main_vk_code
			await self._client.send.Input.dispatchKeyEvent(main_up_params, session_id=session_id)

			# Release modifier keys
			for mod in reversed(modifiers):
				code, vk_code = get_key_info(mod)
				release_params: 'DispatchKeyEventParameters' = {'type': 'keyUp', 'key': mod, 'code': code}
				if vk_code is not None:
					release_params['windowsVirtualKeyCode'] = vk_code
				await self._client.send.Input.dispatchKeyEvent(release_params, session_id=session_id)
		else:
			# Simple key press
			code, vk_code = get_key_info(key)
			key_down_params: 'DispatchKeyEventParameters' = {'type': 'keyDown', 'key': key, 'code': code}
			if vk_code is not None:
				key_down_params['windowsVirtualKeyCode'] = vk_code
			await self._client.send.Input.dispatchKeyEvent(key_down_params, session_id=session_id)

			key_up_params: 'DispatchKeyEventParameters' = {'type': 'keyUp', 'key': key, 'code': code}
			if vk_code is not None:
				key_up_params['windowsVirtualKeyCode'] = vk_code
			await self._client.send.Input.dispatchKeyEvent(key_up_params, session_id=session_id)