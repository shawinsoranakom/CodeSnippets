async def openai_cua_fallback(params: OpenAICUAAction, browser_session: BrowserSession):
	"""
	Fallback action that uses OpenAI's Computer Use Assistant to perform complex
	computer interactions when standard browser actions are insufficient.
	"""
	print(f'🎯 CUA Action Starting - Goal: {params.description}')

	try:
		# Get browser state summary
		state = await browser_session.get_browser_state_summary()
		page_info = state.page_info
		if not page_info:
			raise Exception('Page info not found - cannot execute CUA action')

		print(f'📐 Viewport size: {page_info.viewport_width}x{page_info.viewport_height}')

		screenshot_b64 = state.screenshot
		if not screenshot_b64:
			raise Exception('Screenshot not found - cannot execute CUA action')

		print(f'📸 Screenshot captured (base64 length: {len(screenshot_b64)} chars)')

		# Debug: Check screenshot dimensions
		image = Image.open(BytesIO(base64.b64decode(screenshot_b64)))
		print(f'📏 Screenshot actual dimensions: {image.size[0]}x{image.size[1]}')

		# rescale the screenshot to the viewport size
		image = image.resize((page_info.viewport_width, page_info.viewport_height))
		# Save as PNG to bytes buffer
		buffer = BytesIO()
		image.save(buffer, format='PNG')
		buffer.seek(0)
		# Convert to base64
		screenshot_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
		print(f'📸 Rescaled screenshot to viewport size: {page_info.viewport_width}x{page_info.viewport_height}')

		client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
		print('🔄 Sending request to OpenAI CUA...')

		prompt = f"""
        You will be given an action to execute and screenshot of the current screen. 
        Output one computer_call object that will achieve this goal.
        Goal: {params.description}
        """
		response = await client.responses.create(
			model='computer-use-preview',
			tools=[
				{
					'type': 'computer_use_preview',
					'display_width': page_info.viewport_width,
					'display_height': page_info.viewport_height,
					'environment': 'browser',
				}
			],
			input=[
				{
					'role': 'user',
					'content': [
						{'type': 'input_text', 'text': prompt},
						{
							'type': 'input_image',
							'detail': 'auto',
							'image_url': f'data:image/png;base64,{screenshot_b64}',
						},
					],
				}
			],
			truncation='auto',
			temperature=0.1,
		)

		print(f'📥 CUA response received: {response}')
		computer_calls = [item for item in response.output if item.type == 'computer_call']
		computer_call = computer_calls[0] if computer_calls else None
		if not computer_call:
			raise Exception('No computer calls found in CUA response')

		action = computer_call.action
		print(f'🎬 Executing CUA action: {action.type} - {action}')

		action_result = await handle_model_action(browser_session, action)
		await asyncio.sleep(0.1)

		print('✅ CUA action completed successfully')
		return action_result

	except Exception as e:
		msg = f'Error executing CUA action: {e}'
		print(f'❌ {msg}')
		return ActionResult(error=msg)