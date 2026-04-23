def test_cache_only_last_tool_call(self):
		"""Test that only the LAST tool_use block gets cache_control."""
		tool_calls = [
			ToolCall(id='id1', function=Function(name='func1', arguments='{"arg": "1"}')),
			ToolCall(id='id2', function=Function(name='func2', arguments='{"arg": "2"}')),
			ToolCall(id='id3', function=Function(name='func3', arguments='{"arg": "3"}')),
		]

		assistant_msg = AssistantMessage(content=None, tool_calls=tool_calls, cache=True)
		serialized = AnthropicMessageSerializer.serialize(assistant_msg)
		assert isinstance(serialized['content'], list)
		content_blocks = serialized['content']

		# Count tool_use blocks with cache_control
		# Note: content_blocks are dicts at runtime despite type annotations
		cache_count = sum(1 for block in content_blocks if block.get('cache_control') is not None)  # type: ignore[attr-defined]
		assert cache_count == 1, f'Expected 1 cache_control block, got {cache_count}'

		# Verify it's the last tool_use block
		assert content_blocks[-1].get('cache_control') is not None  # type: ignore[attr-defined]
		assert content_blocks[0].get('cache_control') is None  # type: ignore[attr-defined]
		assert content_blocks[1].get('cache_control') is None