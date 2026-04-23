def _replace_sensitive_data(
		self, params: BaseModel, sensitive_data: dict[str, Any], current_url: str | None = None
	) -> BaseModel:
		"""
		Replaces sensitive data placeholders in params with actual values.

		Args:
			params: The parameter object containing <secret>placeholder</secret> tags
			sensitive_data: Dictionary of sensitive data, either in old format {key: value}
						   or new format {domain_pattern: {key: value}}
			current_url: Optional current URL for domain matching

		Returns:
			BaseModel: The parameter object with placeholders replaced by actual values
		"""
		secret_pattern = re.compile(r'<secret>(.*?)</secret>')

		# Set to track all missing placeholders across the full object
		all_missing_placeholders = set()
		# Set to track successfully replaced placeholders
		replaced_placeholders = set()

		# Process sensitive data based on format and current URL
		applicable_secrets = {}

		for domain_or_key, content in sensitive_data.items():
			if isinstance(content, dict):
				# New format: {domain_pattern: {key: value}}
				# Only include secrets for domains that match the current URL
				if current_url and not is_new_tab_page(current_url):
					# it's a real url, check it using our custom allowed_domains scheme://*.example.com glob matching
					if match_url_with_domain_pattern(current_url, domain_or_key):
						applicable_secrets.update(content)
			else:
				# Old format: {key: value}, expose to all domains (only allowed for legacy reasons)
				applicable_secrets[domain_or_key] = content

		# Filter out empty values
		applicable_secrets = {k: v for k, v in applicable_secrets.items() if v}

		def recursively_replace_secrets(value: str | dict | list) -> str | dict | list:
			if isinstance(value, str):
				# 1. Handle tagged secrets: <secret>label</secret>
				matches = secret_pattern.findall(value)
				for placeholder in matches:
					if placeholder in applicable_secrets:
						# generate a totp code if secret is suffixed with bu_2fa_code
						if placeholder.endswith('bu_2fa_code'):
							totp = pyotp.TOTP(applicable_secrets[placeholder], digits=6)
							replacement_value = totp.now()
						else:
							replacement_value = applicable_secrets[placeholder]

						value = value.replace(f'<secret>{placeholder}</secret>', replacement_value)
						replaced_placeholders.add(placeholder)
					else:
						# Keep track of missing placeholders
						all_missing_placeholders.add(placeholder)

				# 2. Handle literal secrets: "user_name" (no tags)
				# This handles cases where the LLM forgets to use tags but uses the exact placeholder name
				if value in applicable_secrets:
					placeholder_name = value
					if placeholder_name.endswith('bu_2fa_code'):
						totp = pyotp.TOTP(applicable_secrets[placeholder_name], digits=6)
						value = totp.now()
					else:
						value = applicable_secrets[placeholder_name]
					replaced_placeholders.add(placeholder_name)

				return value
			elif isinstance(value, dict):
				return {k: recursively_replace_secrets(v) for k, v in value.items()}
			elif isinstance(value, list):
				return [recursively_replace_secrets(v) for v in value]
			return value

		params_dump = params.model_dump()
		processed_params = recursively_replace_secrets(params_dump)

		# Log sensitive data usage
		self._log_sensitive_data_usage(replaced_placeholders, current_url)

		# Log a warning if any placeholders are missing
		if all_missing_placeholders:
			logger.warning(f'Missing or empty keys in sensitive_data dictionary: {", ".join(all_missing_placeholders)}')

		return type(params).model_validate(processed_params)