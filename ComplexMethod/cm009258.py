def test_profile() -> None:
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    assert model.profile
    assert not model.profile["structured_output"]

    model = ChatAnthropic(model="claude-sonnet-4-5")
    assert model.profile
    assert model.profile["structured_output"]
    assert model.profile["tool_calling"]

    # Test overwriting a field
    model.profile["tool_calling"] = False
    assert not model.profile["tool_calling"]

    # Test we didn't mutate
    model = ChatAnthropic(model="claude-sonnet-4-5")
    assert model.profile
    assert model.profile["tool_calling"]

    # Test passing in profile
    model = ChatAnthropic(model="claude-sonnet-4-5", profile={"tool_calling": False})
    assert model.profile == {"tool_calling": False}