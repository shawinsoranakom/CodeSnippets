def detect_pagination_buttons(selector_map: dict[int, EnhancedDOMTreeNode]) -> list[dict[str, str | int | bool]]:
		"""Detect pagination buttons from the selector map.

		Args:
			selector_map: Map of element indices to EnhancedDOMTreeNode

		Returns:
			List of pagination button information dicts with:
			- button_type: 'next', 'prev', 'first', 'last', 'page_number'
			- backend_node_id: Backend node ID for clicking
			- text: Button text/label
			- selector: XPath selector
			- is_disabled: Whether the button appears disabled
		"""
		pagination_buttons: list[dict[str, str | int | bool]] = []

		# Common pagination patterns to look for
		# `«` and `»` are ambiguous across sites, so treat them only as prev/next
		# fallback symbols and let word-based first/last signals win
		next_patterns = ['next', '>', '»', '→', 'siguiente', 'suivant', 'weiter', 'volgende']
		prev_patterns = ['prev', 'previous', '<', '«', '←', 'anterior', 'précédent', 'zurück', 'vorige']
		first_patterns = ['first', '⇤', 'primera', 'première', 'erste', 'eerste']
		last_patterns = ['last', '⇥', 'última', 'dernier', 'letzte', 'laatste']

		for index, node in selector_map.items():
			# Skip non-clickable elements
			if not node.snapshot_node or not node.snapshot_node.is_clickable:
				continue

			# Get element text and attributes
			text = node.get_all_children_text().lower().strip()
			aria_label = node.attributes.get('aria-label', '').lower()
			title = node.attributes.get('title', '').lower()
			class_name = node.attributes.get('class', '').lower()
			role = node.attributes.get('role', '').lower()

			# Combine all text sources for pattern matching
			all_text = f'{text} {aria_label} {title} {class_name}'.strip()

			# Check if it's disabled
			is_disabled = (
				node.attributes.get('disabled') == 'true'
				or node.attributes.get('aria-disabled') == 'true'
				or 'disabled' in class_name
			)

			button_type: str | None = None

			# Match specific first/last semantics before generic prev/next fallbacks.
			if any(pattern in all_text for pattern in first_patterns):
				button_type = 'first'
			# Check for last button
			elif any(pattern in all_text for pattern in last_patterns):
				button_type = 'last'
			# Check for next button
			elif any(pattern in all_text for pattern in next_patterns):
				button_type = 'next'
			# Check for previous button
			elif any(pattern in all_text for pattern in prev_patterns):
				button_type = 'prev'
			# Check for numeric page buttons (single or double digit)
			elif text.isdigit() and len(text) <= 2 and role in ['button', 'link', '']:
				button_type = 'page_number'

			if button_type:
				pagination_buttons.append(
					{
						'button_type': button_type,
						'backend_node_id': index,
						'text': node.get_all_children_text().strip() or aria_label or title,
						'selector': node.xpath,
						'is_disabled': is_disabled,
					}
				)

		return pagination_buttons