async def test_memory():
    memory = BrainMemory()
    memory.add_talk(Message(content="talk"))
    assert memory.history[0].role == "user"
    memory.add_answer(Message(content="answer"))
    assert memory.history[1].role == "assistant"
    redis_key = BrainMemory.to_redis_key("none", "user_id", "chat_id")
    await memory.dumps(redis_key=redis_key)
    assert memory.exists("talk")
    assert 1 == memory.to_int("1", 0)
    memory.last_talk = "AAA"
    assert memory.pop_last_talk() == "AAA"
    assert memory.last_talk is None
    assert memory.is_history_available
    assert memory.history_text

    memory = await BrainMemory.loads(redis_key=redis_key)
    assert memory