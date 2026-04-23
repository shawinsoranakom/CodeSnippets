def process_element_highlight(
	element_id: int,
	element: EnhancedDOMTreeNode,
	draw,
	device_pixel_ratio: float,
	font,
	filter_highlight_ids: bool,
	image_size: tuple[int, int],
) -> None:
	"""Process a single element for highlighting."""
	try:
		# Use absolute_position coordinates directly
		if not element.absolute_position:
			return

		bounds = element.absolute_position

		# Scale coordinates from CSS pixels to device pixels for screenshot
		# The screenshot is captured at device pixel resolution, but coordinates are in CSS pixels
		x1 = int(bounds.x * device_pixel_ratio)
		y1 = int(bounds.y * device_pixel_ratio)
		x2 = int((bounds.x + bounds.width) * device_pixel_ratio)
		y2 = int((bounds.y + bounds.height) * device_pixel_ratio)

		# Ensure coordinates are within image bounds
		img_width, img_height = image_size
		x1 = max(0, min(x1, img_width))
		y1 = max(0, min(y1, img_height))
		x2 = max(x1, min(x2, img_width))
		y2 = max(y1, min(y2, img_height))

		# Skip if bounding box is too small or invalid
		if x2 - x1 < 2 or y2 - y1 < 2:
			return

		# Get element color based on type
		tag_name = element.tag_name if hasattr(element, 'tag_name') else 'div'
		element_type = None
		if hasattr(element, 'attributes') and element.attributes:
			element_type = element.attributes.get('type')

		color = get_element_color(tag_name, element_type)

		# Get element index for overlay and apply filtering
		backend_node_id = getattr(element, 'backend_node_id', None)
		index_text = None

		if backend_node_id is not None:
			if filter_highlight_ids:
				# Use the meaningful text that matches what the LLM sees
				meaningful_text = element.get_meaningful_text_for_llm()
				# Show ID only if meaningful text is less than 5 characters
				if len(meaningful_text) < 3:
					index_text = str(backend_node_id)
			else:
				# Always show ID when filter is disabled
				index_text = str(backend_node_id)

		# Draw enhanced bounding box with bigger index
		draw_enhanced_bounding_box_with_text(
			draw, (x1, y1, x2, y2), color, index_text, font, tag_name, image_size, device_pixel_ratio
		)

	except Exception as e:
		logger.debug(f'Failed to draw highlight for element {element_id}: {e}')