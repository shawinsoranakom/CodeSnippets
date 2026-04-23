async def test_structured_output_done_auto_attaches_downloads(self, browser_session, base_url):
		"""Session downloads are auto-attached even without files_to_display."""

		class MyOutput(BaseModel):
			url: str

		tools = Tools(output_model=MyOutput)

		with tempfile.TemporaryDirectory() as temp_dir:
			file_system = FileSystem(temp_dir)

			# Simulate a CDP-tracked browser download
			fake_download = os.path.join(temp_dir, 'tax-bill.pdf')
			await anyio.Path(fake_download).write_bytes(b'%PDF-1.4 fake pdf content')

			saved_downloads = browser_session._downloaded_files.copy()
			browser_session._downloaded_files.append(fake_download)
			try:
				result = await tools.done(
					data={'url': f'{base_url}/bill.pdf'},
					success=True,
					browser_session=browser_session,
					file_system=file_system,
				)

				assert isinstance(result, ActionResult)
				assert result.is_done is True
				assert result.extracted_content is not None
				output = json.loads(result.extracted_content)
				assert output == {'url': f'{base_url}/bill.pdf'}
				# The download should be auto-attached
				assert result.attachments is not None
				assert len(result.attachments) == 1
				assert result.attachments[0] == fake_download
			finally:
				browser_session._downloaded_files = saved_downloads