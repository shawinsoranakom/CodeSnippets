def _example_value(prop: dict, schemas: dict) -> object:
	"""Generate a placeholder value for an OpenAPI property."""
	if '$ref' in prop:
		ref_name = prop['$ref'].rsplit('/', 1)[-1]
		if ref_name in schemas:
			return _generate_body_example_dict(ref_name, schemas)
		return {}

	t = prop.get('type', 'string')
	fmt = prop.get('format', '')
	enum = prop.get('enum')

	if enum:
		return enum[0]
	if t == 'string':
		if fmt == 'uri' or fmt == 'url':
			return 'https://example.com'
		if fmt == 'date-time':
			return '2025-01-01T00:00:00Z'
		if 'email' in fmt:
			return 'user@example.com'
		return '...'
	if t == 'integer':
		return 0
	if t == 'number':
		return 0.0
	if t == 'boolean':
		return False
	if t == 'array':
		items = prop.get('items', {})
		return [_example_value(items, schemas)]
	if t == 'object':
		props = prop.get('properties', {})
		return {k: _example_value(v, schemas) for k, v in props.items()}
	return '...'