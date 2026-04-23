def _build_model(schema: dict, name: str) -> type[BaseModel]:
	"""Build a pydantic model from an object-type JSON Schema node."""
	_check_unsupported(schema)

	properties = schema.get('properties', {})
	required_fields = set(schema.get('required', []))
	fields: dict[str, Any] = {}

	for prop_name, prop_schema in properties.items():
		prop_type = _resolve_type(prop_schema, f'{name}_{prop_name}')

		if prop_name in required_fields:
			default = ...
		elif 'default' in prop_schema:
			default = prop_schema['default']
		elif prop_schema.get('nullable', False):
			# _resolve_type already made the type include None
			default = None
		else:
			# Non-required, non-nullable, no explicit default.
			# Use a type-appropriate zero value for primitives/arrays;
			# fall back to None (with | None) for enums and nested objects
			# where no in-set or constructible default exists.
			json_type = prop_schema.get('type', 'string')
			if 'enum' in prop_schema:
				# Can't pick an arbitrary enum member as default — use None
				# so absent fields serialize as null, not an out-of-set value.
				prop_type = prop_type | None
				default = None
			elif json_type in _PRIMITIVE_DEFAULTS:
				default = _PRIMITIVE_DEFAULTS[json_type]
			elif json_type == 'array':
				default = []
			else:
				# Nested object or unknown — must allow None as sentinel
				prop_type = prop_type | None
				default = None

		field_kwargs: dict[str, Any] = {}
		if 'description' in prop_schema:
			field_kwargs['description'] = prop_schema['description']

		if isinstance(default, list) and not default:
			fields[prop_name] = (prop_type, Field(default_factory=list, **field_kwargs))
		else:
			fields[prop_name] = (prop_type, Field(default, **field_kwargs))

	return create_model(name, __base__=_StrictBase, **fields)