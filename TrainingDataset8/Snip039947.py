def test_map_set_del_3837_regression():
    """A regression test for `test_map_set_del` that involves too much setup
    to conveniently use the hypothesis `example` decorator."""

    meta1 = stst.mock_metadata(
        "$$GENERATED_WIDGET_KEY-e3e70682-c209-4cac-629f-6fbed82c07cd-None", 0
    )
    meta2 = stst.mock_metadata(
        "$$GENERATED_WIDGET_KEY-f728b4fa-4248-5e3a-0a5d-2f346baa9455-0", 0
    )
    m = SessionState()
    m["0"] = 0
    m.register_widget(metadata=meta1, user_key=None)
    m._compact_state()

    m.register_widget(metadata=meta2, user_key="0")
    key = "0"
    value1 = 0

    m[key] = value1
    l1 = len(m)
    del m[key]
    assert key not in m
    assert len(m) == l1 - 1