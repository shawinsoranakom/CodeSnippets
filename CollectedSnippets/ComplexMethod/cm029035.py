async def test_concurrent_operations(self):
		"""Test concurrent file operations."""
		with tempfile.TemporaryDirectory() as tmp_dir:
			fs = FileSystem(base_dir=tmp_dir, create_default_files=False)

			# Create multiple files concurrently
			tasks = []
			for i in range(5):
				tasks.append(fs.write_file(f'file_{i}.md', f'Content for file {i}'))

			# Wait for all operations to complete
			results = await asyncio.gather(*tasks)

			# Verify all operations succeeded
			for result in results:
				assert 'successfully' in result

			# Verify all files were created
			assert len(fs.files) == 5
			for i in range(5):
				assert f'file_{i}.md' in fs.files
				file_obj = fs.get_file(f'file_{i}.md')
				assert file_obj is not None
				assert file_obj.content == f'Content for file {i}'

			fs.nuke()