async def test_img_src_attribute_resolved(self, tools, browser_session, base_url):
		"""find_elements with attributes=['src'] returns absolute URLs for img elements."""
		await _navigate_and_wait(tools, browser_session, f'{base_url}/images-page')

		result = await tools.find_elements(
			selector='img',
			attributes=['src'],
			browser_session=browser_session,
		)

		assert isinstance(result, ActionResult)
		assert result.error is None
		assert result.extracted_content is not None
		assert '1 element' in result.extracted_content
		assert 'src=' in result.extracted_content
		# The resolved DOM property should give the absolute URL (including the httpserver base URL)
		assert base_url in result.extracted_content
		assert 'product.jpg' in result.extracted_content