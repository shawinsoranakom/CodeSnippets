def test_cache_basic_functionality(self):
		"""Test basic cache functionality for all message types."""
		# Test cache with different message types
		messages: list[BaseMessage] = [
			SystemMessage(content='System message!', cache=True),
			UserMessage(content='User message!', cache=True),
			AssistantMessage(content='Assistant message!', cache=False),
		]

		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages)

		assert len(anthropic_messages) == 2
		assert isinstance(system_message, list)
		assert isinstance(anthropic_messages[0]['content'], list)
		assert isinstance(anthropic_messages[1]['content'], str)

		# Test cache with assistant message
		agent_messages: list[BaseMessage] = [
			SystemMessage(content='System message!'),
			UserMessage(content='User message!'),
			AssistantMessage(content='Assistant message!', cache=True),
		]

		anthropic_messages, system_message = AnthropicMessageSerializer.serialize_messages(agent_messages)

		assert isinstance(system_message, str)
		assert isinstance(anthropic_messages[0]['content'], str)
		assert isinstance(anthropic_messages[1]['content'], list)