def _extract_content_text(self, choice: dict[str, Any]) -> str:
		message = choice.get('message', {})
		content = message.get('content')

		if isinstance(content, list):
			text_parts = []
			for part in content:
				if isinstance(part, dict):
					if part.get('type') == 'text' and 'text' in part:
						text_parts.append(part.get('text', ''))
					elif 'content' in part:
						text_parts.append(str(part['content']))
			return ''.join(text_parts)

		if isinstance(content, dict):
			return json.dumps(content)

		return content or ''