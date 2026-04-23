async def test_structured_output_done_with_files_to_display(self, browser_session, base_url):
		"""Structured output done action resolves files_to_display into attachments."""

		class MyOutput(BaseModel):
			summary: str

		tools = Tools(output_model=MyOutput)

		with tempfile.TemporaryDirectory() as temp_dir:
			file_system = FileSystem(temp_dir)
			await file_system.write_file('report.txt', 'some report content')

			result = await tools.done(
				data={'summary': 'done'},
				success=True,
				files_to_display=['report.txt'],
				browser_session=browser_session,
				file_system=file_system,
			)

			assert isinstance(result, ActionResult)
			assert result.is_done is True
			assert result.success is True
			assert result.extracted_content is not None
			output = json.loads(result.extracted_content)
			assert output == {'summary': 'done'}
			assert result.attachments is not None
			assert len(result.attachments) == 1
			assert result.attachments[0].endswith('report.txt')