def _detect_in_action(
	action_dict: dict,
	element: DOMInteractedElement | None,
	detected: dict[str, DetectedVariable],
	detected_values: set[str],
) -> None:
	"""Detect variables in a single action using element context"""

	# Extract action type and parameters
	for action_type, params in action_dict.items():
		if not isinstance(params, dict):
			continue

		# Check fields that commonly contain variables
		fields_to_check = ['text', 'query']

		for field in fields_to_check:
			if field not in params:
				continue

			value = params[field]
			if not isinstance(value, str) or not value.strip():
				continue

			# Skip if we already detected this exact value
			if value in detected_values:
				continue

			# Try to detect variable type (with element context)
			var_info = _detect_variable_type(value, element)
			if not var_info:
				continue

			var_name, var_format = var_info

			# Ensure unique variable name
			var_name = _ensure_unique_name(var_name, detected)

			# Add detected variable
			detected[var_name] = DetectedVariable(
				name=var_name,
				original_value=value,
				type='string',
				format=var_format,
			)

			detected_values.add(value)