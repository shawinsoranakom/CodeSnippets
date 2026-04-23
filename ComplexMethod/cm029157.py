def test_cache_cleaning_last_message_only(self):
		"""Test that only the last cache=True message remains cached."""
		# Create multiple messages with cache=True
		messages_list: list[BaseMessage] = [
			UserMessage(content='First user message', cache=True),
			AssistantMessage(content='First assistant message', cache=True),
			UserMessage(content='Second user message', cache=True),
			AssistantMessage(content='Second assistant message', cache=False),
			UserMessage(content='Third user message', cache=True),  # This should be the only one cached
		]

		# Test the cleaning method directly (only accepts non-system messages)
		normal_messages = cast(list[NonSystemMessage], [msg for msg in messages_list if not isinstance(msg, SystemMessage)])
		cleaned_messages = AnthropicMessageSerializer._clean_cache_messages(normal_messages)

		# Verify only the last cache=True message remains cached
		assert not cleaned_messages[0].cache  # First user message should be uncached
		assert not cleaned_messages[1].cache  # First assistant message should be uncached
		assert not cleaned_messages[2].cache  # Second user message should be uncached
		assert not cleaned_messages[3].cache  # Second assistant message was already uncached
		assert cleaned_messages[4].cache  # Third user message should remain cached

		# Test through serialize_messages
		serialized_messages, system_message = AnthropicMessageSerializer.serialize_messages(messages_list)

		# Count how many messages have list content (indicating caching)
		cached_content_count = sum(1 for msg in serialized_messages if isinstance(msg['content'], list))

		# Only one message should have cached content
		assert cached_content_count == 1

		# The last message should be the cached one
		assert isinstance(serialized_messages[-1]['content'], list)