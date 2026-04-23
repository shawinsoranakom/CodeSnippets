async def test_complete_workflow(self):
		"""Test a complete filesystem workflow."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			# Create filesystem
			fs = FileSystem(base_dir=tmp_dir, create_default_files=True)

			# Write to results file
			await fs.write_file('results.md', '# Test Results\n## Section 1\nInitial results.')

			# Append more content
			await fs.append_file('results.md', '\n## Section 2\nAdditional findings.')

			# Create a notes file
			await fs.write_file('notes.txt', 'Important notes:\n- Note 1\n- Note 2')

			# Save extracted content
			await fs.save_extracted_content('Extracted data from web page')
			await fs.save_extracted_content('Second extraction')

			# Verify file listing
			files = fs.list_files()
			assert len(files) == 5  # results.md, todo.md, notes.txt, 2 extracted files

			# Verify content
			file_obj = fs.get_file('results.md')
			assert file_obj is not None
			results_content = file_obj.content
			assert '# Test Results' in results_content
			assert '## Section 1' in results_content
			assert '## Section 2' in results_content
			assert 'Additional findings.' in results_content

			# Test state persistence
			state = fs.get_state()
			fs.nuke()

			# Restore from state
			fs2 = FileSystem.from_state(state)

			# Verify restoration
			assert len(fs2.files) == 5
			file_obj = fs2.get_file('results.md')
			assert file_obj is not None
			assert file_obj.content == results_content
			file_obj = fs2.get_file('notes.txt')
			assert file_obj is not None
			assert file_obj.content == 'Important notes:\n- Note 1\n- Note 2'
			assert fs2.extracted_content_count == 2

			# Verify files exist on disk
			for filename in files:
				assert (fs2.data_dir / filename).exists()

			fs2.nuke()