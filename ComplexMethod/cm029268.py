def draw_enhanced_bounding_box_with_text(
	draw,  # ImageDraw.Draw - avoiding type annotation due to PIL typing issues
	bbox: tuple[int, int, int, int],
	color: str,
	text: str | None = None,
	font: ImageFont.FreeTypeFont | None = None,
	element_type: str = 'div',
	image_size: tuple[int, int] = (2000, 1500),
	device_pixel_ratio: float = 1.0,
) -> None:
	"""Draw an enhanced bounding box with much bigger index containers and dashed borders."""
	x1, y1, x2, y2 = bbox

	# Draw dashed bounding box with pattern: 1 line, 2 spaces, 1 line, 2 spaces...
	dash_length = 4
	gap_length = 8
	line_width = 2

	# Helper function to draw dashed line
	def draw_dashed_line(start_x, start_y, end_x, end_y):
		if start_x == end_x:  # Vertical line
			y = start_y
			while y < end_y:
				dash_end = min(y + dash_length, end_y)
				draw.line([(start_x, y), (start_x, dash_end)], fill=color, width=line_width)
				y += dash_length + gap_length
		else:  # Horizontal line
			x = start_x
			while x < end_x:
				dash_end = min(x + dash_length, end_x)
				draw.line([(x, start_y), (dash_end, start_y)], fill=color, width=line_width)
				x += dash_length + gap_length

	# Draw dashed rectangle
	draw_dashed_line(x1, y1, x2, y1)  # Top
	draw_dashed_line(x2, y1, x2, y2)  # Right
	draw_dashed_line(x2, y2, x1, y2)  # Bottom
	draw_dashed_line(x1, y2, x1, y1)  # Left

	# Draw much bigger index overlay if we have index text
	if text:
		try:
			# Scale font size for appropriate sizing across different resolutions
			img_width, img_height = image_size

			css_width = img_width  # / device_pixel_ratio
			# Much smaller scaling - 1% of CSS viewport width, max 16px to prevent huge highlights
			base_font_size = max(10, min(20, int(css_width * 0.01)))
			# Use shared font loading function with caching
			big_font = get_cross_platform_font(base_font_size)
			if big_font is None:
				big_font = font  # Fallback to original font if no system fonts found

			# Get text size with bigger font
			if big_font:
				bbox_text = draw.textbbox((0, 0), text, font=big_font)
				text_width = bbox_text[2] - bbox_text[0]
				text_height = bbox_text[3] - bbox_text[1]
			else:
				# Fallback for default font
				bbox_text = draw.textbbox((0, 0), text)
				text_width = bbox_text[2] - bbox_text[0]
				text_height = bbox_text[3] - bbox_text[1]

			# Scale padding appropriately for different resolutions
			padding = max(4, min(10, int(css_width * 0.005)))  # 0.3% of CSS width, max 4px
			element_width = x2 - x1
			element_height = y2 - y1

			# Container dimensions
			container_width = text_width + padding * 2
			container_height = text_height + padding * 2

			# Position in top center - for small elements, place further up to avoid blocking content
			# Center horizontally within the element
			bg_x1 = x1 + (element_width - container_width) // 2

			# Simple rule: if element is small, place index further up to avoid blocking icons
			if element_width < 60 or element_height < 30:
				# Small element: place well above to avoid blocking content
				bg_y1 = max(0, y1 - container_height - 5)
			else:
				# Regular element: place inside with small offset
				bg_y1 = y1 + 2

			bg_x2 = bg_x1 + container_width
			bg_y2 = bg_y1 + container_height

			# Center the number within the index box with proper baseline handling
			text_x = bg_x1 + (container_width - text_width) // 2
			# Add extra vertical space to prevent clipping
			text_y = bg_y1 + (container_height - text_height) // 2 - bbox_text[1]  # Subtract top offset

			# Ensure container stays within image bounds
			img_width, img_height = image_size
			if bg_x1 < 0:
				offset = -bg_x1
				bg_x1 += offset
				bg_x2 += offset
				text_x += offset
			if bg_y1 < 0:
				offset = -bg_y1
				bg_y1 += offset
				bg_y2 += offset
				text_y += offset
			if bg_x2 > img_width:
				offset = bg_x2 - img_width
				bg_x1 -= offset
				bg_x2 -= offset
				text_x -= offset
			if bg_y2 > img_height:
				offset = bg_y2 - img_height
				bg_y1 -= offset
				bg_y2 -= offset
				text_y -= offset

			# Draw bigger background rectangle with thicker border
			draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=color, outline='white', width=2)

			# Draw white text centered in the index box
			draw.text((text_x, text_y), text, fill='white', font=big_font or font)

		except Exception as e:
			logger.debug(f'Failed to draw enhanced text overlay: {e}')