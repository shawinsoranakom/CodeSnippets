def _extract_content(self, response) -> str:
		"""Extract text content from OCI response."""
		try:
			# The response is the direct OCI response object, not a dict
			if not hasattr(response, 'data'):
				raise ModelProviderError(message='Invalid response format: no data attribute', status_code=500, model=self.name)

			chat_response = response.data.chat_response

			# Handle different response types based on provider
			if hasattr(chat_response, 'text'):
				# Cohere response format - has direct text attribute
				return chat_response.text or ''
			elif hasattr(chat_response, 'choices') and chat_response.choices:
				# Generic response format - has choices array (Meta, xAI)
				choice = chat_response.choices[0]
				message = choice.message
				content_parts = message.content

				# Extract text from content parts
				text_parts = []
				for part in content_parts:
					if hasattr(part, 'text'):
						text_parts.append(part.text)

				return '\n'.join(text_parts) if text_parts else ''
			else:
				raise ModelProviderError(
					message=f'Unsupported response format: {type(chat_response).__name__}', status_code=500, model=self.name
				)

		except Exception as e:
			raise ModelProviderError(
				message=f'Failed to extract content from response: {str(e)}', status_code=500, model=self.name
			) from e