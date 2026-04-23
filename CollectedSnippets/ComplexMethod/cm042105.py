async def test_amoderation(content):
    # Prerequisites
    assert config.get_openai_llm()

    moderation = Moderation(LLM())
    results = await moderation.amoderation(content=content)
    assert isinstance(results, list)
    assert len(results) == len(content)

    results = await moderation.amoderation_with_categories(content=content)
    assert isinstance(results, list)
    assert results
    for m in results:
        assert "flagged" in m
        assert "true_categories" in m