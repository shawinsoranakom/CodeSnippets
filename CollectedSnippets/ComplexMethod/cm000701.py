def test_disambiguate_skips_non_string_tool_names():
    """Tools whose 'name' is not a string (None, int, list) must not crash."""
    tools: list = [
        {"function": {"name": "good_tool", "description": "A tool"}},
        {"function": {"name": "good_tool", "description": "Another tool"}},
        # name is None
        {"function": {"name": None, "description": "null name"}},
        # name is an integer
        {"function": {"name": 123, "description": "int name"}},
        # name is a list
        {"function": {"name": ["a", "b"], "description": "list name"}},
    ]
    # Should not raise
    _disambiguate_tool_names(tools)

    # The two good tools should be disambiguated
    names = [
        t["function"]["name"]
        for t in tools
        if isinstance(t, dict)
        and isinstance(t.get("function"), dict)
        and isinstance(t["function"].get("name"), str)
    ]
    assert "good_tool_1" in names
    assert "good_tool_2" in names
    # Non-string names should be left untouched (skipped, not mutated)
    assert tools[2]["function"]["name"] is None
    assert tools[3]["function"]["name"] == 123
    assert tools[4]["function"]["name"] == ["a", "b"]