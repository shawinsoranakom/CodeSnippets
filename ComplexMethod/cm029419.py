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