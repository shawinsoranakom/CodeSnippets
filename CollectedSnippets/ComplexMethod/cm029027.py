async def test_write_jsonl_file(self, temp_filesystem):
		"""Test writing JSONL (JSON Lines) files."""
		fs = temp_filesystem

		# Write valid JSONL content
		jsonl_content = '{"id": 1, "name": "John", "age": 30}\n{"id": 2, "name": "Jane", "age": 25}'
		result = await fs.write_file('data.jsonl', jsonl_content)
		assert result == 'Data written to file data.jsonl successfully.'

		# Verify content was written
		content = await fs.read_file('data.jsonl')
		assert jsonl_content in content

		# Verify file object was created
		assert 'data.jsonl' in fs.files
		file_obj = fs.get_file('data.jsonl')
		assert file_obj is not None
		assert isinstance(file_obj, JsonlFile)
		assert file_obj.content == jsonl_content

		# Write to new JSONL file
		result = await fs.write_file('WebVoyager_data.jsonl', '{"task": "test", "url": "https://example.com"}')
		assert result == 'Data written to file WebVoyager_data.jsonl successfully.'
		assert 'WebVoyager_data.jsonl' in fs.files