def test_agent_message_prompt_includes_images(self, tmp_path: Path):
		"""Test that AgentMessagePrompt includes images in message content."""
		fs = FileSystem(tmp_path)

		# Create browser state
		browser_state = BrowserStateSummary(
			url='https://example.com',
			title='Test',
			tabs=[TabInfo(target_id='test-0', url='https://example.com', title='Test')],
			screenshot=None,
			dom_state=SerializedDOMState(_root=None, selector_map={}),
		)

		# Create images
		read_state_images = [{'name': 'test.png', 'data': 'base64_image_data_here'}]

		# Create message prompt
		prompt = AgentMessagePrompt(
			browser_state_summary=browser_state,
			file_system=fs,
			read_state_images=read_state_images,
		)

		# Get user message with vision enabled
		user_message = prompt.get_user_message(use_vision=True)

		# Verify message has content parts (not just string)
		assert isinstance(user_message.content, list)

		# Find image content parts
		image_parts = [part for part in user_message.content if isinstance(part, ContentPartImageParam)]
		text_parts = [part for part in user_message.content if isinstance(part, ContentPartTextParam)]

		# Should have at least one image
		assert len(image_parts) >= 1

		# Should have text label
		image_labels = [part.text for part in text_parts if 'test.png' in part.text]
		assert len(image_labels) >= 1

		# Verify image data URL format
		img_part = image_parts[0]
		assert 'data:image/' in img_part.image_url.url
		assert 'base64,base64_image_data_here' in img_part.image_url.url