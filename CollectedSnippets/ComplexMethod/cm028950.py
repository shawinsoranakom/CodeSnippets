def test_parse_agent_history_list_with_generic_parameter(self):
		"""Test parsing AgentHistoryList[ExtractedData] preserves output model schema"""
		data = {
			'history': [
				{
					'model_output': None,
					'result': [{'extracted_content': '{"title": "Test", "price": 9.99, "in_stock": true}', 'is_done': True}],
					'state': {'url': 'https://example.com', 'title': 'Test', 'tabs': []},
				}
			]
		}

		# Parse with generic type annotation
		result = _parse_with_type_annotation(data, AgentHistoryList[ExtractedData])

		assert isinstance(result, AgentHistoryList)
		assert len(result.history) == 1
		# With generic, _output_model_schema should be set
		assert result._output_model_schema is ExtractedData

		# Now structured_output property should work
		structured = result.structured_output
		assert structured is not None
		assert isinstance(structured, ExtractedData)
		assert structured.title == 'Test'
		assert structured.price == 9.99
		assert structured.in_stock is True