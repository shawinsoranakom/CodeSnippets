def serialize_tree(node: SimplifiedNode | None, include_attributes: list[str], depth: int = 0) -> str:
		"""Serialize the optimized tree to string format."""
		if not node:
			return ''

		# Skip rendering excluded nodes, but process their children
		if hasattr(node, 'excluded_by_parent') and node.excluded_by_parent:
			formatted_text = []
			for child in node.children:
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, depth)
				if child_text:
					formatted_text.append(child_text)
			return '\n'.join(formatted_text)

		formatted_text = []
		depth_str = depth * '\t'
		next_depth = depth

		if node.original_node.node_type == NodeType.ELEMENT_NODE:
			# Skip displaying nodes marked as should_display=False
			if not node.should_display:
				for child in node.children:
					child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, depth)
					if child_text:
						formatted_text.append(child_text)
				return '\n'.join(formatted_text)

			# Special handling for SVG elements - show the tag but collapse children
			if node.original_node.tag_name.lower() == 'svg':
				shadow_prefix = ''
				if node.is_shadow_host:
					has_closed_shadow = any(
						child.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
						and child.original_node.shadow_root_type
						and child.original_node.shadow_root_type.lower() == 'closed'
						for child in node.children
					)
					shadow_prefix = '|SHADOW(closed)|' if has_closed_shadow else '|SHADOW(open)|'

				line = f'{depth_str}{shadow_prefix}'
				# Add interactive marker if clickable
				if node.is_interactive:
					new_prefix = '*' if node.is_new else ''
					line += f'{new_prefix}[{node.original_node.backend_node_id}]'
				line += '<svg'
				attributes_html_str = DOMTreeSerializer._build_attributes_string(node.original_node, include_attributes, '')
				if attributes_html_str:
					line += f' {attributes_html_str}'
				line += ' /> <!-- SVG content collapsed -->'
				formatted_text.append(line)
				# Don't process children for SVG
				return '\n'.join(formatted_text)

			# Add element if clickable, scrollable, or iframe
			is_any_scrollable = node.original_node.is_actually_scrollable or node.original_node.is_scrollable
			should_show_scroll = node.original_node.should_show_scroll_info
			if (
				node.is_interactive
				or is_any_scrollable
				or node.original_node.tag_name.upper() == 'IFRAME'
				or node.original_node.tag_name.upper() == 'FRAME'
			):
				next_depth += 1

				# Build attributes string with compound component info
				text_content = ''
				attributes_html_str = DOMTreeSerializer._build_attributes_string(
					node.original_node, include_attributes, text_content
				)

				# Add compound component information to attributes if present
				if node.original_node._compound_children:
					compound_info = []
					for child_info in node.original_node._compound_children:
						parts = []
						if child_info['name']:
							parts.append(f'name={child_info["name"]}')
						if child_info['role']:
							parts.append(f'role={child_info["role"]}')
						if child_info['valuemin'] is not None:
							parts.append(f'min={child_info["valuemin"]}')
						if child_info['valuemax'] is not None:
							parts.append(f'max={child_info["valuemax"]}')
						if child_info['valuenow'] is not None:
							parts.append(f'current={child_info["valuenow"]}')

						# Add select-specific information
						if 'options_count' in child_info and child_info['options_count'] is not None:
							parts.append(f'count={child_info["options_count"]}')
						if 'first_options' in child_info and child_info['first_options']:
							options_str = '|'.join(child_info['first_options'][:4])  # Limit to 4 options
							parts.append(f'options={options_str}')
						if 'format_hint' in child_info and child_info['format_hint']:
							parts.append(f'format={child_info["format_hint"]}')

						if parts:
							compound_info.append(f'({",".join(parts)})')

					if compound_info:
						compound_attr = f'compound_components={",".join(compound_info)}'
						if attributes_html_str:
							attributes_html_str += f' {compound_attr}'
						else:
							attributes_html_str = compound_attr

				# Build the line with shadow host indicator
				shadow_prefix = ''
				if node.is_shadow_host:
					# Check if any shadow children are closed
					has_closed_shadow = any(
						child.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
						and child.original_node.shadow_root_type
						and child.original_node.shadow_root_type.lower() == 'closed'
						for child in node.children
					)
					shadow_prefix = '|SHADOW(closed)|' if has_closed_shadow else '|SHADOW(open)|'

				if should_show_scroll and not node.is_interactive:
					# Scrollable container but not clickable
					line = f'{depth_str}{shadow_prefix}|scroll element|<{node.original_node.tag_name}'
				elif node.is_interactive:
					# Clickable (and possibly scrollable) - show backend_node_id
					new_prefix = '*' if node.is_new else ''
					scroll_prefix = '|scroll element[' if should_show_scroll else '['
					line = f'{depth_str}{shadow_prefix}{new_prefix}{scroll_prefix}{node.original_node.backend_node_id}]<{node.original_node.tag_name}'
				elif node.original_node.tag_name.upper() == 'IFRAME':
					# Iframe element (not interactive)
					line = f'{depth_str}{shadow_prefix}|IFRAME|<{node.original_node.tag_name}'
				elif node.original_node.tag_name.upper() == 'FRAME':
					# Frame element (not interactive)
					line = f'{depth_str}{shadow_prefix}|FRAME|<{node.original_node.tag_name}'
				else:
					line = f'{depth_str}{shadow_prefix}<{node.original_node.tag_name}'

				if attributes_html_str:
					line += f' {attributes_html_str}'

				line += ' />'

				# Add scroll information only when we should show it
				if should_show_scroll:
					scroll_info_text = node.original_node.get_scroll_info_text()
					if scroll_info_text:
						line += f' ({scroll_info_text})'

				formatted_text.append(line)

		elif node.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# Shadow DOM representation - show clearly to LLM
			if node.original_node.shadow_root_type and node.original_node.shadow_root_type.lower() == 'closed':
				formatted_text.append(f'{depth_str}Closed Shadow')
			else:
				formatted_text.append(f'{depth_str}Open Shadow')

			next_depth += 1

			# Process shadow DOM children
			for child in node.children:
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, next_depth)
				if child_text:
					formatted_text.append(child_text)

			# Close shadow DOM indicator
			if node.children:  # Only show close if we had content
				formatted_text.append(f'{depth_str}Shadow End')

		elif node.original_node.node_type == NodeType.TEXT_NODE:
			# Include visible text
			is_visible = node.original_node.snapshot_node and node.original_node.is_visible
			if (
				is_visible
				and node.original_node.node_value
				and node.original_node.node_value.strip()
				and len(node.original_node.node_value.strip()) > 1
			):
				clean_text = node.original_node.node_value.strip()
				formatted_text.append(f'{depth_str}{clean_text}')

		# Process children (for non-shadow elements)
		if node.original_node.node_type != NodeType.DOCUMENT_FRAGMENT_NODE:
			for child in node.children:
				child_text = DOMTreeSerializer.serialize_tree(child, include_attributes, next_depth)
				if child_text:
					formatted_text.append(child_text)

			# Add hidden content hint for iframes
			if (
				node.original_node.node_type == NodeType.ELEMENT_NODE
				and node.original_node.tag_name
				and node.original_node.tag_name.upper() in ('IFRAME', 'FRAME')
			):
				if node.original_node.hidden_elements_info:
					# Show specific interactive elements with scroll distances
					hidden = node.original_node.hidden_elements_info
					hint_lines = [f'{depth_str}... ({len(hidden)} more elements below - scroll to reveal):']
					for elem in hidden:
						hint_lines.append(f'{depth_str}    <{elem["tag"]}> "{elem["text"]}" ~{elem["pages"]} pages down')
					formatted_text.extend(hint_lines)
				elif node.original_node.has_hidden_content:
					# Generic hint for non-interactive hidden content
					formatted_text.append(f'{depth_str}... (more content below viewport - scroll to reveal)')

		return '\n'.join(formatted_text)