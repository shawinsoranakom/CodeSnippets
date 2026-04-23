def _format_element_for_error(self, elem: DOMInteractedElement | None) -> str:
		"""Format element info for error messages during history rerun."""
		if elem is None:
			return '<no element recorded>'

		parts = [f'<{elem.node_name}>']

		# Add key identifying attributes
		if elem.attributes:
			for key in ['name', 'id', 'aria-label', 'type']:
				if key in elem.attributes and elem.attributes[key]:
					parts.append(f'{key}="{elem.attributes[key]}"')

		# Add hash info
		parts.append(f'hash={elem.element_hash}')
		if elem.stable_hash:
			parts.append(f'stable_hash={elem.stable_hash}')

		# Add xpath (truncated)
		if elem.x_path:
			xpath_short = elem.x_path if len(elem.x_path) <= 60 else f'...{elem.x_path[-57:]}'
			parts.append(f'xpath="{xpath_short}"')

		return ' '.join(parts)