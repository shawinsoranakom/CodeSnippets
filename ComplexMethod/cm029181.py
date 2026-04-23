def serialize(message: BaseMessage) -> Message:
		"""Serialize a custom message to an Ollama Message."""

		if isinstance(message, UserMessage):
			text_content = OllamaMessageSerializer._extract_text_content(message.content)
			images = OllamaMessageSerializer._extract_images(message.content)

			ollama_message = Message(
				role='user',
				content=text_content if text_content else None,
			)

			if images:
				ollama_message.images = images

			return ollama_message

		elif isinstance(message, SystemMessage):
			text_content = OllamaMessageSerializer._extract_text_content(message.content)

			return Message(
				role='system',
				content=text_content if text_content else None,
			)

		elif isinstance(message, AssistantMessage):
			# Handle content
			text_content = None
			if message.content is not None:
				text_content = OllamaMessageSerializer._extract_text_content(message.content)

			ollama_message = Message(
				role='assistant',
				content=text_content if text_content else None,
			)

			# Handle tool calls
			if message.tool_calls:
				ollama_message.tool_calls = OllamaMessageSerializer._serialize_tool_calls(message.tool_calls)

			return ollama_message

		else:
			raise ValueError(f'Unknown message type: {type(message)}')