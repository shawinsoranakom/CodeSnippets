async def test_switch_tab_operations(self, browser_session, base_url):
		"""Test tab creation, switching, and closing operations."""
		# Navigate to home page in first tab
		from browser_use.browser.events import NavigateToUrlEvent

		event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=f'{base_url}/'))
		await event

		# Create a new tab
		await browser_session.create_new_tab(f'{base_url}/scroll_test')

		# Verify we have two tabs now
		tabs_info = await browser_session.get_tabs()
		assert len(tabs_info) == 2, 'Should have two tabs open'

		# Verify current tab is the scroll test page
		current_url = await browser_session.get_current_page_url()
		assert f'{base_url}/scroll_test' in current_url

		# Switch back to the first tab
		await browser_session.switch_to_tab(0)

		# Verify we're back on the home page
		current_url = await browser_session.get_current_page_url()
		assert f'{base_url}/' in current_url

		# Close the second tab
		await browser_session.close_tab(1)

		# Verify we have the expected number of tabs
		# The first tab remains plus any about:blank tabs created by AboutBlankWatchdog
		tabs_info = await browser_session.get_tabs_info()
		# Filter out about:blank tabs created by the watchdog
		non_blank_tabs = [tab for tab in tabs_info if 'about:blank' not in tab.url]
		assert len(non_blank_tabs) == 1, (
			f'Should have one non-blank tab open after closing the second, but got {len(non_blank_tabs)}: {non_blank_tabs}'
		)
		assert base_url in non_blank_tabs[0].url, 'The remaining tab should be the home page'