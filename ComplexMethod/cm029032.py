async def test_write_file_auto_sanitizes(self):
		"""Test that write_file auto-sanitizes invalid filenames and includes a notice."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			fs = FileSystem(base_dir=tmp_dir, create_default_files=False)

			# Filename with special chars should be auto-sanitized with notice
			result = await fs.write_file('test@file.md', 'content')
			assert 'successfully' in result
			assert 'auto-corrected' in result
			assert 'testfile.md' in result

			# Filename with spaces - spaces are valid, so no sanitization needed
			result = await fs.write_file('my file.txt', 'content')
			assert 'successfully' in result

			# Verify the sanitized file can be read back
			content = await fs.read_file('testfile.md')
			assert 'content' in content

			# Verify reading with the original invalid name also works (via sanitization)
			content = await fs.read_file('test@file.md')
			assert 'content' in content
			assert 'auto-corrected' in content

			fs.nuke()