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