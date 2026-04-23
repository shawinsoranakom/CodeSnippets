def clean_schema(obj: Any, parent_key: str | None = None) -> Any:
			if isinstance(obj, dict):
				# Remove unsupported properties
				cleaned = {}
				for key, value in obj.items():
					# Only strip 'title' when it's a JSON Schema metadata field (not inside 'properties')
					# 'title' as a metadata field appears at schema level, not as a property name
					is_metadata_title = key == 'title' and parent_key != 'properties'
					if key not in ['additionalProperties', 'default'] and not is_metadata_title:
						cleaned_value = clean_schema(value, parent_key=key)
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

				return cleaned
			elif isinstance(obj, list):
				return [clean_schema(item, parent_key=parent_key) for item in obj]
			return obj