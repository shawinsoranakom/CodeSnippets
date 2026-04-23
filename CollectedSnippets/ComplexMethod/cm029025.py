async def test_write_json_file(self, temp_filesystem):
		"""Test writing JSON files."""
		fs = temp_filesystem

		# Write valid JSON content
		json_content = '{"users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]}'
		result = await fs.write_file('data.json', json_content)
		assert result == 'Data written to file data.json successfully.'

		# Verify content was written
		content = await fs.read_file('data.json')
		assert json_content in content

		# Verify file object was created
		assert 'data.json' in fs.files
		file_obj = fs.get_file('data.json')
		assert file_obj is not None
		assert isinstance(file_obj, JsonFile)
		assert file_obj.content == json_content

		# Write to new JSON file
		result = await fs.write_file('config.json', '{"debug": true, "port": 8080}')
		assert result == 'Data written to file config.json successfully.'
		assert 'config.json' in fs.files