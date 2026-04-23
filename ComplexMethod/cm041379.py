def test_hashable_dict():
    d1 = HashableJsonDict({"a": ["b"], "c": 1})
    d2 = HashableJsonDict({"a": "b"})
    d3 = HashableJsonDict({"c": 1, "a": ["b"]})
    d4 = HashableJsonDict({})

    assert len({d1, d2, d3}) == 2
    assert {d1, d2, d3} == {d1, d2} == {d2, d3}
    assert {d1, d3} == {d3, d1}
    assert {d1, d1} == {d3, d3}
    assert {d1, d2, d3} != {d1}
    assert {d1, d2, d3} != {d2}
    assert {d1, d2, d3} != {d1, d3}
    assert {d4, d4} == {d4}

    with pytest.raises(Exception) as exc:
        d1["foo"] = "bar"
    exc.match("does not support item assignment")