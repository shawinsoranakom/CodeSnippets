async def test_wait_action(self, tools, browser_session):
		"""Test that the wait action correctly waits for the specified duration."""

		# verify that it's in the default action set
		wait_action = None
		for action_name, action in tools.registry.registry.actions.items():
			if 'wait' in action_name.lower() and 'seconds' in str(action.param_model.model_fields):
				wait_action = action
				break
		assert wait_action is not None, 'Could not find wait action in tools'

		# Check that it has seconds parameter with default
		assert 'seconds' in wait_action.param_model.model_fields
		schema = wait_action.param_model.model_json_schema()
		assert schema['properties']['seconds']['default'] == 3

		# Record start time
		start_time = time.time()

		# Execute wait action
		result = await tools.wait(seconds=3, browser_session=browser_session)

		# Record end time
		end_time = time.time()

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None
		assert 'Waited for' in result.extracted_content or 'Waiting for' in result.extracted_content

		# Verify that approximately 1 second has passed (allowing some margin)
		assert end_time - start_time <= 2.5  # We wait 3-1 seconds for LLM call

		# longer wait
		# Record start time
		start_time = time.time()

		# Execute wait action
		result = await tools.wait(seconds=5, browser_session=browser_session)

		# Record end time
		end_time = time.time()

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None
		assert 'Waited for' in result.extracted_content or 'Waiting for' in result.extracted_content

		assert 3.5 <= end_time - start_time <= 4.5