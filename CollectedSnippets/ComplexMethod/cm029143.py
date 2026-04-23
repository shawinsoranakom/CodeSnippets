def remove_forbidden_fields(obj: Any) -> None:
				"""Recursively remove minItems/min_items and default values"""
				if isinstance(obj, dict):
					# Remove forbidden keys
					if remove_min_items:
						obj.pop('minItems', None)
						obj.pop('min_items', None)
					if remove_defaults:
						obj.pop('default', None)
					# Recursively process all values
					for value in obj.values():
						if isinstance(value, (dict, list)):
							remove_forbidden_fields(value)
				elif isinstance(obj, list):
					for item in obj:
						if isinstance(item, (dict, list)):
							remove_forbidden_fields(item)