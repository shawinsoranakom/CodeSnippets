def _serialize_iframe(node: SimplifiedNode, include_attributes: list[str], depth: int) -> str:
		"""Handle iframe serialization with content document."""
		formatted_text = []
		depth_str = depth * '\t'
		tag = node.original_node.tag_name.lower()

		# Build minimal iframe marker with key attributes
		attributes_str = DOMEvalSerializer._build_compact_attributes(node.original_node)
		line = f'{depth_str}<{tag}'
		if attributes_str:
			line += f' {attributes_str}'

		# Add scroll info for iframe content
		if node.original_node.should_show_scroll_info:
			scroll_text = node.original_node.get_scroll_info_text()
			if scroll_text:
				line += f' scroll="{scroll_text}"'

		line += ' />'
		formatted_text.append(line)

		# If iframe has content document, serialize its content
		if node.original_node.content_document:
			# Add marker for iframe content
			formatted_text.append(f'{depth_str}\t#iframe-content')

			# Process content document children
			for child_node in node.original_node.content_document.children_nodes or []:
				# Process html documents
				if child_node.tag_name.lower() == 'html':
					# Find and serialize body content only (skip head)
					for html_child in child_node.children:
						if html_child.tag_name.lower() == 'body':
							for body_child in html_child.children:
								# Recursively process body children (iframe content)
								DOMEvalSerializer._serialize_document_node(
									body_child, formatted_text, include_attributes, depth + 2, is_iframe_content=True
								)
							break  # Stop after processing body
				else:
					# Not an html element - serialize directly
					DOMEvalSerializer._serialize_document_node(
						child_node, formatted_text, include_attributes, depth + 1, is_iframe_content=True
					)

		return '\n'.join(formatted_text)