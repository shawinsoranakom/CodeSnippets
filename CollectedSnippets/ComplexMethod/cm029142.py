def ensure_additional_properties_false(obj: Any) -> None:
			"""Ensure all objects have additionalProperties: false"""
			if isinstance(obj, dict):
				# If it's an object type, ensure additionalProperties is false
				if obj.get('type') == 'object':
					obj['additionalProperties'] = False

				# Recursively apply to all values
				for value in obj.values():
					if isinstance(value, (dict, list)):
						ensure_additional_properties_false(value)
			elif isinstance(obj, list):
				for item in obj:
					if isinstance(item, (dict, list)):
						ensure_additional_properties_false(item)