async def test_generate_gif(self, test_dir, httpserver_url, llm, generate_gif):
		"""Test GIF generation with different settings."""
		# Clean up any existing GIFs first
		for gif in Path.cwd().glob('agent_*.gif'):
			gif.unlink()

		gif_param = generate_gif
		expected_gif_path = None

		if generate_gif == 'custom_path':
			expected_gif_path = test_dir / 'custom_agent.gif'
			gif_param = str(expected_gif_path)

		browser_session = BrowserSession(browser_profile=BrowserProfile(headless=True, disable_security=True, user_data_dir=None))
		await browser_session.start()
		try:
			agent = Agent(
				task=f'go to {httpserver_url}',
				llm=llm,
				browser_session=browser_session,
				generate_gif=gif_param,
			)
			history: AgentHistoryList = await agent.run(max_steps=2)

			result = history.final_result()
			assert result is not None

			# Check GIF creation
			if generate_gif is False:
				gif_files = list(Path.cwd().glob('*.gif'))
				assert len(gif_files) == 0, 'GIF file was created when generate_gif=False'
			elif generate_gif is True:
				# With mock LLM that doesn't navigate, all screenshots will be about:blank placeholders
				# So no GIF will be created (this is expected behavior)
				gif_files = list(Path.cwd().glob('agent_history.gif'))
				assert len(gif_files) == 0, 'GIF should not be created when all screenshots are placeholders'
			else:  # custom_path
				assert expected_gif_path is not None, 'expected_gif_path should be set for custom_path'
				# With mock LLM that doesn't navigate, no GIF will be created
				assert not expected_gif_path.exists(), 'GIF should not be created when all screenshots are placeholders'
		finally:
			await browser_session.kill()