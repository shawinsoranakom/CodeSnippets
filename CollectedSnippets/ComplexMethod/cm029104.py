def scroll_info(self) -> dict[str, Any] | None:
		"""Calculate scroll information for this element if it's scrollable."""
		if not self.is_actually_scrollable or not self.snapshot_node:
			return None

		# Get scroll and client rects from snapshot data
		scroll_rects = self.snapshot_node.scrollRects
		client_rects = self.snapshot_node.clientRects
		bounds = self.snapshot_node.bounds

		if not scroll_rects or not client_rects:
			return None

		# Calculate scroll position and percentages
		scroll_top = scroll_rects.y
		scroll_left = scroll_rects.x

		# Total scrollable height and width
		scrollable_height = scroll_rects.height
		scrollable_width = scroll_rects.width

		# Visible (client) dimensions
		visible_height = client_rects.height
		visible_width = client_rects.width

		# Calculate how much content is above/below/left/right of current view
		content_above = max(0, scroll_top)
		content_below = max(0, scrollable_height - visible_height - scroll_top)
		content_left = max(0, scroll_left)
		content_right = max(0, scrollable_width - visible_width - scroll_left)

		# Calculate scroll percentages
		vertical_scroll_percentage = 0
		horizontal_scroll_percentage = 0

		if scrollable_height > visible_height:
			max_scroll_top = scrollable_height - visible_height
			vertical_scroll_percentage = (scroll_top / max_scroll_top) * 100 if max_scroll_top > 0 else 0

		if scrollable_width > visible_width:
			max_scroll_left = scrollable_width - visible_width
			horizontal_scroll_percentage = (scroll_left / max_scroll_left) * 100 if max_scroll_left > 0 else 0

		# Calculate pages equivalent (using visible height as page unit)
		pages_above = content_above / visible_height if visible_height > 0 else 0
		pages_below = content_below / visible_height if visible_height > 0 else 0
		total_pages = scrollable_height / visible_height if visible_height > 0 else 1

		return {
			'scroll_top': scroll_top,
			'scroll_left': scroll_left,
			'scrollable_height': scrollable_height,
			'scrollable_width': scrollable_width,
			'visible_height': visible_height,
			'visible_width': visible_width,
			'content_above': content_above,
			'content_below': content_below,
			'content_left': content_left,
			'content_right': content_right,
			'vertical_scroll_percentage': round(vertical_scroll_percentage, 1),
			'horizontal_scroll_percentage': round(horizontal_scroll_percentage, 1),
			'pages_above': round(pages_above, 1),
			'pages_below': round(pages_below, 1),
			'total_pages': round(total_pages, 1),
			'can_scroll_up': content_above > 0,
			'can_scroll_down': content_below > 0,
			'can_scroll_left': content_left > 0,
			'can_scroll_right': content_right > 0,
		}