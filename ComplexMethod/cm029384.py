def _extract_body(self, payload: dict[str, Any]) -> str:
		"""Extract email body from payload"""
		body = ''

		if payload.get('body', {}).get('data'):
			# Simple email body
			body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
		elif payload.get('parts'):
			# Multi-part email
			for part in payload['parts']:
				if part['mimeType'] == 'text/plain' and part.get('body', {}).get('data'):
					part_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
					body += part_body
				elif part['mimeType'] == 'text/html' and not body and part.get('body', {}).get('data'):
					# Fallback to HTML if no plain text
					body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

		return body