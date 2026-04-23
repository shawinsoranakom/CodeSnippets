async def test_from_state(self, temp_filesystem):
		"""Test restoring filesystem from state."""
		fs = temp_filesystem

		# Add some content
		await fs.write_file('results.md', '# Original Results')
		await fs.write_file('custom.txt', 'Custom content')
		await fs.save_extracted_content('Extracted data')

		# Get state
		state = fs.get_state()

		# Create new filesystem from state
		fs2 = FileSystem.from_state(state)

		# Verify restoration
		assert fs2.base_dir == fs.base_dir
		assert fs2.extracted_content_count == fs.extracted_content_count
		assert len(fs2.files) == len(fs.files)

		# Verify file contents
		file_obj = fs2.get_file('results.md')
		assert file_obj is not None
		assert file_obj.content == '# Original Results'
		file_obj = fs2.get_file('custom.txt')
		assert file_obj is not None
		assert file_obj.content == 'Custom content'
		file_obj = fs2.get_file('extracted_content_0.md')
		assert file_obj is not None
		assert file_obj.content == 'Extracted data'

		# Verify files exist on disk
		assert (fs2.data_dir / 'results.md').exists()
		assert (fs2.data_dir / 'custom.txt').exists()
		assert (fs2.data_dir / 'extracted_content_0.md').exists()

		# Clean up second filesystem
		fs2.nuke()