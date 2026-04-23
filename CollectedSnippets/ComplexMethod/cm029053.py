async def handle_model_action(browser_session: BrowserSession, action) -> ActionResult:
	"""
	Given a computer action (e.g., click, double_click, scroll, etc.),
	execute the corresponding operation using CDP.
	"""
	action_type = action.type
	ERROR_MSG: str = 'Could not execute the CUA action.'

	if not browser_session.agent_focus_target_id:
		return ActionResult(error='No active browser session')

	# Get CDP session for the focused target using the public API
	try:
		cdp_session = await browser_session.get_or_create_cdp_session(browser_session.agent_focus_target_id, focus=False)
	except Exception as e:
		return ActionResult(error=f'Failed to get CDP session: {e}')

	try:
		match action_type:
			case 'click':
				x, y = action.x, action.y
				button = action.button
				print(f"Action: click at ({x}, {y}) with button '{button}'")
				# Not handling things like middle click, etc.
				if button != 'left' and button != 'right':
					button = 'left'

				# Use CDP to click
				await browser_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mousePressed',
						'x': x,
						'y': y,
						'button': button,
						'clickCount': 1,
					},
					session_id=cdp_session.session_id,
				)
				await browser_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseReleased',
						'x': x,
						'y': y,
						'button': button,
					},
					session_id=cdp_session.session_id,
				)
				msg = f'Clicked at ({x}, {y}) with button {button}'
				return ActionResult(extracted_content=msg, include_in_memory=True, long_term_memory=msg)

			case 'scroll':
				x, y = action.x, action.y
				scroll_x, scroll_y = action.scroll_x, action.scroll_y
				print(f'Action: scroll at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})')

				# Move mouse to position first
				await browser_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseMoved',
						'x': x,
						'y': y,
					},
					session_id=cdp_session.session_id,
				)

				# Execute scroll using JavaScript
				await browser_session.cdp_client.send.Runtime.evaluate(
					params={
						'expression': f'window.scrollBy({scroll_x}, {scroll_y})',
					},
					session_id=cdp_session.session_id,
				)
				msg = f'Scrolled at ({x}, {y}) with offsets (scroll_x={scroll_x}, scroll_y={scroll_y})'
				return ActionResult(extracted_content=msg, include_in_memory=True, long_term_memory=msg)

			case 'keypress':
				keys = action.keys
				for k in keys:
					print(f"Action: keypress '{k}'")
					# A simple mapping for common keys; expand as needed.
					key_code = k
					if k.lower() == 'enter':
						key_code = 'Enter'
					elif k.lower() == 'space':
						key_code = 'Space'

					# Use CDP to send key
					await browser_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyDown',
							'key': key_code,
						},
						session_id=cdp_session.session_id,
					)
					await browser_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'keyUp',
							'key': key_code,
						},
						session_id=cdp_session.session_id,
					)
				msg = f'Pressed keys: {keys}'
				return ActionResult(extracted_content=msg, include_in_memory=True, long_term_memory=msg)

			case 'type':
				text = action.text
				print(f'Action: type text: {text}')

				# Type text character by character
				for char in text:
					await browser_session.cdp_client.send.Input.dispatchKeyEvent(
						params={
							'type': 'char',
							'text': char,
						},
						session_id=cdp_session.session_id,
					)
				msg = f'Typed text: {text}'
				return ActionResult(extracted_content=msg, include_in_memory=True, long_term_memory=msg)

			case 'wait':
				print('Action: wait')
				await asyncio.sleep(2)
				msg = 'Waited for 2 seconds'
				return ActionResult(extracted_content=msg, include_in_memory=True, long_term_memory=msg)

			case 'screenshot':
				# Nothing to do as screenshot is taken at each turn
				print('Action: screenshot')
				return ActionResult(error=ERROR_MSG)
			# Handle other actions here

			case _:
				print(f'Unrecognized action: {action}')
				return ActionResult(error=ERROR_MSG)

	except Exception as e:
		print(f'Error handling action {action}: {e}')
		return ActionResult(error=ERROR_MSG)