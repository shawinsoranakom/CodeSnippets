async def test_read_external_png_image(self, tmp_path: Path):
		"""Test reading external PNG image file."""
		# Create an external image file
		external_file = tmp_path / 'test.png'
		img_bytes = self.create_test_image(width=300, height=200, format='PNG')
		external_file.write_bytes(img_bytes)

		fs = FileSystem(tmp_path / 'workspace')
		structured_result = await fs.read_file_structured(str(external_file), external_file=True)

		assert 'message' in structured_result
		assert 'Read image file' in structured_result['message']
		assert 'images' in structured_result
		assert structured_result['images'] is not None
		assert len(structured_result['images']) == 1

		img_data = structured_result['images'][0]
		assert img_data['name'] == 'test.png'
		assert 'data' in img_data
		# Verify base64 is valid
		decoded = base64.b64decode(img_data['data'])
		assert decoded == img_bytes