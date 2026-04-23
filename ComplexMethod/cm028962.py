async def test_done_action(self, tools, browser_session, base_url):
		"""Test that DoneAction completes a task and reports success or failure."""
		# Create a temporary directory for the file system
		with tempfile.TemporaryDirectory() as temp_dir:
			file_system = FileSystem(temp_dir)

			# First navigate to a page
			await tools.navigate(url=f'{base_url}/page1', new_tab=False, browser_session=browser_session)

			success_done_message = 'Successfully completed task'

			# Execute done action with file_system
			result = await tools.done(
				text=success_done_message, success=True, browser_session=browser_session, file_system=file_system
			)

			# Verify the result
			assert isinstance(result, ActionResult)
			assert result.extracted_content is not None
			assert success_done_message in result.extracted_content
			assert result.success is True
			assert result.is_done is True
			assert result.error is None

			failed_done_message = 'Failed to complete task'

			# Execute failed done action with file_system
			result = await tools.done(
				text=failed_done_message, success=False, browser_session=browser_session, file_system=file_system
			)

			# Verify the result
			assert isinstance(result, ActionResult)
			assert result.extracted_content is not None
			assert failed_done_message in result.extracted_content
			assert result.success is False
			assert result.is_done is True
			assert result.error is None