def test_featurizer_embed(samples, featurizer, mock_llm_config):
    """Test the embed method to ensure it generates the right number of samples and computes the metadata correctly."""
    embedding = featurizer.embed(
        'Test issue', llm_config=mock_llm_config, samples=samples
    )

    # We should get the right number of samples.
    assert len(embedding.samples) == samples

    # Because of the mocks, all the samples should be the same (and be correct).
    assert all(sample == embedding.samples[0] for sample in embedding.samples)
    assert embedding.samples[0]['feature1'] is True
    assert embedding.samples[0]['feature2'] is False
    assert embedding.samples[0]['feature3'] is True

    # And all the metadata should be correct (we know the token counts because
    # they're mocked, so just count once per sample).
    assert embedding.prompt_tokens == 10 * samples
    assert embedding.completion_tokens == 5 * samples

    # These timings are real, so best we can do is check that they're positive.
    assert embedding.response_latency > 0.0