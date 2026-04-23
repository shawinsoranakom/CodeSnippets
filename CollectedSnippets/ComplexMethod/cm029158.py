def test_cache_only_last_block_in_message(self):
		"""Test that only the LAST block in a message gets cache_control when cache=True."""
		# Test UserMessage with multiple text parts
		user_msg = UserMessage(
			content=[
				ContentPartTextParam(text='Part 1', type='text'),
				ContentPartTextParam(text='Part 2', type='text'),
				ContentPartTextParam(text='Part 3', type='text'),
			],
			cache=True,
		)
		serialized = AnthropicMessageSerializer.serialize(user_msg)
		assert isinstance(serialized['content'], list)
		content_blocks = serialized['content']

		# Count blocks with cache_control
		# Note: content_blocks are dicts at runtime despite type annotations
		cache_count = sum(1 for block in content_blocks if block.get('cache_control') is not None)  # type: ignore[attr-defined]
		assert cache_count == 1, f'Expected 1 cache_control block, got {cache_count}'

		# Verify it's the last block
		assert content_blocks[-1].get('cache_control') is not None  # type: ignore[attr-defined]
		assert content_blocks[0].get('cache_control') is None  # type: ignore[attr-defined]
		assert content_blocks[1].get('cache_control') is None