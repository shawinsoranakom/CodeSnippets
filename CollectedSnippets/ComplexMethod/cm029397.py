def _detect_sensitive_key_name(text: str, sensitive_data: dict[str, str | dict[str, str]] | None) -> str | None:
	"""Detect which sensitive key name corresponds to the given text value."""
	if not sensitive_data or not text:
		return None

	# Collect all sensitive values and their keys
	for domain_or_key, content in sensitive_data.items():
		if isinstance(content, dict):
			# New format: {domain: {key: value}}
			for key, value in content.items():
				if value and value == text:
					return key
		elif content:  # Old format: {key: value}
			if content == text:
				return domain_or_key

	return None