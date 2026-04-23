async def test_custom_action_with_no_arguments(self, browser_session, base_url):
		"""Test that custom actions with no arguments are handled correctly"""
		from browser_use.agent.views import ActionResult
		from browser_use.tools.registry.service import Registry

		# Create a registry
		registry = Registry()

		# Register a custom action with no arguments
		@registry.action('Some custom action with no args')
		def simple_action():
			return ActionResult(extracted_content='return some result')

		# Navigate to a test page
		from browser_use.browser.events import NavigateToUrlEvent

		event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/'))
		await event

		# Execute the action
		result = await registry.execute_action('simple_action', {})

		# Verify the result
		assert isinstance(result, ActionResult)
		assert result.extracted_content == 'return some result'

		# Test that the action model is created correctly
		action_model = registry.create_action_model()

		# The action should be in the model fields
		assert 'simple_action' in action_model.model_fields

		# Create an instance with the simple_action
		action_instance = action_model(simple_action={})  # type: ignore[call-arg]

		# Test that model_dump works correctly
		dumped = action_instance.model_dump(exclude_unset=True)
		assert 'simple_action' in dumped
		assert dumped['simple_action'] == {}

		# Test async version as well
		@registry.action('Async custom action with no args')
		async def async_simple_action():
			return ActionResult(extracted_content='async result')

		result = await registry.execute_action('async_simple_action', {})
		assert result.extracted_content == 'async result'

		# Test with special parameters but no regular arguments
		@registry.action('Action with only special params')
		async def special_params_only(browser_session):
			current_url = await browser_session.get_current_page_url()
			return ActionResult(extracted_content=f'Page URL: {current_url}')

		result = await registry.execute_action('special_params_only', {}, browser_session=browser_session)
		assert 'Page URL:' in result.extracted_content
		assert base_url in result.extracted_content