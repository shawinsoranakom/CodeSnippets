def count_targets_in_tree(node, targets=None):
			if targets is None:
				targets = set()
			# SimplifiedNode has original_node which is an EnhancedDOMTreeNode
			if hasattr(node, 'original_node') and node.original_node and node.original_node.target_id:
				targets.add(node.original_node.target_id)
			# Recursively check children
			if hasattr(node, 'children') and node.children:
				for child in node.children:
					count_targets_in_tree(child, targets)
			return targets