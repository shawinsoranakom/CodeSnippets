def _serialize_children(node: SimplifiedNode, include_attributes: list[str], depth: int) -> str:
		"""Helper to serialize all children of a node."""
		children_output = []

		# Check if parent is a list container (ul, ol)
		is_list_container = node.original_node.node_type == NodeType.ELEMENT_NODE and node.original_node.tag_name.lower() in [
			'ul',
			'ol',
		]

		# Track list items and consecutive links
		li_count = 0
		max_list_items = 50
		consecutive_link_count = 0
		max_consecutive_links = 50
		total_links_skipped = 0

		for child in node.children:
			# Get tag name for this child
			current_tag = None
			if child.original_node.node_type == NodeType.ELEMENT_NODE:
				current_tag = child.original_node.tag_name.lower()

			# If we're in a list container and this child is an li element
			if is_list_container and current_tag == 'li':
				li_count += 1
				# Skip li elements after the 5th one
				if li_count > max_list_items:
					continue

			# Track consecutive anchor tags (links)
			if current_tag == 'a':
				consecutive_link_count += 1
				# Skip links after the 5th consecutive one
				if consecutive_link_count > max_consecutive_links:
					total_links_skipped += 1
					continue
			else:
				# Reset counter when we hit a non-link element
				# But first add truncation message if we skipped links
				if total_links_skipped > 0:
					depth_str = depth * '\t'
					children_output.append(f'{depth_str}... ({total_links_skipped} more links in this list)')
					total_links_skipped = 0
				consecutive_link_count = 0

			child_text = DOMEvalSerializer.serialize_tree(child, include_attributes, depth)
			if child_text:
				children_output.append(child_text)

		# Add truncation message if we skipped items at the end
		if is_list_container and li_count > max_list_items:
			depth_str = depth * '\t'
			children_output.append(
				f'{depth_str}... ({li_count - max_list_items} more items in this list (truncated) use evaluate to get more.'
			)

		# Add truncation message for links if we skipped any at the end
		if total_links_skipped > 0:
			depth_str = depth * '\t'
			children_output.append(
				f'{depth_str}... ({total_links_skipped} more links in this list) (truncated) use evaluate to get more.'
			)

		return '\n'.join(children_output)