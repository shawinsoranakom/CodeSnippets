def _optimize_tree(self, node: SimplifiedNode | None) -> SimplifiedNode | None:
		"""Step 2: Optimize tree structure."""
		if not node:
			return None

		# Process children
		optimized_children = []
		for child in node.children:
			optimized_child = self._optimize_tree(child)
			if optimized_child:
				optimized_children.append(optimized_child)

		node.children = optimized_children

		# Keep meaningful nodes
		is_visible = node.original_node.snapshot_node and node.original_node.is_visible

		# EXCEPTION: File inputs are often hidden with opacity:0 but are still functional
		is_file_input = (
			node.original_node.tag_name
			and node.original_node.tag_name.lower() == 'input'
			and node.original_node.attributes
			and node.original_node.attributes.get('type') == 'file'
		)

		if (
			is_visible  # Keep all visible nodes
			or node.original_node.is_actually_scrollable
			or node.original_node.node_type == NodeType.TEXT_NODE
			or node.children
			or is_file_input  # Keep file inputs even if not visible
		):
			return node

		return None