async def test_image_end_to_end(self, tmp_path: Path):
		"""Test complete flow: external image → FileSystem → ActionResult → MessageManager → Prompt."""
		# Step 1: Create external image
		external_file = tmp_path / 'photo.png'
		img_bytes = self.create_test_image()
		external_file.write_bytes(img_bytes)

		# Step 2: Read via FileSystem
		fs = FileSystem(tmp_path / 'workspace')
		structured_result = await fs.read_file_structured(str(external_file), external_file=True)

		assert structured_result['images'] is not None

		# Step 3: Create ActionResult (simulating tools/service.py)
		action_result = ActionResult(
			extracted_content=structured_result['message'],
			long_term_memory='Read image file photo.png',
			images=structured_result['images'],
			include_extracted_content_only_once=True,
		)

		# Step 4: Process in MessageManager
		system_message = SystemMessage(content='Test system message')
		mm = MessageManager(task='test', system_message=system_message, file_system=fs)
		step_info = AgentStepInfo(step_number=1, max_steps=10)
		mm._update_agent_history_description(model_output=None, result=[action_result], step_info=step_info)

		# Verify images stored
		assert len(mm.state.read_state_images) == 1
		assert mm.state.read_state_images[0]['name'] == 'photo.png'

		# Step 5: Create message with AgentMessagePrompt
		browser_state = BrowserStateSummary(
			url='https://example.com',
			title='Test',
			tabs=[TabInfo(target_id='test-0', url='https://example.com', title='Test')],
			screenshot=None,
			dom_state=SerializedDOMState(_root=None, selector_map={}),
		)

		prompt = AgentMessagePrompt(
			browser_state_summary=browser_state,
			file_system=fs,
			read_state_images=mm.state.read_state_images,
		)

		user_message = prompt.get_user_message(use_vision=True)

		# Verify image is in message
		assert isinstance(user_message.content, list)
		image_parts = [part for part in user_message.content if isinstance(part, ContentPartImageParam)]
		assert len(image_parts) >= 1

		# Verify image data is correct
		base64_str = base64.b64encode(img_bytes).decode('utf-8')
		assert base64_str in image_parts[0].image_url.url