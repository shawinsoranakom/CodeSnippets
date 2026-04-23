def test_disambiguate_tools_with_boolean_and_numeric_defaults():
    """Boolean and numeric default values should serialize correctly in description."""
    tools: list[dict] = [
        {
            "function": {
                "name": "processor",
                "description": "Proc",
                "_hardcoded_defaults": {
                    "enabled": True,
                    "count": 42,
                    "ratio": 3.14,
                },
            }
        },
        {
            "function": {
                "name": "processor",
                "description": "Proc",
                "_hardcoded_defaults": {"enabled": False, "count": 0},
            }
        },
    ]
    _disambiguate_tool_names(tools)

    names = [t["function"]["name"] for t in tools]
    assert len(set(names)) == 2

    tool_1 = next(t for t in tools if t["function"]["name"] == "processor_1")
    desc = tool_1["function"]["description"]
    assert "enabled=true" in desc
    assert "count=42" in desc
    assert "ratio=3.14" in desc