def _format_find_results(data: dict, selector: str) -> str:
	"""Format find_elements CDP result into human-readable text for the agent."""
	if not isinstance(data, dict):
		return f'find_elements returned unexpected result: {data}'

	elements = data.get('elements', [])
	total = data.get('total', 0)
	showing = data.get('showing', 0)

	if total == 0:
		return f'No elements found matching "{selector}".'

	lines = [f'Found {total} element{"s" if total != 1 else ""} matching "{selector}":']
	lines.append('')
	for el in elements:
		idx = el.get('index', 0)
		tag = el.get('tag', '?')
		text = el.get('text', '')
		attrs = el.get('attrs', {})
		children = el.get('children_count', 0)

		# Build element description
		parts = [f'[{idx}] <{tag}>']
		if text:
			# Collapse whitespace for readability
			display_text = ' '.join(text.split())
			if len(display_text) > 120:
				display_text = display_text[:120] + '...'
			parts.append(f'"{display_text}"')
		if attrs:
			attr_strs = [f'{k}="{v}"' for k, v in attrs.items()]
			parts.append('{' + ', '.join(attr_strs) + '}')
		parts.append(f'({children} children)')
		lines.append(' '.join(parts))

	if showing < total:
		lines.append(f'\nShowing {showing} of {total} total elements. Increase max_results to see more.')

	return '\n'.join(lines)