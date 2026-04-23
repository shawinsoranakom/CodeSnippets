def _should_exclude_child(self, node: SimplifiedNode, active_bounds: PropagatingBounds) -> bool:
		"""
		Determine if child should be excluded based on propagating bounds.
		"""

		# Never exclude text nodes - we always want to preserve text content
		if node.original_node.node_type == NodeType.TEXT_NODE:
			return False

		# Get child bounds
		if not node.original_node.snapshot_node or not node.original_node.snapshot_node.bounds:
			return False  # No bounds = can't determine containment

		child_bounds = node.original_node.snapshot_node.bounds

		# Check containment with configured threshold
		if not self._is_contained(child_bounds, active_bounds.bounds, self.containment_threshold):
			return False  # Not sufficiently contained

		# EXCEPTION RULES - Keep these even if contained:

		child_tag = node.original_node.tag_name.lower()
		child_role = node.original_node.attributes.get('role') if node.original_node.attributes else None
		child_attributes = {
			'tag': child_tag,
			'role': child_role,
		}

		# 1. Never exclude form elements (they need individual interaction)
		if child_tag in ['input', 'select', 'textarea', 'label']:
			return False

		# 2. Keep if child is also a propagating element
		# (might have stopPropagation, e.g., button in button)
		if self._is_propagating_element(child_attributes):
			return False

		# 3. Keep if has explicit onclick handler
		if node.original_node.attributes and 'onclick' in node.original_node.attributes:
			return False

		# 4. Keep if has aria-label suggesting it's independently interactive
		if node.original_node.attributes:
			aria_label = node.original_node.attributes.get('aria-label')
			if aria_label and aria_label.strip():
				# Has meaningful aria-label, likely interactive
				return False

		# 5. Keep if has role suggesting interactivity
		if node.original_node.attributes:
			role = node.original_node.attributes.get('role')
			if role in ['button', 'link', 'checkbox', 'radio', 'tab', 'menuitem', 'option']:
				return False

		# Default: exclude this child
		return True