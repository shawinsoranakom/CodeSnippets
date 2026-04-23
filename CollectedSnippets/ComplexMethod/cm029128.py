def _extract_select_options(self, select_node: EnhancedDOMTreeNode) -> dict[str, Any] | None:
		"""Extract option information from a select element."""
		if not select_node.children:
			return None

		options = []
		option_values = []

		def extract_options_recursive(node: EnhancedDOMTreeNode) -> None:
			"""Recursively extract option elements, including from optgroups."""
			if node.tag_name.lower() == 'option':
				# Extract option text and value
				option_text = ''
				option_value = ''

				# Get value attribute if present
				if node.attributes and 'value' in node.attributes:
					option_value = str(node.attributes['value']).strip()

				# Get text content from direct child text nodes only to avoid duplication
				def get_direct_text_content(n: EnhancedDOMTreeNode) -> str:
					text = ''
					for child in n.children:
						if child.node_type == NodeType.TEXT_NODE and child.node_value:
							text += child.node_value.strip() + ' '
					return text.strip()

				option_text = get_direct_text_content(node)

				# Use text as value if no explicit value
				if not option_value and option_text:
					option_value = option_text

				if option_text or option_value:
					options.append({'text': option_text, 'value': option_value})
					option_values.append(option_value)

			elif node.tag_name.lower() == 'optgroup':
				# Process optgroup children
				for child in node.children:
					extract_options_recursive(child)
			else:
				# Process other children that might contain options
				for child in node.children:
					extract_options_recursive(child)

		# Extract all options from select children
		for child in select_node.children:
			extract_options_recursive(child)

		if not options:
			return None

		# Prepare first 4 options for display
		first_options = []
		for option in options[:4]:
			# Always use text if available, otherwise use value
			display_text = option['text'] if option['text'] else option['value']
			if display_text:
				# Limit individual option text to avoid overly long attributes
				text = display_text[:30] + ('...' if len(display_text) > 30 else '')
				first_options.append(text)

		# Add ellipsis indicator if there are more options than shown
		if len(options) > 4:
			first_options.append(f'... {len(options) - 4} more options...')

		# Try to infer format hint from option values
		format_hint = None
		if len(option_values) >= 2:
			# Check for common patterns
			if all(val.isdigit() for val in option_values[:5] if val):
				format_hint = 'numeric'
			elif all(len(val) == 2 and val.isupper() for val in option_values[:5] if val):
				format_hint = 'country/state codes'
			elif all('/' in val or '-' in val for val in option_values[:5] if val):
				format_hint = 'date/path format'
			elif any('@' in val for val in option_values[:5] if val):
				format_hint = 'email addresses'

		return {'count': len(options), 'first_options': first_options, 'format_hint': format_hint}