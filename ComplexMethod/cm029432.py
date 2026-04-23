def _json_schema_to_python_type(self, schema: dict, model_name: str = 'NestedModel') -> Any:
		"""Convert JSON Schema type to Python type.

		Args:
			schema: JSON Schema definition
			model_name: Name for nested models

		Returns:
			Python type corresponding to the schema
		"""
		json_type = schema.get('type', 'string')

		# Basic type mapping
		type_mapping = {
			'string': str,
			'number': float,
			'integer': int,
			'boolean': bool,
			'array': list,
			'null': type(None),
		}

		# Handle enums (they're still strings)
		if 'enum' in schema:
			return str

		# Handle objects with nested properties
		if json_type == 'object':
			properties = schema.get('properties', {})
			if properties:
				# Create nested pydantic model for objects with properties
				nested_fields = {}
				required_fields = set(schema.get('required', []))

				for prop_name, prop_schema in properties.items():
					# Recursively process nested properties
					prop_type = self._json_schema_to_python_type(prop_schema, f'{model_name}_{prop_name}')

					# Determine if field is required and handle defaults
					if prop_name in required_fields:
						default = ...  # Required field
					else:
						# Optional field - make type optional and handle default
						prop_type = prop_type | None
						if 'default' in prop_schema:
							default = prop_schema['default']
						else:
							default = None

					# Add field with description if available
					field_kwargs = {}
					if 'description' in prop_schema:
						field_kwargs['description'] = prop_schema['description']

					nested_fields[prop_name] = (prop_type, Field(default, **field_kwargs))

				# Create a BaseModel class with proper configuration
				class ConfiguredBaseModel(BaseModel):
					model_config = ConfigDict(extra='forbid', validate_by_name=True, validate_by_alias=True)

				try:
					# Create and return nested pydantic model
					return create_model(model_name, __base__=ConfiguredBaseModel, **nested_fields)
				except Exception as e:
					logger.error(f'Failed to create nested model {model_name}: {e}')
					logger.debug(f'Fields: {nested_fields}')
					# Fallback to basic dict if model creation fails
					return dict
			else:
				# Object without properties - just return dict
				return dict

		# Handle arrays with specific item types
		if json_type == 'array':
			if 'items' in schema:
				# Get the item type recursively
				item_type = self._json_schema_to_python_type(schema['items'], f'{model_name}_item')
				# Return properly typed list
				return list[item_type]
			else:
				# Array without item type specification
				return list

		# Get base type for non-object types
		base_type = type_mapping.get(json_type, str)

		# Handle nullable/optional types
		if schema.get('nullable', False) or json_type == 'null':
			return base_type | None

		return base_type