async def test_write_file(self, temp_filesystem):
		"""Test writing content to files."""
		fs = temp_filesystem

		# Write to existing file
		result = await fs.write_file('results.md', '# Test Results\nThis is a test.')
		assert result == 'Data written to file results.md successfully.'

		# Verify content was written
		content = await fs.read_file('results.md')
		assert '# Test Results\nThis is a test.' in content

		# Write to new file
		result = await fs.write_file('new_file.txt', 'New file content')
		assert result == 'Data written to file new_file.txt successfully.'
		assert 'new_file.txt' in fs.files
		assert fs.get_file('new_file.txt').content == 'New file content'

		# Write with special chars in filename - auto-sanitized to 'invalidname.md'
		result = await fs.write_file('invalid@name.md', 'content')
		assert 'successfully' in result
		assert 'auto-corrected' in result
		assert 'invalidname.md' in result

		# Write with unsupported extension - gives specific error
		result = await fs.write_file('test.doc', 'content')
		assert 'Unsupported file extension' in result