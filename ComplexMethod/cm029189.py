def serialize(message: BaseMessage) -> ChatCompletionMessageParam:
		"""Serialize a custom message to an OpenAI message param."""

		if isinstance(message, UserMessage):
			user_result: ChatCompletionUserMessageParam = {
				'role': 'user',
				'content': GroqMessageSerializer._serialize_user_content(message.content),
			}
			if message.name is not None:
				user_result['name'] = message.name
			return user_result

		elif isinstance(message, SystemMessage):
			system_result: ChatCompletionSystemMessageParam = {
				'role': 'system',
				'content': GroqMessageSerializer._serialize_system_content(message.content),
			}
			if message.name is not None:
				system_result['name'] = message.name
			return system_result

		elif isinstance(message, AssistantMessage):
			# Handle content serialization
			content = None
			if message.content is not None:
				content = GroqMessageSerializer._serialize_assistant_content(message.content)

			assistant_result: ChatCompletionAssistantMessageParam = {'role': 'assistant'}

			# Only add content if it's not None
			if content is not None:
				assistant_result['content'] = content

			if message.name is not None:
				assistant_result['name'] = message.name

			if message.tool_calls:
				assistant_result['tool_calls'] = [GroqMessageSerializer._serialize_tool_call(tc) for tc in message.tool_calls]

			return assistant_result

		else:
			raise ValueError(f'Unknown message type: {type(message)}')