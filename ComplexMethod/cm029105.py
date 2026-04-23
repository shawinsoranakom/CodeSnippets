def get_scroll_info_text(self) -> str:
		"""Get human-readable scroll information text for this element."""
		# Special case for iframes: check content document for scroll info
		if self.tag_name.lower() == 'iframe':
			# Try to get scroll info from the HTML document inside the iframe
			if self.content_document:
				# Look for HTML element in content document
				html_element = self._find_html_in_content_document()
				if html_element and html_element.scroll_info:
					info = html_element.scroll_info
					# Provide minimal but useful scroll info
					pages_below = info.get('pages_below', 0)
					pages_above = info.get('pages_above', 0)
					v_pct = int(info.get('vertical_scroll_percentage', 0))

					if pages_below > 0 or pages_above > 0:
						return f'scroll: {pages_above:.1f}↑ {pages_below:.1f}↓ {v_pct}%'

			return 'scroll'

		scroll_info = self.scroll_info
		if not scroll_info:
			return ''

		parts = []

		# Vertical scroll info (concise format)
		if scroll_info['scrollable_height'] > scroll_info['visible_height']:
			parts.append(f'{scroll_info["pages_above"]:.1f} pages above, {scroll_info["pages_below"]:.1f} pages below')

		# Horizontal scroll info (concise format)
		if scroll_info['scrollable_width'] > scroll_info['visible_width']:
			parts.append(f'horizontal {scroll_info["horizontal_scroll_percentage"]:.0f}%')

		return ' '.join(parts)