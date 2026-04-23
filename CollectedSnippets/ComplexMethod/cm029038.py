async def test_google_sheets_style_calling_pattern(self, registry, browser_session):
		"""Test the specific pattern from Google Sheets actions that causes the error"""

		# Simulate the _select_cell_or_range helper function
		async def _select_cell_or_range(browser_session: BrowserSession, cell_or_range: str):
			url = await browser_session.get_current_page_url()
			return ActionResult(extracted_content=f'Selected cell {cell_or_range} on {url}')

		@registry.action('Select cell or range')
		async def select_cell_or_range(cell_or_range: str, browser_session: BrowserSession):
			# This pattern now works with kwargs
			return await _select_cell_or_range(browser_session=browser_session, cell_or_range=cell_or_range)

		@registry.action('Select cell or range (fixed)')
		async def select_cell_or_range_fixed(cell_or_range: str, browser_session: BrowserSession):
			# This pattern also works
			return await _select_cell_or_range(browser_session, cell_or_range)

		@registry.action('Update range contents')
		async def update_range_contents(range_name: str, new_contents: str, browser_session: BrowserSession):
			# This action calls select_cell_or_range, simulating the real Google Sheets pattern
			# Get the action's param model to call it properly
			action = registry.registry.actions['select_cell_or_range_fixed']
			params = action.param_model(cell_or_range=range_name)
			await select_cell_or_range_fixed(cell_or_range=range_name, browser_session=browser_session)
			return ActionResult(extracted_content=f'Updated range {range_name} with {new_contents}')

		# Test the fixed version (should work)
		result_fixed = await registry.execute_action(
			'select_cell_or_range_fixed', {'cell_or_range': 'A1:F100'}, browser_session=browser_session
		)
		assert result_fixed.extracted_content is not None
		assert 'Selected cell A1:F100 on' in result_fixed.extracted_content
		assert '/test' in result_fixed.extracted_content

		# Test the chained calling pattern
		result_chain = await registry.execute_action(
			'update_range_contents', {'range_name': 'B2:D4', 'new_contents': 'test data'}, browser_session=browser_session
		)
		assert result_chain.extracted_content is not None
		assert 'Updated range B2:D4 with test data' in result_chain.extracted_content

		# Test the problematic version (should work with enhanced registry)
		result_problematic = await registry.execute_action(
			'select_cell_or_range', {'cell_or_range': 'A1:F100'}, browser_session=browser_session
		)
		# With the enhanced registry, this should succeed
		assert result_problematic.extracted_content is not None
		assert 'Selected cell A1:F100 on' in result_problematic.extracted_content
		assert '/test' in result_problematic.extracted_content