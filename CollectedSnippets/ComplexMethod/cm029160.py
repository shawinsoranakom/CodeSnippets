def test_cache_assistant_with_content_and_tools(self):
		"""Test AssistantMessage with both content and tool calls - only last tool gets cache."""
		tool_call = ToolCall(id='test_id', function=Function(name='test_function', arguments='{"arg": "value"}'))

		assistant_msg = AssistantMessage(
			content=[
				ContentPartTextParam(text='Text part 1', type='text'),
				ContentPartTextParam(text='Text part 2', type='text'),
			],
			tool_calls=[tool_call],
			cache=True,
		)
		serialized = AnthropicMessageSerializer.serialize(assistant_msg)
		assert isinstance(serialized['content'], list)
		content_blocks = serialized['content']

		# Should have 2 text blocks + 1 tool_use block = 3 blocks total
		assert len(content_blocks) == 3

		# Only the last block (tool_use) should have cache_control
		# Note: content_blocks are dicts at runtime despite type annotations
		cache_count = sum(1 for block in content_blocks if block.get('cache_control') is not None)  # type: ignore[attr-defined]
		assert cache_count == 1, f'Expected 1 cache_control block, got {cache_count}'
		assert content_blocks[-1].get('cache_control') is not None  # type: ignore[attr-defined]  # Last tool_use block
		assert content_blocks[0].get('cache_control') is None  # type: ignore[attr-defined]  # First text block
		assert content_blocks[1].get('cache_control') is None