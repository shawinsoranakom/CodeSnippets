def convert_parameters_to_pydantic(parameters: list[ParameterSchema], model_name: str = 'SkillParameters') -> type[BaseModel]:
	"""Convert a list of ParameterSchema to a pydantic model for structured output

	Args:
		parameters: List of parameter schemas from the skill API
		model_name: Name for the generated pydantic model

	Returns:
		A pydantic BaseModel class with fields matching the parameter schemas
	"""
	if not parameters:
		# Return empty model if no parameters
		return create_model(model_name, __base__=BaseModel)

	fields: dict[str, Any] = {}

	for param in parameters:
		# Map parameter type string to Python types
		python_type: Any = str  # default

		param_type = param.type

		if param_type == 'string':
			python_type = str
		elif param_type == 'number':
			python_type = float
		elif param_type == 'boolean':
			python_type = bool
		elif param_type == 'object':
			python_type = dict[str, Any]
		elif param_type == 'array':
			python_type = list[Any]
		elif param_type == 'cookie':
			python_type = str  # Treat cookies as strings

		# Check if parameter is required (defaults to True if not specified)
		is_required = param.required if param.required is not None else True

		# Make optional if not required
		if not is_required:
			python_type = python_type | None  # type: ignore

		# Create field with description
		field_kwargs = {}
		if param.description:
			field_kwargs['description'] = param.description

		if is_required:
			fields[param.name] = (python_type, Field(**field_kwargs))
		else:
			fields[param.name] = (python_type, Field(default=None, **field_kwargs))

	# Create and return the model
	return create_model(model_name, __base__=BaseModel, **fields)