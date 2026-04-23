def test_event_json_fragment() -> None:
    """Test event JSON fragments."""
    now = dt_util.utcnow()
    data = {"some": "attr"}
    context = ha.Context()
    event1, event2 = (
        ha.Event(
            "some_type", data, time_fired_timestamp=now.timestamp(), context=context
        )
        for _ in range(2)
    )

    # We are testing that the JSON fragments are the same when as_dict is called
    # after json_fragment or before.
    json_fragment_1 = event1.json_fragment
    as_dict_1 = event1.as_dict()
    as_dict_2 = event2.as_dict()
    json_fragment_2 = event2.json_fragment

    assert json_dumps(json_fragment_1) == json_dumps(json_fragment_2)
    # We also test that the as_dict is the same
    assert as_dict_1 == as_dict_2

    # Finally we verify that the as_dict is a ReadOnlyDict
    # as is the data and context inside regardless of
    # if the json fragment was called first or not
    assert isinstance(as_dict_1, ReadOnlyDict)
    assert isinstance(as_dict_1["data"], ReadOnlyDict)
    assert isinstance(as_dict_1["context"], ReadOnlyDict)

    assert isinstance(as_dict_2, ReadOnlyDict)
    assert isinstance(as_dict_2["data"], ReadOnlyDict)
    assert isinstance(as_dict_2["context"], ReadOnlyDict)