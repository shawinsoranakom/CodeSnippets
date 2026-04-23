def convert_json_schema_to_pydantic(schema: dict[str, Any], model_name: str = 'SkillOutput') -> type[BaseModel]:
	"""Convert a JSON schema to a pydantic model

	Args:
		schema: JSON schema dictionary (OpenAPI/JSON Schema format)
		model_name: Name for the generated pydantic model

	Returns:
		A pydantic BaseModel class matching the schema

	Note:
		This is a simplified converter that handles basic types.
		For complex nested schemas, consider using datamodel-code-generator.
	"""
	if not schema or 'properties' not in schema:
		# Return empty model if no schema
		return create_model(model_name, __base__=BaseModel)

	fields: dict[str, Any] = {}
	properties = schema.get('properties', {})
	required_fields = set(schema.get('required', []))

	for field_name, field_schema in properties.items():
		# Get the field type
		field_type_str = field_schema.get('type', 'string')
		field_description = field_schema.get('description')

		# Map JSON schema types to Python types
		python_type: Any = str  # default

		if field_type_str == 'string':
			python_type = str
		elif field_type_str == 'number':
			python_type = float
		elif field_type_str == 'integer':
			python_type = int
		elif field_type_str == 'boolean':
			python_type = bool
		elif field_type_str == 'object':
			python_type = dict[str, Any]
		elif field_type_str == 'array':
			# Check if items type is specified
			items_schema = field_schema.get('items', {})
			items_type = items_schema.get('type', 'string')

			if items_type == 'string':
				python_type = list[str]
			elif items_type == 'number':
				python_type = list[float]
			elif items_type == 'integer':
				python_type = list[int]
			elif items_type == 'boolean':
				python_type = list[bool]
			elif items_type == 'object':
				python_type = list[dict[str, Any]]
			else:
				python_type = list[Any]

		# Make optional if not required
		is_required = field_name in required_fields
		if not is_required:
			python_type = python_type | None  # type: ignore

		# Create field with description
		field_kwargs = {}
		if field_description:
			field_kwargs['description'] = field_description

		if is_required:
			fields[field_name] = (python_type, Field(**field_kwargs))
		else:
			fields[field_name] = (python_type, Field(default=None, **field_kwargs))

	# Create and return the model
	return create_model(model_name, __base__=BaseModel, **fields)