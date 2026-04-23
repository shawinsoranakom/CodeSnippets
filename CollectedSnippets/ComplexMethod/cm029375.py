def _format_openapi_help(spec_data: bytes) -> str:
	"""Parse OpenAPI spec and render grouped endpoints."""
	try:
		spec = json.loads(spec_data)
	except (json.JSONDecodeError, ValueError):
		return ''

	paths = spec.get('paths', {})
	schemas = spec.get('components', {}).get('schemas', {})
	info = spec.get('info', {})

	lines: list[str] = []
	title = info.get('title', 'API')
	version = info.get('version', '')
	lines.append(f'{title} {version}'.strip())
	lines.append('')

	# Group by tag
	groups: dict[str, list[str]] = {}
	for path, methods in sorted(paths.items()):
		for method, details in sorted(methods.items()):
			if method in ('parameters', 'summary', 'description'):
				continue
			tags = details.get('tags', ['Other'])
			tag = tags[0] if tags else 'Other'
			summary = details.get('summary', '')

			# Build endpoint line
			parts = [f'  {method.upper():6s} {path}']
			if summary:
				parts.append(f'  # {summary}')

			# Parameters
			params = details.get('parameters', [])
			param_strs = []
			for p in params:
				name = p.get('name', '')
				required = p.get('required', False)
				marker = '*' if required else ''
				param_strs.append(f'{name}{marker}')
			if param_strs:
				parts.append(f'  params: {", ".join(param_strs)}')

			# Body example
			body_ref = _find_body_ref(spec, method, path)
			if body_ref:
				example = _generate_body_example(body_ref, schemas)
				parts.append(f"  body: '{example}'")

			groups.setdefault(tag, []).append('\n'.join(parts) if len(parts) > 1 else parts[0])

	for tag, endpoints in sorted(groups.items()):
		lines.append(f'[{tag}]')
		for ep in endpoints:
			lines.append(ep)
		lines.append('')

	return '\n'.join(lines)