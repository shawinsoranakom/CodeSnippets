def test_process_user_and_assistant_messages_with_url_shortening(self, agent: Agent):
		"""Test URL shortening in both UserMessage and AssistantMessage."""
		user_content = f'I need to access {SUPER_LONG_URL} for the API documentation'
		assistant_content = f'I will help you navigate to {SUPER_LONG_URL} to retrieve the documentation'

		messages: list[BaseMessage] = [UserMessage(content=user_content), AssistantMessage(content=assistant_content)]

		# Process messages (modifies messages in-place and returns URL mappings)
		url_mappings = agent._process_messsages_and_replace_long_urls_shorter_ones(messages)

		# Verify URL was shortened in both messages
		user_processed_content = messages[0].content or ''
		assistant_processed_content = messages[1].content or ''

		assert user_processed_content != user_content
		assert assistant_processed_content != assistant_content
		assert 'https://documentation.example-company.com' in user_processed_content
		assert 'https://documentation.example-company.com' in assistant_processed_content
		assert len(user_processed_content) < len(user_content)
		assert len(assistant_processed_content) < len(assistant_content)

		# Verify URL mapping was returned (should be same shortened URL for both occurrences)
		assert len(url_mappings) == 1
		shortened_url = next(iter(url_mappings.keys()))
		assert url_mappings[shortened_url] == SUPER_LONG_URL