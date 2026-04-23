def test_get_kwargs():
    kwargs = get_kwargs(DummyConfig)
    print(kwargs)

    # bools should not have their type set
    assert kwargs["regular_bool"].get("type") is None
    assert kwargs["optional_bool"].get("type") is None
    # optional literals should have None as a choice
    assert kwargs["optional_literal"]["choices"] == ["x", "y", "None"]
    # tuples should have the correct nargs
    assert kwargs["tuple_n"]["nargs"] == "+"
    assert kwargs["tuple_2"]["nargs"] == 2
    # lists should work
    assert kwargs["list_n"]["type"] is int
    assert kwargs["list_n"]["nargs"] == "+"
    # lists with literals should have the correct choices
    assert kwargs["list_literal"]["type"] is int
    assert kwargs["list_literal"]["nargs"] == "+"
    assert kwargs["list_literal"]["choices"] == [1, 2]
    # lists with unions should become str type.
    # If not, we cannot know which type to use for parsing
    assert kwargs["list_union"]["type"] is str
    # sets should work like lists
    assert kwargs["set_n"]["type"] is int
    assert kwargs["set_n"]["nargs"] == "+"
    # literals of literals should have merged choices
    assert kwargs["literal_literal"]["choices"] == [1, 2]
    # dict should have json tip in help
    json_tip = "Should either be a valid JSON string or JSON keys"
    assert json_tip in kwargs["json_tip"]["help"]
    # nested config should construct the nested config
    assert kwargs["nested_config"]["type"]('{"field": 2}') == NestedConfig(2)