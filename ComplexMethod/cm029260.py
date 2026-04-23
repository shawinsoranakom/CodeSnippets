def _get_sensitive_data_description(self, current_page_url) -> str:
		sensitive_data = self.sensitive_data
		if not sensitive_data:
			return ''

		# Collect placeholders for sensitive data
		placeholders: set[str] = set()

		for key, value in sensitive_data.items():
			if isinstance(value, dict):
				# New format: {domain: {key: value}}
				if current_page_url and match_url_with_domain_pattern(current_page_url, key, True):
					placeholders.update(value.keys())
			else:
				# Old format: {key: value}
				placeholders.add(key)

		if placeholders:
			placeholder_list = sorted(list(placeholders))
			# Format as bullet points for clarity
			formatted_placeholders = '\n'.join(f'  - {p}' for p in placeholder_list)

			info = 'SENSITIVE DATA - Use these placeholders for secure input:\n'
			info += f'{formatted_placeholders}\n\n'
			info += 'IMPORTANT: When entering sensitive values, you MUST wrap the placeholder name in <secret> tags.\n'
			info += f'Example: To enter the value for "{placeholder_list[0]}", use: <secret>{placeholder_list[0]}</secret>\n'
			info += 'The system will automatically replace these tags with the actual secret values.'
			return info

		return ''