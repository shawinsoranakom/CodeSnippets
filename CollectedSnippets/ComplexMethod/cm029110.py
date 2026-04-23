def is_hidden_by_threshold(element: EnhancedDOMTreeNode) -> bool:
			"""Check if element is hidden by viewport threshold (not CSS)."""
			if element.is_visible or not element.snapshot_node or not element.snapshot_node.bounds:
				return False

			computed_styles = element.snapshot_node.computed_styles or {}
			display = computed_styles.get('display', '').lower()
			visibility = computed_styles.get('visibility', '').lower()
			opacity = computed_styles.get('opacity', '1')

			css_hidden = display == 'none' or visibility == 'hidden'
			try:
				css_hidden = css_hidden or float(opacity) <= 0
			except (ValueError, TypeError):
				pass

			return not css_hidden