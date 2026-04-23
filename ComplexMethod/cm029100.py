def _get_element_position(self, element: 'EnhancedDOMTreeNode') -> int:
		"""Get the position of an element among its siblings with the same tag name.
		Returns 0 if it's the only element of its type, otherwise returns 1-based index."""
		if not element.parent_node or not element.parent_node.children_nodes:
			return 0

		same_tag_siblings = [
			child
			for child in element.parent_node.children_nodes
			if child.node_type == NodeType.ELEMENT_NODE and child.node_name.lower() == element.node_name.lower()
		]

		if len(same_tag_siblings) <= 1:
			return 0  # No index needed if it's the only one

		try:
			# XPath is 1-indexed
			position = same_tag_siblings.index(element) + 1
			return position
		except ValueError:
			return 0