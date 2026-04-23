def test_file_content_operations(self):
		"""Test content update and append operations."""
		file_obj = TxtFile(name='test')

		# Initial content
		assert file_obj.content == ''
		assert file_obj.get_size == 0

		# Write content
		file_obj.write_file_content('First line')
		assert file_obj.content == 'First line'
		assert file_obj.get_size == 10

		# Append content
		file_obj.append_file_content('\nSecond line')
		assert file_obj.content == 'First line\nSecond line'
		assert file_obj.get_line_count == 2

		# Update content
		file_obj.update_content('New content')
		assert file_obj.content == 'New content'