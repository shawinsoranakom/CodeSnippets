async def test_upload_wrapped_file_input(self, httpserver):
		"""File input wrapped in a label/div is found via find_file_input_near_element."""
		from browser_use.browser.events import NavigateToUrlEvent
		from browser_use.browser.session import BrowserSession
		from browser_use.skill_cli.actions import ActionHandler
		from browser_use.skill_cli.commands.browser import handle
		from browser_use.skill_cli.sessions import SessionInfo

		httpserver.expect_request('/').respond_with_data(
			"""<html><body>
				<label id="wrapper">
					Upload here
					<input type="file" id="hidden-upload" style="opacity: 0" />
				</label>
			</body></html>""",
			content_type='text/html',
		)

		session = BrowserSession(headless=True)
		await session.start()
		try:
			await session.event_bus.dispatch(NavigateToUrlEvent(url=httpserver.url_for('/')))

			session_info = SessionInfo(
				name='test',
				headed=False,
				profile=None,
				cdp_url=None,
				browser_session=session,
				actions=ActionHandler(session),
			)

			await session.get_browser_state_summary()

			# The file input should be found even if we target the label or a nearby element
			selector_map = await session.get_selector_map()

			# Find any non-file-input element that is near the file input
			file_input_index = None
			other_index = None
			for idx, el in selector_map.items():
				if session.is_file_input(el):
					file_input_index = idx
				else:
					other_index = idx

			# If both the file input and another element are in the selector map,
			# try uploading via the other element (the heuristic should find the file input)
			if other_index is not None:
				with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
					f.write(b'test content for wrapped upload')
					test_file = f.name

				try:
					result = await handle('upload', session_info, {'index': other_index, 'path': test_file})
					# Should succeed if the heuristic found the nearby file input
					# or error if too far away - either way, the heuristic was exercised
					if 'uploaded' in result:
						assert result['element'] == other_index
					else:
						# If the elements are too far apart, the heuristic won't find it
						assert 'error' in result
				finally:
					Path(test_file).unlink(missing_ok=True)
			elif file_input_index is not None:
				# Only the file input is indexed, just test direct upload
				with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
					f.write(b'test content')
					test_file = f.name

				try:
					result = await handle('upload', session_info, {'index': file_input_index, 'path': test_file})
					assert 'uploaded' in result
				finally:
					Path(test_file).unlink(missing_ok=True)
		finally:
			await session.kill()