def serialize(messages: list[BaseMessage]) -> list[dict[str, Any]]:
		result: list[dict[str, Any]] = []
		for msg in messages:
			if isinstance(msg, UserMessage):
				d: dict[str, Any] = {'role': 'user'}
				d['content'] = LiteLLMMessageSerializer._serialize_user_content(msg.content)
				if msg.name is not None:
					d['name'] = msg.name
				result.append(d)

			elif isinstance(msg, SystemMessage):
				d = {'role': 'system'}
				d['content'] = LiteLLMMessageSerializer._serialize_system_content(msg.content)
				if msg.name is not None:
					d['name'] = msg.name
				result.append(d)

			elif isinstance(msg, AssistantMessage):
				d = {'role': 'assistant'}
				d['content'] = LiteLLMMessageSerializer._serialize_assistant_content(msg.content)
				if msg.name is not None:
					d['name'] = msg.name
				if msg.tool_calls:
					d['tool_calls'] = [
						{
							'id': tc.id,
							'type': 'function',
							'function': {
								'name': tc.function.name,
								'arguments': tc.function.arguments,
							},
						}
						for tc in msg.tool_calls
					]
				result.append(d)
		return result