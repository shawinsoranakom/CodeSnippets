async def test_structured_extraction_returns_json(self, browser_session, base_url):
		"""When output_schema is provided, extract returns structured JSON in <structured_result> tags."""
		tools = Tools()
		await tools.navigate(url=f'{base_url}/products', new_tab=False, browser_session=browser_session)
		await asyncio.sleep(0.5)

		output_schema = {
			'type': 'object',
			'properties': {
				'products': {
					'type': 'array',
					'items': {
						'type': 'object',
						'properties': {
							'name': {'type': 'string'},
							'price': {'type': 'number'},
						},
						'required': ['name', 'price'],
					},
				},
			},
			'required': ['products'],
		}

		mock_data = {'products': [{'name': 'Widget A', 'price': 9.99}, {'name': 'Widget B', 'price': 19.99}]}
		extraction_llm = _make_extraction_llm(structured_response=mock_data)

		with tempfile.TemporaryDirectory() as tmp:
			fs = FileSystem(tmp)
			result = await tools.extract(
				query='List all products with prices',
				output_schema=output_schema,
				browser_session=browser_session,
				page_extraction_llm=extraction_llm,
				file_system=fs,
			)

		assert isinstance(result, ActionResult)
		assert result.extracted_content is not None
		assert '<structured_result>' in result.extracted_content
		assert '</structured_result>' in result.extracted_content

		# Parse the JSON out of the tags
		start = result.extracted_content.index('<structured_result>') + len('<structured_result>')
		end = result.extracted_content.index('</structured_result>')
		parsed = json.loads(result.extracted_content[start:end].strip())
		assert parsed == mock_data

		# Metadata
		assert result.metadata is not None
		assert result.metadata['structured_extraction'] is True
		meta = result.metadata['extraction_result']
		assert meta['data'] == mock_data
		assert meta['schema_used'] == output_schema