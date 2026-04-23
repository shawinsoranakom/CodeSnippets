def test_filename_validation(self, temp_filesystem):
		"""Test filename validation."""
		fs = temp_filesystem

		# Valid filenames - basic
		assert fs._is_valid_filename('test.md') is True
		assert fs._is_valid_filename('my_file.txt') is True
		assert fs._is_valid_filename('file-name.md') is True
		assert fs._is_valid_filename('file123.txt') is True
		assert fs._is_valid_filename('data.json') is True
		assert fs._is_valid_filename('data.jsonl') is True
		assert fs._is_valid_filename('users.csv') is True
		assert fs._is_valid_filename('WebVoyager_data.jsonl') is True  # with underscores

		# Valid filenames - dots in name part
		assert fs._is_valid_filename('report.v2.md') is True  # dots in name
		assert fs._is_valid_filename('file.backup.2024.csv') is True  # multiple dots in name
		assert fs._is_valid_filename('useAppStore.json') is True  # camelCase with dot-like extension

		# Valid filenames - spaces and parentheses
		assert fs._is_valid_filename('test with spaces.md') is True  # spaces allowed
		assert fs._is_valid_filename('report (1).csv') is True  # parentheses allowed
		assert fs._is_valid_filename('my file (copy).txt') is True  # spaces and parens

		# Valid filenames - new extensions
		assert fs._is_valid_filename('page.html') is True
		assert fs._is_valid_filename('config.xml') is True

		# Invalid filenames
		assert fs._is_valid_filename('test.doc') is False  # wrong extension
		assert fs._is_valid_filename('test') is False  # no extension
		assert fs._is_valid_filename('test@file.md') is False  # special chars (@)
		assert fs._is_valid_filename('.md') is False  # no name
		assert fs._is_valid_filename('.json') is False  # no name
		assert fs._is_valid_filename('.jsonl') is False  # no name
		assert fs._is_valid_filename('.csv') is False  # no name
		assert fs._is_valid_filename('screenshot.png') is False  # binary extension
		assert fs._is_valid_filename('image.jpg') is False