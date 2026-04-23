def clean_schema(obj: Any) -> Any:
			if isinstance(obj, dict):
				# Remove unsupported properties
				cleaned = {}
				for key, value in obj.items():
					if key not in ['additionalProperties', 'title', 'default']:
						cleaned_value = clean_schema(value)
						# Handle empty object properties - Gemini doesn't allow empty OBJECT types
						if (
							key == 'properties'
							and isinstance(cleaned_value, dict)
							and len(cleaned_value) == 0
							and isinstance(obj.get('type', ''), str)
							and obj.get('type', '').upper() == 'OBJECT'
						):
							# Convert empty object to have at least one property
							cleaned['properties'] = {'_placeholder': {'type': 'string'}}
						else:
							cleaned[key] = cleaned_value

				# If this is an object type with empty properties, add a placeholder
				if (
					isinstance(cleaned.get('type', ''), str)
					and cleaned.get('type', '').upper() == 'OBJECT'
					and 'properties' in cleaned
					and isinstance(cleaned['properties'], dict)
					and len(cleaned['properties']) == 0
				):
					cleaned['properties'] = {'_placeholder': {'type': 'string'}}

				# Also remove 'title' from the required list if it exists
				if 'required' in cleaned and isinstance(cleaned.get('required'), list):
					cleaned['required'] = [p for p in cleaned['required'] if p != 'title']

				return cleaned
			elif isinstance(obj, list):
				return [clean_schema(item) for item in obj]
			return obj