def find_file_input_near_element(
		self,
		node: 'EnhancedDOMTreeNode',
		max_height: int = 3,
		max_descendant_depth: int = 3,
	) -> 'EnhancedDOMTreeNode | None':
		"""Find the closest file input to the given element.

		Walks up the DOM tree (up to max_height levels), checking the node itself,
		its descendants (up to max_descendant_depth deep), and siblings at each level.

		Args:
			node: Starting DOM element
			max_height: Maximum levels to walk up the parent chain
			max_descendant_depth: Maximum depth to search descendants

		Returns:
			The nearest file input element, or None if not found
		"""
		from browser_use.dom.views import EnhancedDOMTreeNode

		def _find_in_descendants(n: EnhancedDOMTreeNode, depth: int) -> EnhancedDOMTreeNode | None:
			if depth < 0:
				return None
			if self.is_file_input(n):
				return n
			for child in n.children_nodes or []:
				result = _find_in_descendants(child, depth - 1)
				if result:
					return result
			return None

		current: EnhancedDOMTreeNode | None = node
		for _ in range(max_height + 1):
			if current is None:
				break
			# Check the current node itself
			if self.is_file_input(current):
				return current
			# Check all descendants of the current node
			result = _find_in_descendants(current, max_descendant_depth)
			if result:
				return result
			# Check all siblings and their descendants
			if current.parent_node:
				for sibling in current.parent_node.children_nodes or []:
					if sibling is current:
						continue
					if self.is_file_input(sibling):
						return sibling
					result = _find_in_descendants(sibling, max_descendant_depth)
					if result:
						return result
			current = current.parent_node
		return None