def test_immutable_dict():
    d1 = ImmutableDict({"a": ["b"], "c": 1})

    assert dict(d1) == {"a": ["b"], "c": 1}
    assert set(d1) == {"a", "c"}
    assert d1["a"] == ["b"]
    assert d1["c"] == 1
    assert len(d1) == 2

    assert "a" in d1
    assert "z" not in d1

    with pytest.raises(Exception) as exc:
        d1["foo"] = "bar"
    exc.match("does not support item assignment")