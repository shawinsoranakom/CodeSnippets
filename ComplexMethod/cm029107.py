def is_element_visible_according_to_all_parents(
		cls, node: EnhancedDOMTreeNode, html_frames: list[EnhancedDOMTreeNode], viewport_threshold: int | None = 1000
	) -> bool:
		"""Check if the element is visible according to all its parent HTML frames.

		Args:
			node: The DOM node to check visibility for
			html_frames: List of parent HTML frame nodes
			viewport_threshold: Pixel threshold beyond viewport to consider visible.
				Default 1000px. Set to None to disable threshold checking entirely.
		"""

		if not node.snapshot_node:
			return False

		computed_styles = node.snapshot_node.computed_styles or {}

		display = computed_styles.get('display', '').lower()
		visibility = computed_styles.get('visibility', '').lower()
		opacity = computed_styles.get('opacity', '1')

		if display == 'none' or visibility == 'hidden':
			return False

		try:
			if float(opacity) <= 0:
				return False
		except (ValueError, TypeError):
			pass

		# Start with the element's local bounds (in its own frame's coordinate system)
		current_bounds = node.snapshot_node.bounds

		if not current_bounds:
			return False  # If there are no bounds, the element is not visible

		# If threshold is None, skip all viewport-based filtering (only check CSS visibility)
		if viewport_threshold is None:
			return True

		"""
		Reverse iterate through the html frames (that can be either iframe or document -> if it's a document frame compare if the current bounds interest with it (taking scroll into account) otherwise move the current bounds by the iframe offset)
		"""
		for frame in reversed(html_frames):
			if (
				frame.node_type == NodeType.ELEMENT_NODE
				and (frame.node_name.upper() == 'IFRAME' or frame.node_name.upper() == 'FRAME')
				and frame.snapshot_node
				and frame.snapshot_node.bounds
			):
				iframe_bounds = frame.snapshot_node.bounds

				# negate the values added in `_construct_enhanced_node`
				current_bounds.x += iframe_bounds.x
				current_bounds.y += iframe_bounds.y

			if (
				frame.node_type == NodeType.ELEMENT_NODE
				and frame.node_name == 'HTML'
				and frame.snapshot_node
				and frame.snapshot_node.scrollRects
				and frame.snapshot_node.clientRects
			):
				# For iframe content, we need to check visibility within the iframe's viewport
				# The scrollRects represent the current scroll position
				# The clientRects represent the viewport size
				# Elements are visible if they fall within the viewport after accounting for scroll

				# The viewport of the frame (what's actually visible)
				viewport_left = 0  # Viewport always starts at 0 in frame coordinates
				viewport_top = 0
				viewport_right = frame.snapshot_node.clientRects.width
				viewport_bottom = frame.snapshot_node.clientRects.height

				# Adjust element bounds by the scroll offset to get position relative to viewport
				# When scrolled down, scrollRects.y is positive, so we subtract it from element's y
				adjusted_x = current_bounds.x - frame.snapshot_node.scrollRects.x
				adjusted_y = current_bounds.y - frame.snapshot_node.scrollRects.y

				frame_intersects = (
					adjusted_x < viewport_right
					and adjusted_x + current_bounds.width > viewport_left
					and adjusted_y < viewport_bottom + viewport_threshold
					and adjusted_y + current_bounds.height > viewport_top - viewport_threshold
				)

				if not frame_intersects:
					return False

				# Keep the original coordinate adjustment to maintain consistency
				# This adjustment is needed for proper coordinate transformation
				current_bounds.x -= frame.snapshot_node.scrollRects.x
				current_bounds.y -= frame.snapshot_node.scrollRects.y

		# If we reach here, element is visible in main viewport and all containing iframes
		return True