async def test_save_as_pdf_default_filename(self, tools, browser_session, base_url):
		"""save_as_pdf with no filename uses the page title."""
		await tools.navigate(url=f'{base_url}/pdf-test', new_tab=False, browser_session=browser_session)
		await asyncio.sleep(0.5)

		with tempfile.TemporaryDirectory() as temp_dir:
			file_system = FileSystem(temp_dir)
			result = await tools.save_as_pdf(browser_session=browser_session, file_system=file_system)

			assert isinstance(result, ActionResult)
			assert result.extracted_content is not None
			assert 'Saved page as PDF' in result.extracted_content

			attachments = _get_attachments(result)
			assert len(attachments) == 1

			pdf_path = attachments[0]
			assert pdf_path.endswith('.pdf')
			assert await anyio.Path(pdf_path).exists()

			# Verify it's actually a PDF (starts with %PDF magic bytes)
			header = await anyio.Path(pdf_path).read_bytes()
			assert header[:5] == b'%PDF-', f'File does not start with PDF magic bytes: {header[:5]!r}'