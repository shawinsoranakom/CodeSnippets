def _clean_cache_messages(messages: list[NonSystemMessage]) -> list[NonSystemMessage]:
		"""Clean cache settings so only the last cache=True message remains cached.

		Because of how Claude caching works, only the last cache message matters.
		This method automatically removes cache=True from all messages except the last one.

		Args:
			messages: List of non-system messages to clean

		Returns:
			List of messages with cleaned cache settings
		"""
		if not messages:
			return messages

		# Create a copy to avoid modifying the original
		cleaned_messages = [msg.model_copy(deep=True) for msg in messages]

		# Find the last message with cache=True
		last_cache_index = -1
		for i in range(len(cleaned_messages) - 1, -1, -1):
			if cleaned_messages[i].cache:
				last_cache_index = i
				break

		# If we found a cached message, disable cache for all others
		if last_cache_index != -1:
			for i, msg in enumerate(cleaned_messages):
				if i != last_cache_index and msg.cache:
					# Set cache to False for all messages except the last cached one
					msg.cache = False

		return cleaned_messages