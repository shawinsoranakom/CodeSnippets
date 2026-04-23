def _filter_sensitive_data_from_dict(
		self, data: dict[str, Any], sensitive_data: dict[str, str | dict[str, str]] | None
	) -> dict[str, Any]:
		"""Recursively filter sensitive data from a dictionary"""
		if not sensitive_data:
			return data

		filtered_data = {}
		for key, value in data.items():
			if isinstance(value, str):
				filtered_data[key] = self._filter_sensitive_data_from_string(value, sensitive_data)
			elif isinstance(value, dict):
				filtered_data[key] = self._filter_sensitive_data_from_dict(value, sensitive_data)
			elif isinstance(value, list):
				filtered_data[key] = [
					self._filter_sensitive_data_from_string(item, sensitive_data)
					if isinstance(item, str)
					else self._filter_sensitive_data_from_dict(item, sensitive_data)
					if isinstance(item, dict)
					else item
					for item in value
				]
			else:
				filtered_data[key] = value
		return filtered_data