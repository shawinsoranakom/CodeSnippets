def test_max_depth() -> None:
    d = {}
    d["foo"] = {"fob": {"a": [1, 2, 3], "b": {"z": "x", "y": ["a", "b", "c"]}}}

    assert pretty_repr(d, max_depth=0) == "{...}"
    assert pretty_repr(d, max_depth=1) == "{'foo': {...}}"
    assert pretty_repr(d, max_depth=2) == "{'foo': {'fob': {...}}}"
    assert pretty_repr(d, max_depth=3) == "{'foo': {'fob': {'a': [...], 'b': {...}}}}"
    assert (
        pretty_repr(d, max_width=100, max_depth=4)
        == "{'foo': {'fob': {'a': [1, 2, 3], 'b': {'z': 'x', 'y': [...]}}}}"
    )
    assert (
        pretty_repr(d, max_width=100, max_depth=5)
        == "{'foo': {'fob': {'a': [1, 2, 3], 'b': {'z': 'x', 'y': ['a', 'b', 'c']}}}}"
    )
    assert (
        pretty_repr(d, max_width=100, max_depth=None)
        == "{'foo': {'fob': {'a': [1, 2, 3], 'b': {'z': 'x', 'y': ['a', 'b', 'c']}}}}"
    )