def _is_autocomplete_field(node: EnhancedDOMTreeNode) -> bool:
	"""Detect if a node is an autocomplete/combobox field from its attributes."""
	attrs = node.attributes or {}
	if attrs.get('role') == 'combobox':
		return True
	aria_ac = attrs.get('aria-autocomplete', '')
	if aria_ac and aria_ac != 'none':
		return True
	if attrs.get('list'):
		return True
	haspopup = attrs.get('aria-haspopup', '')
	if haspopup and haspopup != 'false' and (attrs.get('aria-controls') or attrs.get('aria-owns')):
		return True
	return False