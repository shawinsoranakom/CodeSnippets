def _substitute_in_dict(self, data: dict, replacements: dict[str, str]) -> int:
		"""Recursively substitute values in a dictionary, returns count of substitutions made"""
		count = 0
		for key, value in data.items():
			if isinstance(value, str):
				# Replace if exact match
				if value in replacements:
					data[key] = replacements[value]
					count += 1
			elif isinstance(value, dict):
				# Recurse into nested dicts
				count += self._substitute_in_dict(value, replacements)
			elif isinstance(value, list):
				# Handle lists
				for i, item in enumerate(value):
					if isinstance(item, str) and item in replacements:
						value[i] = replacements[item]
						count += 1
					elif isinstance(item, dict):
						count += self._substitute_in_dict(item, replacements)
		return count