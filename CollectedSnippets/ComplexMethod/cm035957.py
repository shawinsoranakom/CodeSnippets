def test_featurizer_embed_batch(samples, batch_size, featurizer, mock_llm_config):
    """Test the embed_batch method to ensure it correctly handles all issues in the batch."""
    embeddings = featurizer.embed_batch(
        [f'Issue {i}' for i in range(batch_size)],
        llm_config=mock_llm_config,
        samples=samples,
    )

    # Make sure that we get an embedding for each issue.
    assert len(embeddings) == batch_size

    # Since the embeddings are computed from a mocked completionc all, they should
    # all be the same. We can check that they're well-formatted by applying the same
    # checks as in `test_featurizer_embed`.
    for embedding in embeddings:
        assert all(sample == embedding.samples[0] for sample in embedding.samples)
        assert embedding.samples[0]['feature1'] is True
        assert embedding.samples[0]['feature2'] is False
        assert embedding.samples[0]['feature3'] is True

        assert len(embedding.samples) == samples
        assert embedding.prompt_tokens == 10 * samples
        assert embedding.completion_tokens == 5 * samples
        assert embedding.response_latency >= 0.0