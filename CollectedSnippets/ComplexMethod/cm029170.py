def serialize(message: BaseMessage) -> dict[str, Any] | SystemMessage:
		"""Serialize a custom message to AWS Bedrock format."""

		if isinstance(message, UserMessage):
			return {
				'role': 'user',
				'content': AWSBedrockMessageSerializer._serialize_user_content(message.content),
			}

		elif isinstance(message, SystemMessage):
			# System messages are handled separately in AWS Bedrock
			return message

		elif isinstance(message, AssistantMessage):
			content_blocks: list[dict[str, Any]] = []

			# Add content blocks if present
			if message.content is not None:
				content_blocks.extend(AWSBedrockMessageSerializer._serialize_assistant_content(message.content))

			# Add tool use blocks if present
			if message.tool_calls:
				for tool_call in message.tool_calls:
					content_blocks.append(AWSBedrockMessageSerializer._serialize_tool_call(tool_call))

			# AWS Bedrock requires at least one content block
			if not content_blocks:
				content_blocks = [{'text': ''}]

			return {
				'role': 'assistant',
				'content': content_blocks,
			}

		else:
			raise ValueError(f'Unknown message type: {type(message)}')