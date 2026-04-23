def is_actually_scrollable(self) -> bool:
		"""
		Enhanced scroll detection that combines CDP detection with CSS analysis.

		This detects scrollable elements that Chrome's CDP might miss, which is common
		in iframes and dynamically sized containers.
		"""
		# First check if CDP already detected it as scrollable
		if self.is_scrollable:
			return True

		# Enhanced detection for elements CDP missed
		if not self.snapshot_node:
			return False

		# Check scroll vs client rects - this is the most reliable indicator
		scroll_rects = self.snapshot_node.scrollRects
		client_rects = self.snapshot_node.clientRects

		if scroll_rects and client_rects:
			# Content is larger than visible area = scrollable
			has_vertical_scroll = scroll_rects.height > client_rects.height + 1  # +1 for rounding
			has_horizontal_scroll = scroll_rects.width > client_rects.width + 1

			if has_vertical_scroll or has_horizontal_scroll:
				# Also check CSS to make sure scrolling is allowed
				if self.snapshot_node.computed_styles:
					styles = self.snapshot_node.computed_styles

					overflow = styles.get('overflow', 'visible').lower()
					overflow_x = styles.get('overflow-x', overflow).lower()
					overflow_y = styles.get('overflow-y', overflow).lower()

					# Only allow scrolling if overflow is explicitly set to auto, scroll, or overlay
					# Do NOT consider 'visible' overflow as scrollable - this was causing the issue
					allows_scroll = (
						overflow in ['auto', 'scroll', 'overlay']
						or overflow_x in ['auto', 'scroll', 'overlay']
						or overflow_y in ['auto', 'scroll', 'overlay']
					)

					return allows_scroll
				else:
					# No CSS info, but content overflows - be more conservative
					# Only consider it scrollable if it's a common scrollable container element
					scrollable_tags = {'div', 'main', 'section', 'article', 'aside', 'body', 'html'}
					return self.tag_name.lower() in scrollable_tags

		return False