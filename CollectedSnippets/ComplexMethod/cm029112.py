def has_any_hidden_content(subtree_root: EnhancedDOMTreeNode) -> bool:
			"""Check if there's any hidden content (interactive or not) in subtree."""
			if is_hidden_by_threshold(subtree_root):
				return True

			for child in subtree_root.children_nodes or []:
				if has_any_hidden_content(child):
					return True

			for shadow_root in subtree_root.shadow_roots or []:
				if has_any_hidden_content(shadow_root):
					return True

			return False