def test_featurizer_embed_batch_thread_safety(featurizer, mock_llm_config, monkeypatch):
    """Test embed_batch maintains correct ordering and handles concurrent execution safely."""
    import time
    from unittest.mock import MagicMock

    # Create unique responses for each issue to verify ordering
    def create_mock_response(issue_index):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [MagicMock()]
        # Each issue gets a unique feature pattern based on its index
        mock_response.choices[0].message.tool_calls[0].function.arguments = (
            f'{{"feature1": {str(issue_index % 2 == 0).lower()}, '
            f'"feature2": {str(issue_index % 3 == 0).lower()}, '
            f'"feature3": {str(issue_index % 5 == 0).lower()}}}'
        )
        mock_response.usage.prompt_tokens = 10 + issue_index
        mock_response.usage.completion_tokens = 5 + issue_index
        return mock_response

    # Track call order and add delays to simulate varying processing times
    call_count = 0
    call_order = []

    def mock_completion(*args, **kwargs):
        nonlocal call_count
        # Extract issue index from the message content
        messages = kwargs.get('messages', args[0] if args else [])
        message_content = messages[1]['content']
        issue_index = int(message_content.split('Issue ')[-1])
        call_order.append(issue_index)

        # Add varying delays to simulate real-world conditions
        # Later issues process faster to test race conditions
        delay = 0.01 * (20 - issue_index)
        time.sleep(delay)

        call_count += 1
        return create_mock_response(issue_index)

    def mock_llm_class(*args, **kwargs):
        mock_llm_instance = MagicMock()
        mock_llm_instance.completion = mock_completion
        return mock_llm_instance

    monkeypatch.setattr(
        'integrations.solvability.models.featurizer.LLM', mock_llm_class
    )

    # Test with a large enough batch to stress concurrency
    batch_size = 20
    issues = [f'Issue {i}' for i in range(batch_size)]

    embeddings = featurizer.embed_batch(issues, llm_config=mock_llm_config, samples=1)

    # Verify we got all embeddings
    assert len(embeddings) == batch_size

    # Verify each embedding corresponds to its correct issue index
    for i, embedding in enumerate(embeddings):
        assert len(embedding.samples) == 1
        sample = embedding.samples[0]

        # Check the unique pattern matches the issue index
        assert sample['feature1'] == (i % 2 == 0)
        assert sample['feature2'] == (i % 3 == 0)
        assert sample['feature3'] == (i % 5 == 0)

        # Check token counts match
        assert embedding.prompt_tokens == 10 + i
        assert embedding.completion_tokens == 5 + i

    # Verify all issues were processed
    assert call_count == batch_size
    assert len(set(call_order)) == batch_size