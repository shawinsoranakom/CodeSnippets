def update_browser_panel(self) -> None:
		"""Update browser information panel with details about the browser."""
		browser_info = self.query_one('#browser-info', RichLog)
		browser_info.clear()

		# Try to use the agent's browser session if available
		browser_session = self.browser_session
		if hasattr(self, 'agent') and self.agent and hasattr(self.agent, 'browser_session'):
			browser_session = self.agent.browser_session

		if browser_session:
			try:
				# Check if browser session has a CDP client
				if not hasattr(browser_session, 'cdp_client') or browser_session.cdp_client is None:
					browser_info.write('[yellow]Browser session created, waiting for browser to launch...[/]')
					return

				# Update our reference if we're using the agent's session
				if browser_session != self.browser_session:
					self.browser_session = browser_session

				# Get basic browser info from browser_profile
				browser_type = 'Chromium'
				headless = browser_session.browser_profile.headless

				# Determine connection type based on config
				connection_type = 'playwright'  # Default
				if browser_session.cdp_url:
					connection_type = 'CDP'
				elif browser_session.browser_profile.executable_path:
					connection_type = 'user-provided'

				# Get window size details from browser_profile
				window_width = None
				window_height = None
				if browser_session.browser_profile.viewport:
					window_width = browser_session.browser_profile.viewport.width
					window_height = browser_session.browser_profile.viewport.height

				# Try to get browser PID
				browser_pid = 'Unknown'
				connected = False
				browser_status = '[red]Disconnected[/]'

				try:
					# Check if browser PID is available
					# Check if we have a CDP client
					if browser_session.cdp_client is not None:
						connected = True
						browser_status = '[green]Connected[/]'
						browser_pid = 'N/A'
				except Exception as e:
					browser_pid = f'Error: {str(e)}'

				# Display browser information
				browser_info.write(f'[bold cyan]Chromium[/] Browser ({browser_status})')
				browser_info.write(
					f'Type: [yellow]{connection_type}[/] [{"green" if not headless else "red"}]{" (headless)" if headless else ""}[/]'
				)
				browser_info.write(f'PID: [dim]{browser_pid}[/]')
				browser_info.write(f'CDP Port: {browser_session.cdp_url}')

				if window_width and window_height:
					browser_info.write(f'Window: [blue]{window_width}[/] × [blue]{window_height}[/]')

				# Include additional information about the browser if needed
				if connected and hasattr(self, 'agent') and self.agent:
					try:
						# Show when the browser was connected
						timestamp = int(time.time())
						current_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
						browser_info.write(f'Last updated: [dim]{current_time}[/]')
					except Exception:
						pass

					# Show the agent's current page URL if available
					if browser_session.agent_focus_target_id:
						target = browser_session.session_manager.get_focused_target()
						target_url = target.url if target else 'about:blank'
						current_url = target_url.replace('https://', '').replace('http://', '').replace('www.', '')[:36] + '…'
						browser_info.write(f'👁️  [green]{current_url}[/]')
			except Exception as e:
				browser_info.write(f'[red]Error updating browser info: {str(e)}[/]')
		else:
			browser_info.write('[red]Browser not initialized[/]')