async def get_tabs(self) -> list[TabInfo]:
		"""Get information about all open tabs using cached target data."""
		tabs = []

		# Safety check - return empty list if browser not connected yet
		if not self.session_manager:
			return tabs

		# Get all page targets from SessionManager
		page_targets = self.session_manager.get_all_page_targets()

		for i, target in enumerate(page_targets):
			target_id = target.target_id
			url = target.url
			title = target.title

			try:
				# Skip JS execution for chrome:// pages and new tab pages
				if is_new_tab_page(url) or url.startswith('chrome://'):
					# Use URL as title for chrome pages, or mark new tabs as unusable
					if is_new_tab_page(url):
						title = ''
					elif not title:
						# For chrome:// pages without a title, use the URL itself
						title = url

				# Special handling for PDF pages without titles
				if (not title or title == '') and (url.endswith('.pdf') or 'pdf' in url):
					# PDF pages might not have a title, use URL filename
					try:
						from urllib.parse import urlparse

						filename = urlparse(url).path.split('/')[-1]
						if filename:
							title = filename
					except Exception:
						pass

			except Exception as e:
				# Fallback to basic title handling
				self.logger.debug(f'⚠️ Failed to get target info for tab #{i}: {_log_pretty_url(url)} - {type(e).__name__}')

				if is_new_tab_page(url):
					title = ''
				elif url.startswith('chrome://'):
					title = url
				else:
					title = ''

			tab_info = TabInfo(
				target_id=target_id,
				url=url,
				title=title,
				parent_target_id=None,
			)
			tabs.append(tab_info)

		return tabs