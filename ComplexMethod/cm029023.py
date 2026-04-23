def test_filename_parsing(self, temp_filesystem):
		"""Test filename parsing into name and extension."""
		fs = temp_filesystem

		name, ext = fs._parse_filename('test.md')
		assert name == 'test'
		assert ext == 'md'

		name, ext = fs._parse_filename('my_file.TXT')
		assert name == 'my_file'
		assert ext == 'txt'  # Should be lowercased

		name, ext = fs._parse_filename('data.json')
		assert name == 'data'
		assert ext == 'json'

		name, ext = fs._parse_filename('users.CSV')
		assert name == 'users'
		assert ext == 'csv'