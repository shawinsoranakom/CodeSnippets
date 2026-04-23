def serialize_messages_for_cohere(messages: list[BaseMessage]) -> str:
		"""
		Serialize messages for Cohere models which expect a single message string.

		Cohere models use CohereChatRequest.message (string) instead of messages array.
		We combine all messages into a single conversation string.

		Args:
		    messages: List of browser-use messages

		Returns:
		    Single string containing the conversation
		"""
		conversation_parts = []

		for message in messages:
			content = ''

			if isinstance(message, UserMessage):
				if isinstance(message.content, str):
					content = message.content
				elif isinstance(message.content, list):
					# Extract text from content parts
					text_parts = []
					for part in message.content:
						if part.type == 'text':
							text_parts.append(part.text)
						elif part.type == 'image_url':
							# Cohere may not support images in all models, use a short placeholder
							# to avoid massive token usage from base64 data URIs
							if part.image_url.url.startswith('data:image/'):
								text_parts.append('[Image: base64_data]')
							else:
								text_parts.append('[Image: external_url]')
					content = ' '.join(text_parts)

				conversation_parts.append(f'User: {content}')

			elif isinstance(message, SystemMessage):
				if isinstance(message.content, str):
					content = message.content
				elif isinstance(message.content, list):
					# Extract text from content parts
					text_parts = []
					for part in message.content:
						if part.type == 'text':
							text_parts.append(part.text)
					content = ' '.join(text_parts)

				conversation_parts.append(f'System: {content}')

			elif isinstance(message, AssistantMessage):
				if isinstance(message.content, str):
					content = message.content
				elif isinstance(message.content, list):
					# Extract text from content parts
					text_parts = []
					for part in message.content:
						if part.type == 'text':
							text_parts.append(part.text)
						elif part.type == 'refusal':
							text_parts.append(f'[Refusal] {part.refusal}')
					content = ' '.join(text_parts)

				conversation_parts.append(f'Assistant: {content}')
			else:
				# Fallback
				conversation_parts.append(f'User: {str(message)}')

		return '\n\n'.join(conversation_parts)