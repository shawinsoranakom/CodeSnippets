async def test_save_extracted_content(self, temp_filesystem):
		"""Test saving extracted content with auto-numbering."""
		fs = temp_filesystem

		# Save first extracted content
		result = await fs.save_extracted_content('First extracted content')
		assert result == 'extracted_content_0.md'
		assert 'extracted_content_0.md' in fs.files
		assert fs.extracted_content_count == 1

		# Save second extracted content
		result = await fs.save_extracted_content('Second extracted content')
		assert result == 'extracted_content_1.md'
		assert 'extracted_content_1.md' in fs.files
		assert fs.extracted_content_count == 2

		# Verify content
		content1 = fs.get_file('extracted_content_0.md').content
		content2 = fs.get_file('extracted_content_1.md').content
		assert content1 == 'First extracted content'
		assert content2 == 'Second extracted content'