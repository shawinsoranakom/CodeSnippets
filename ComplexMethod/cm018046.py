def test_state_json_fragment() -> None:
    """Test state JSON fragments."""
    last_time = datetime(1984, 12, 8, 12, 0, 0)
    state1, state2 = (
        ha.State(
            "happy.happy",
            "on",
            {"pig": "dog"},
            context=ha.Context(id="01H0D6K3RFJAYAV2093ZW30PCW"),
            last_changed=last_time,
            last_reported=last_time,
            last_updated=last_time,
        )
        for _ in range(2)
    )

    # We are testing that the JSON fragments are the same when as_dict is called
    # after json_fragment or before.
    json_fragment_1 = state1.json_fragment
    as_dict_1 = state1.as_dict()
    as_dict_2 = state2.as_dict()
    json_fragment_2 = state2.json_fragment

    assert json_dumps(json_fragment_1) == json_dumps(json_fragment_2)
    # We also test that the as_dict is the same
    assert as_dict_1 == as_dict_2

    # Finally we verify that the as_dict is a ReadOnlyDict
    # as is the attributes and context inside regardless of
    # if the json fragment was called first or not
    assert isinstance(as_dict_1, ReadOnlyDict)
    assert isinstance(as_dict_1["attributes"], ReadOnlyDict)
    assert isinstance(as_dict_1["context"], ReadOnlyDict)

    assert isinstance(as_dict_2, ReadOnlyDict)
    assert isinstance(as_dict_2["attributes"], ReadOnlyDict)
    assert isinstance(as_dict_2["context"], ReadOnlyDict)