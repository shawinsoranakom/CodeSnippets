def serialize_tree(node: SimplifiedNode | None, include_attributes: list[str], depth: int = 0) -> str:
		"""
		Serialize complete DOM tree structure for LLM understanding.

		Strategy:
		- Show ALL elements to preserve DOM structure
		- Non-interactive elements show just tag name
		- Interactive elements show full attributes + [index]
		- Self-closing tags only (no closing tags)
		"""
		if not node:
			return ''

		# Skip excluded nodes but process children
		if hasattr(node, 'excluded_by_parent') and node.excluded_by_parent:
			return DOMEvalSerializer._serialize_children(node, include_attributes, depth)

		# Skip nodes marked as should_display=False
		if not node.should_display:
			return DOMEvalSerializer._serialize_children(node, include_attributes, depth)

		formatted_text = []
		depth_str = depth * '\t'

		if node.original_node.node_type == NodeType.ELEMENT_NODE:
			tag = node.original_node.tag_name.lower()
			is_visible = node.original_node.snapshot_node and node.original_node.is_visible

			# Container elements that should be shown even if invisible (might have visible children)
			container_tags = {'html', 'body', 'div', 'main', 'section', 'article', 'aside', 'header', 'footer', 'nav'}

			# Skip invisible elements UNLESS they're containers or iframes (which might have visible children)
			if not is_visible and tag not in container_tags and tag not in ['iframe', 'frame']:
				return DOMEvalSerializer._serialize_children(node, include_attributes, depth)

			# Special handling for iframes - show them with their content
			if tag in ['iframe', 'frame']:
				return DOMEvalSerializer._serialize_iframe(node, include_attributes, depth)

			# Skip SVG elements entirely - they're just decorative graphics with no interaction value
			# Show the <svg> tag itself to indicate graphics, but don't recurse into children
			if tag == 'svg':
				line = f'{depth_str}'
				# Add [i_X] for interactive SVG elements only
				if node.is_interactive:
					line += f'[i_{node.original_node.backend_node_id}] '
				line += '<svg'
				attributes_str = DOMEvalSerializer._build_compact_attributes(node.original_node)
				if attributes_str:
					line += f' {attributes_str}'
				line += ' /> <!-- SVG content collapsed -->'
				return line

			# Skip SVG child elements entirely (path, rect, g, circle, etc.)
			if tag in SVG_ELEMENTS:
				return ''

			# Build compact attributes string
			attributes_str = DOMEvalSerializer._build_compact_attributes(node.original_node)

			# Decide if this element should be shown
			is_semantic = tag in SEMANTIC_ELEMENTS
			has_useful_attrs = bool(attributes_str)
			has_text_content = DOMEvalSerializer._has_direct_text(node)
			has_children = len(node.children) > 0

			# Build compact element representation
			line = f'{depth_str}'
			# Add backend node ID notation - [i_X] for interactive elements only
			if node.is_interactive:
				line += f'[i_{node.original_node.backend_node_id}] '
			# Non-interactive elements don't get an index notation
			line += f'<{tag}'

			if attributes_str:
				line += f' {attributes_str}'

			# Add scroll info if element is scrollable
			if node.original_node.should_show_scroll_info:
				scroll_text = node.original_node.get_scroll_info_text()
				if scroll_text:
					line += f' scroll="{scroll_text}"'

			# Add inline text if present (keep it on same line for compactness)
			inline_text = DOMEvalSerializer._get_inline_text(node)

			# For containers (html, body, div, etc.), always show children even if there's inline text
			# For other elements, inline text replaces children (more compact)
			is_container = tag in container_tags

			if inline_text and not is_container:
				line += f'>{inline_text}'
			else:
				line += ' />'

			formatted_text.append(line)

			# Process children (always for containers, only if no inline_text for others)
			if has_children and (is_container or not inline_text):
				children_text = DOMEvalSerializer._serialize_children(node, include_attributes, depth + 1)
				if children_text:
					formatted_text.append(children_text)

		elif node.original_node.node_type == NodeType.TEXT_NODE:
			# Text nodes are handled inline with their parent
			pass

		elif node.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# Shadow DOM - just show children directly with minimal marker
			if node.children:
				formatted_text.append(f'{depth_str}#shadow')
				children_text = DOMEvalSerializer._serialize_children(node, include_attributes, depth + 1)
				if children_text:
					formatted_text.append(children_text)

		return '\n'.join(formatted_text)