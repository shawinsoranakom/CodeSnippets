def traverse_node(node: SimplifiedNode) -> None:
			"""Recursively traverse simplified DOM tree to count elements"""
			if not node or not node.original_node:
				return

			original = node.original_node
			stats['total_elements'] += 1

			# Count by node type and tag
			if original.node_type == NodeType.ELEMENT_NODE:
				tag = original.tag_name.lower() if original.tag_name else ''

				if tag == 'a':
					stats['links'] += 1
				elif tag in ('iframe', 'frame'):
					stats['iframes'] += 1
				elif tag == 'img':
					stats['images'] += 1

				# Check if scrollable
				if original.is_actually_scrollable:
					stats['scroll_containers'] += 1

				# Check if interactive
				if node.is_interactive:
					stats['interactive_elements'] += 1

				# Check if this element hosts shadow DOM
				if node.is_shadow_host:
					# Check if any shadow children are closed
					has_closed_shadow = any(
						child.original_node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
						and child.original_node.shadow_root_type
						and child.original_node.shadow_root_type.lower() == 'closed'
						for child in node.children
					)
					if has_closed_shadow:
						stats['shadow_closed'] += 1
					else:
						stats['shadow_open'] += 1

			elif original.node_type == NodeType.TEXT_NODE:
				stats['text_chars'] += len(original.node_value.strip())

			elif original.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
				# Shadow DOM fragment - these are the actual shadow roots
				# But don't double-count since we count them at the host level above
				pass

			# Traverse children
			for child in node.children:
				traverse_node(child)