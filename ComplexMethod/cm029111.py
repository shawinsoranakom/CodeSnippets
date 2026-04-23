def collect_hidden_elements(subtree_root: EnhancedDOMTreeNode, viewport_height: float) -> list[dict[str, Any]]:
			"""Collect hidden interactive elements from subtree."""
			hidden: list[dict[str, Any]] = []

			if subtree_root.node_type == NodeType.ELEMENT_NODE:
				is_interactive = ClickableElementDetector.is_interactive(subtree_root)

				if is_interactive and is_hidden_by_threshold(subtree_root):
					# Get element text/name
					text = ''
					if subtree_root.ax_node and subtree_root.ax_node.name:
						text = subtree_root.ax_node.name[:40]
					elif subtree_root.attributes:
						text = (
							subtree_root.attributes.get('placeholder', '')
							or subtree_root.attributes.get('title', '')
							or subtree_root.attributes.get('aria-label', '')
						)[:40]

					# Get y position and convert to pages
					y_pos = 0.0
					if subtree_root.snapshot_node and subtree_root.snapshot_node.bounds:
						y_pos = subtree_root.snapshot_node.bounds.y
					pages_down = round(y_pos / viewport_height, 1) if viewport_height > 0 else 0

					hidden.append(
						{
							'tag': subtree_root.tag_name or '?',
							'text': text or '(no label)',
							'pages': pages_down,
						}
					)

			for child in subtree_root.children_nodes or []:
				hidden.extend(collect_hidden_elements(child, viewport_height))

			for shadow_root in subtree_root.shadow_roots or []:
				hidden.extend(collect_hidden_elements(shadow_root, viewport_height))

			return hidden