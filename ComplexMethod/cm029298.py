async def _close_extension_options_pages(self) -> None:
		"""Close any extension options/welcome pages that have opened."""
		try:
			# Get all page targets from SessionManager
			page_targets = self.session_manager.get_all_page_targets()

			for target in page_targets:
				target_url = target.url
				target_id = target.target_id

				# Check if this is an extension options/welcome page
				if 'chrome-extension://' in target_url and (
					'options.html' in target_url or 'welcome.html' in target_url or 'onboarding.html' in target_url
				):
					self.logger.info(f'[BrowserSession] 🚫 Closing extension options page: {target_url}')
					try:
						await self._cdp_close_page(target_id)
					except Exception as e:
						self.logger.debug(f'[BrowserSession] Could not close extension page {target_id}: {e}')

		except Exception as e:
			self.logger.debug(f'[BrowserSession] Error closing extension options pages: {e}')