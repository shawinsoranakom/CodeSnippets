def draw_bounding_box_with_text(
	draw,  # ImageDraw.Draw - avoiding type annotation due to PIL typing issues
	bbox: tuple[int, int, int, int],
	color: str,
	text: str | None = None,
	font: ImageFont.FreeTypeFont | None = None,
) -> None:
	"""Draw a bounding box with optional text overlay."""
	x1, y1, x2, y2 = bbox

	# Draw dashed bounding box
	dash_length = 2
	gap_length = 6

	# Top edge
	x = x1
	while x < x2:
		end_x = min(x + dash_length, x2)
		draw.line([(x, y1), (end_x, y1)], fill=color, width=2)
		draw.line([(x, y1 + 1), (end_x, y1 + 1)], fill=color, width=2)
		x += dash_length + gap_length

	# Bottom edge
	x = x1
	while x < x2:
		end_x = min(x + dash_length, x2)
		draw.line([(x, y2), (end_x, y2)], fill=color, width=2)
		draw.line([(x, y2 - 1), (end_x, y2 - 1)], fill=color, width=2)
		x += dash_length + gap_length

	# Left edge
	y = y1
	while y < y2:
		end_y = min(y + dash_length, y2)
		draw.line([(x1, y), (x1, end_y)], fill=color, width=2)
		draw.line([(x1 + 1, y), (x1 + 1, end_y)], fill=color, width=2)
		y += dash_length + gap_length

	# Right edge
	y = y1
	while y < y2:
		end_y = min(y + dash_length, y2)
		draw.line([(x2, y), (x2, end_y)], fill=color, width=2)
		draw.line([(x2 - 1, y), (x2 - 1, end_y)], fill=color, width=2)
		y += dash_length + gap_length

	# Draw index overlay if we have index text
	if text:
		try:
			# Get text size
			if font:
				bbox_text = draw.textbbox((0, 0), text, font=font)
				text_width = bbox_text[2] - bbox_text[0]
				text_height = bbox_text[3] - bbox_text[1]
			else:
				# Fallback for default font
				bbox_text = draw.textbbox((0, 0), text)
				text_width = bbox_text[2] - bbox_text[0]
				text_height = bbox_text[3] - bbox_text[1]

			# Smart positioning based on element size
			padding = 5
			element_width = x2 - x1
			element_height = y2 - y1
			element_area = element_width * element_height
			index_box_area = (text_width + padding * 2) * (text_height + padding * 2)

			# Calculate size ratio to determine positioning strategy
			size_ratio = element_area / max(index_box_area, 1)

			if size_ratio < 4:
				# Very small elements: place outside in bottom-right corner
				text_x = x2 + padding
				text_y = y2 - text_height
				# Ensure it doesn't go off screen
				text_x = min(text_x, 1200 - text_width - padding)
				text_y = max(text_y, 0)
			elif size_ratio < 16:
				# Medium elements: place in bottom-right corner inside
				text_x = x2 - text_width - padding
				text_y = y2 - text_height - padding
			else:
				# Large elements: place in center
				text_x = x1 + (element_width - text_width) // 2
				text_y = y1 + (element_height - text_height) // 2

			# Ensure text stays within bounds
			text_x = max(0, min(text_x, 1200 - text_width))
			text_y = max(0, min(text_y, 800 - text_height))

			# Draw background rectangle for maximum contrast
			bg_x1 = text_x - padding
			bg_y1 = text_y - padding
			bg_x2 = text_x + text_width + padding
			bg_y2 = text_y + text_height + padding

			# Use white background with thick black border for maximum visibility
			draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill='white', outline='black', width=2)

			# Draw bold dark text on light background for best contrast
			draw.text((text_x, text_y), text, fill='black', font=font)

		except Exception as e:
			logger.debug(f'Failed to draw text overlay: {e}')