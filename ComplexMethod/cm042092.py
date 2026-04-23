async def test_memory_llm(llm):
    memory = BrainMemory()
    for i in range(500):
        memory.add_talk(Message(content="Lily is a girl.\n"))

    res = await memory.is_related("apple", "moon", llm)
    assert not res

    res = await memory.rewrite(sentence="apple Lily eating", context="", llm=llm)
    assert "Lily" in res

    res = await memory.summarize(llm=llm)
    assert res

    res = await memory.get_title(llm=llm)
    assert res
    assert "Lily" in res
    assert memory.history or memory.historical_summary