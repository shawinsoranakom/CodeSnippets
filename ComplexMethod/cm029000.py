async def test_radio_group_switching(self, tools: Tools, browser_session: BrowserSession, base_url: str):
		"""Click one radio then another in the same group; first should uncheck."""
		await tools.navigate(url=f'{base_url}/radio-sibling', new_tab=False, browser_session=browser_session)
		await browser_session.get_browser_state_summary()

		# Click red first
		red_idx = await browser_session.get_index_by_id('radio-red')
		assert red_idx is not None
		result = await tools.click(index=red_idx, browser_session=browser_session)
		assert result.error is None, f'Click red failed: {result.error}'

		is_red_checked, _ = await _get_checked_and_result(browser_session, 'radio-red')
		assert is_red_checked, 'radio-red should be checked'

		# Re-fetch state so indices are current, then click green
		await browser_session.get_browser_state_summary()
		green_idx = await browser_session.get_index_by_id('radio-green')
		assert green_idx is not None
		result = await tools.click(index=green_idx, browser_session=browser_session)
		assert result.error is None, f'Click green failed: {result.error}'

		is_green_checked, result_text = await _get_checked_and_result(browser_session, 'radio-green')
		assert is_green_checked, 'radio-green should be checked'
		assert 'selected:green' in result_text

		# Verify red is now unchecked
		is_red_checked, _ = await _get_checked_and_result(browser_session, 'radio-red')
		assert not is_red_checked, 'radio-red should be unchecked after selecting green'