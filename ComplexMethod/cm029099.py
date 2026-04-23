def xpath(self) -> str:
		"""Generate XPath for this DOM node, stopping at shadow boundaries or iframes."""
		segments = []
		current_element = self

		while current_element and (
			current_element.node_type == NodeType.ELEMENT_NODE or current_element.node_type == NodeType.DOCUMENT_FRAGMENT_NODE
		):
			# just pass through shadow roots
			if current_element.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
				current_element = current_element.parent_node
				continue

			# stop ONLY if we hit iframe
			if current_element.parent_node and current_element.parent_node.node_name.lower() == 'iframe':
				break

			position = self._get_element_position(current_element)
			tag_name = current_element.node_name.lower()
			xpath_index = f'[{position}]' if position > 0 else ''
			segments.insert(0, f'{tag_name}{xpath_index}')

			current_element = current_element.parent_node

		return '/'.join(segments)