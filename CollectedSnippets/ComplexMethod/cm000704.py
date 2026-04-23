def test_disambiguate_multiple_distinct_duplicate_groups():
    """Two groups of duplicates (group_a x2 and group_b x2) should each get suffixed."""
    tools: list[dict] = [
        {"function": {"name": "group_a", "description": "A1"}},
        {"function": {"name": "group_a", "description": "A2"}},
        {"function": {"name": "group_b", "description": "B1"}},
        {"function": {"name": "group_b", "description": "B2"}},
        {"function": {"name": "unique_c", "description": "C1"}},
    ]
    _disambiguate_tool_names(tools)

    names = [t["function"]["name"] for t in tools]
    assert len(set(names)) == 5, f"Tool names are not unique: {names}"
    assert "group_a_1" in names
    assert "group_a_2" in names
    assert "group_b_1" in names
    assert "group_b_2" in names
    # unique tool is untouched
    assert "unique_c" in names