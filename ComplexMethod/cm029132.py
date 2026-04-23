def _filter_tree_recursive(self, node: SimplifiedNode, active_bounds: PropagatingBounds | None = None, depth: int = 0):
		"""
		Recursively filter tree with bounding box propagation.
		Bounds propagate to ALL descendants until overridden.
		"""

		# Check if this node should be excluded by active bounds
		if active_bounds and self._should_exclude_child(node, active_bounds):
			node.excluded_by_parent = True
			# Important: Still check if this node starts NEW propagation

		# Check if this node starts new propagation (even if excluded!)
		new_bounds = None
		tag = node.original_node.tag_name.lower()
		role = node.original_node.attributes.get('role') if node.original_node.attributes else None
		attributes = {
			'tag': tag,
			'role': role,
		}
		# Check if this element matches any propagating element pattern
		if self._is_propagating_element(attributes):
			# This node propagates bounds to ALL its descendants
			if node.original_node.snapshot_node and node.original_node.snapshot_node.bounds:
				new_bounds = PropagatingBounds(
					tag=tag,
					bounds=node.original_node.snapshot_node.bounds,
					node_id=node.original_node.node_id,
					depth=depth,
				)

		# Propagate to ALL children
		# Use new_bounds if this node starts propagation, otherwise continue with active_bounds
		propagate_bounds = new_bounds if new_bounds else active_bounds

		for child in node.children:
			self._filter_tree_recursive(child, propagate_bounds, depth + 1)