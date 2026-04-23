def _include_entry(self, e: _HarEntryBuilder) -> bool:
		if not _is_https(e.url):
			return False
		# Filter out favicon requests (matching Playwright behavior)
		if e.url and '/favicon.ico' in e.url.lower():
			return False
		if getattr(self, '_mode', 'full') == 'full':
			return True
		# minimal: include main document and same-origin subresources
		if e.frame_id and e.frame_id in self._top_level_pages:
			page_info = self._top_level_pages[e.frame_id]
			page_url = page_info.get('url') if isinstance(page_info, dict) else page_info
			return _origin(e.url or '') == _origin(page_url or '')
		return False