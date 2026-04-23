def test_find_unserializable_data() -> None:
    """Find unserializeable data."""
    assert find_paths_unserializable_data(1) == {}
    assert find_paths_unserializable_data([1, 2]) == {}
    assert find_paths_unserializable_data({"something": "yo"}) == {}

    assert find_paths_unserializable_data({"something": set()}) == {
        "$.something": set()
    }
    assert find_paths_unserializable_data({"something": [1, set()]}) == {
        "$.something[1]": set()
    }
    assert find_paths_unserializable_data([1, {"bla": set(), "blub": set()}]) == {
        "$[1].bla": set(),
        "$[1].blub": set(),
    }
    assert find_paths_unserializable_data({("A",): 1}) == {"$<key: ('A',)>": ("A",)}
    assert math.isnan(
        find_paths_unserializable_data(
            math.nan, dump=partial(json.dumps, allow_nan=False)
        )["$"]
    )

    # Test custom encoder + State support.

    class MockJSONEncoder(json.JSONEncoder):
        """Mock JSON encoder."""

        def default(self, o):
            """Mock JSON encode method."""
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            return super().default(o)

    bad_data = object()

    assert find_paths_unserializable_data(
        [State("mock_domain.mock_entity", "on", {"bad": bad_data})],
        dump=partial(json.dumps, cls=MockJSONEncoder),
    ) == {"$[0](State: mock_domain.mock_entity).attributes.bad": bad_data}

    assert find_paths_unserializable_data(
        [Event("bad_event", {"bad_attribute": bad_data})],
        dump=partial(json.dumps, cls=MockJSONEncoder),
    ) == {"$[0](Event: bad_event).data.bad_attribute": bad_data}

    class BadData:
        def __init__(self) -> None:
            self.bla = bad_data

        def as_dict(self) -> dict[str, Any]:
            return {"bla": self.bla}

    assert find_paths_unserializable_data(
        BadData(),
        dump=partial(json.dumps, cls=MockJSONEncoder),
    ) == {"$(BadData).bla": bad_data}