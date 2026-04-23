def test_profile() -> None:
    model = ChatOpenAI(model="gpt-4")
    assert model.profile
    assert not model.profile["structured_output"]

    model = ChatOpenAI(model="gpt-5")
    assert model.profile
    assert model.profile["structured_output"]
    assert model.profile["tool_calling"]

    # Test overwriting a field
    model.profile["tool_calling"] = False
    assert not model.profile["tool_calling"]

    # Test we didn't mutate
    model = ChatOpenAI(model="gpt-5")
    assert model.profile
    assert model.profile["tool_calling"]

    # Test passing in profile
    model = ChatOpenAI(model="gpt-5", profile={"tool_calling": False})
    assert model.profile == {"tool_calling": False}

    # Test overrides for gpt-5 input tokens
    model = ChatOpenAI(model="gpt-5")
    assert model.profile["max_input_tokens"] == 272_000