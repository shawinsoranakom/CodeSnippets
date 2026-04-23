async def test_nested_selectors(self, tools, browser_session, base_url):
		"""Nested CSS selectors (child combinator) work correctly."""
		await _navigate_and_wait(tools, browser_session, f'{base_url}/articles')

		result = await tools.find_elements(
			selector='article a.read-more',
			attributes=['href'],
			browser_session=browser_session,
		)

		assert isinstance(result, ActionResult)
		assert result.error is None
		assert result.extracted_content is not None
		assert '3 elements' in result.extracted_content
		assert '/articles/python' in result.extracted_content
		assert '/articles/javascript' in result.extracted_content
		assert '/articles/css' in result.extracted_content