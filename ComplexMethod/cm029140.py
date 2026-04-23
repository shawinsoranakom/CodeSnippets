def _make_strict_compatible(schema: dict[str, Any] | list[Any]) -> None:
		"""Ensure all properties are required for OpenAI strict mode"""
		if isinstance(schema, dict):
			# First recursively apply to nested objects
			for key, value in schema.items():
				if isinstance(value, (dict, list)) and key != 'required':
					SchemaOptimizer._make_strict_compatible(value)

			# Then update required for this level
			if 'properties' in schema and 'type' in schema and schema['type'] == 'object':
				# Add all properties to required array
				all_props = list(schema['properties'].keys())
				schema['required'] = all_props  # Set all properties as required

		elif isinstance(schema, list):
			for item in schema:
				SchemaOptimizer._make_strict_compatible(item)